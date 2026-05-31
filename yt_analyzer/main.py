"""
Main CLI entry point for yt_analyzer
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from .config import DEFAULT_LIMIT, DEFAULT_SORT, REPORTS_DIR
from .fetcher import YouTubeFetcher
from .scorer import score_videos, sort_videos
from .reporter import generate_markdown_report, print_summary
from .niche_presets import get_niche_keywords, get_available_niches, is_valid_niche
from .uploader_bridge import upload_video_to_tiktok

console = Console()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Analyze YouTube channels and niches to find viral content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a channel
  python -m yt_analyzer.main --mode channel --channel "@MrBeast" --limit 30

  # Search by keyword
  python -m yt_analyzer.main --mode search --query "satisfying videos 2024" --limit 25

  # Use niche preset
  python -m yt_analyzer.main --mode search --niche cooking --limit 30

  # Auto-upload top video
  python -m yt_analyzer.main --mode search --query "viral moments" --auto-upload-top

  # Filter by duration and views
  python -m yt_analyzer.main --mode search --query "tech tutorials" \\
    --filter-duration 60-600 --filter-views 10000
        """
    )

    parser.add_argument(
        '--mode',
        required=True,
        choices=['channel', 'search'],
        help='Analysis mode: channel or search'
    )

    parser.add_argument(
        '--channel',
        help='Channel handle (e.g., @MrBeast) - required for channel mode'
    )

    parser.add_argument(
        '--query',
        help='Search query/keyword - required for search mode'
    )

    parser.add_argument(
        '--niche',
        choices=get_available_niches(),
        help='Niche preset (overrides --query)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=DEFAULT_LIMIT,
        help=f'Number of videos to analyze (default: {DEFAULT_LIMIT})'
    )

    parser.add_argument(
        '--sort',
        choices=['viral-score', 'engagement', 'views', 'velocity'],
        default=DEFAULT_SORT,
        help=f'Sort by metric (default: {DEFAULT_SORT})'
    )

    parser.add_argument(
        '--filter-duration',
        help='Duration range in seconds (e.g., 60-600)'
    )

    parser.add_argument(
        '--filter-views',
        type=int,
        help='Minimum view count'
    )

    parser.add_argument(
        '--filter-date',
        help='Date range (YYYY-MM-DD:YYYY-MM-DD)'
    )

    parser.add_argument(
        '--output',
        default='report.md',
        help='Output markdown file (default: report.md)'
    )

    parser.add_argument(
        '--auto-upload-top',
        action='store_true',
        help='Automatically upload #1 video to TikTok'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Skip upload (testing)'
    )

    return parser.parse_args()


def parse_duration_filter(duration_str: str) -> tuple:
    """Parse duration filter string (e.g., '60-600')"""
    try:
        parts = duration_str.split('-')
        if len(parts) != 2:
            raise ValueError()
        return int(parts[0]), int(parts[1])
    except:
        raise ValueError(f"Invalid duration format: {duration_str}. Use format: MIN-MAX (e.g., 60-600)")


def parse_date_filter(date_str: str) -> tuple:
    """Parse date filter string (e.g., '2024-01-01:2024-12-31')"""
    try:
        parts = date_str.split(':')
        if len(parts) != 2:
            raise ValueError()

        start_date = datetime.strptime(parts[0], '%Y-%m-%d')
        end_date = datetime.strptime(parts[1], '%Y-%m-%d')

        # Convert to ISO 8601 format for YouTube API
        return (
            start_date.strftime('%Y-%m-%dT00:00:00Z'),
            end_date.strftime('%Y-%m-%dT23:59:59Z')
        )
    except:
        raise ValueError(f"Invalid date format: {date_str}. Use format: YYYY-MM-DD:YYYY-MM-DD")


def filter_videos(videos: list, args) -> list:
    """Apply filters to video list"""
    filtered = videos

    # Duration filter
    if args.filter_duration:
        min_dur, max_dur = parse_duration_filter(args.filter_duration)
        filtered = [v for v in filtered if min_dur <= v['duration_seconds'] <= max_dur]
        console.print(f"[dim]Filtered by duration: {len(filtered)} videos remaining[/dim]")

    # Views filter
    if args.filter_views:
        filtered = [v for v in filtered if v['view_count'] >= args.filter_views]
        console.print(f"[dim]Filtered by views: {len(filtered)} videos remaining[/dim]")

    return filtered


def main():
    """Main execution flow"""
    args = parse_args()

    # Print header
    console.print(Panel.fit(
        "[bold cyan]yt_analyzer[/bold cyan] - YouTube Viral Content Analyzer",
        border_style="cyan"
    ))

    try:
        # Validate arguments
        if args.mode == 'channel' and not args.channel:
            raise Exception("--channel is required for channel mode")

        if args.mode == 'search' and not args.query and not args.niche:
            raise Exception("--query or --niche is required for search mode")

        # Initialize fetcher
        fetcher = YouTubeFetcher()

        # Determine query
        if args.niche:
            keywords = get_niche_keywords(args.niche)
            query = ' OR '.join(keywords)
            console.print(f"[cyan]Using niche preset:[/cyan] {args.niche}")
            console.print(f"[dim]Keywords: {', '.join(keywords)}[/dim]\n")
        else:
            query = args.query or args.channel

        # Parse date filter if provided
        published_after = None
        published_before = None
        if args.filter_date:
            published_after, published_before = parse_date_filter(args.filter_date)

        # Fetch videos
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            if args.mode == 'channel':
                task = progress.add_task(f"Resolving channel {args.channel}...", total=None)
                channel_id = fetcher.resolve_channel_id(args.channel)

                if not channel_id:
                    raise Exception(f"Channel not found: {args.channel}")

                progress.update(task, description=f"Fetching videos from {args.channel}...")
                video_ids = fetcher.get_channel_videos(channel_id, args.limit)

            else:  # search mode
                task = progress.add_task(f"Searching for: {query[:50]}...", total=None)
                video_ids = fetcher.search_videos(
                    query,
                    args.limit,
                    published_after,
                    published_before
                )

            if not video_ids:
                raise Exception("No videos found")

            progress.update(task, description=f"Fetching details for {len(video_ids)} videos...")
            videos = fetcher.get_video_details(video_ids)

        console.print(f"[green]✓[/green] Fetched {len(videos)} videos\n")

        # Apply filters
        if args.filter_duration or args.filter_views:
            videos = filter_videos(videos, args)

            if not videos:
                raise Exception("No videos remaining after filtering")

        # Score videos
        console.print("📊 Calculating viral scores...")
        scored_videos = score_videos(videos)

        # Sort videos
        sorted_videos = sort_videos(scored_videos, args.sort)

        # Print summary
        console.print()
        print_summary(sorted_videos, limit=10)

        # Generate report
        console.print(f"\n📝 Generating report...")

        output_path = REPORTS_DIR / args.output if not Path(args.output).is_absolute() else Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_path = generate_markdown_report(
            sorted_videos,
            query,
            args.mode,
            str(output_path)
        )

        console.print(f"[green]✓[/green] Report saved: {report_path}\n")

        # Auto-upload top video
        if args.auto_upload_top and sorted_videos:
            top_video = sorted_videos[0]

            console.print(f"[bold]🚀 Auto-uploading top video to TikTok...[/bold]")
            console.print(f"[dim]Title: {top_video['title'][:60]}...[/dim]\n")

            success = upload_video_to_tiktok(top_video, dry_run=args.dry_run)

            if success:
                console.print("[green]✓[/green] Upload complete!\n")
            else:
                console.print("[yellow]⚠[/yellow] Upload failed or was skipped\n")

        # Final summary
        console.print("="*60)
        console.print("[bold green]✅ Analysis Complete![/bold green]\n")
        console.print(f"📊 Videos Analyzed: {len(sorted_videos)}")
        console.print(f"📁 Report: {report_path}")

        if sorted_videos:
            top = sorted_videos[0]
            console.print(f"🏆 Top Video: {top['title'][:50]}...")
            console.print(f"   Score: {top['viral_score']:.1f} | Views: {top['view_count']:,}")

        console.print("="*60)

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        return 130

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
