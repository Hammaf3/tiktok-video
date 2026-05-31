"""
Main CLI entry point for yt2tik
"""
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from .config import DEFAULT_DURATION, TIKTOK_MAX_DURATION
from .logger import setup_logger
from .downloader import download_youtube_video
from .converter import convert_to_tiktok_format
from .caption_gen import generate_caption, validate_caption
from .uploader import upload_to_tiktok

console = Console()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Convert YouTube videos to TikTok format and auto-upload',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with auto-upload
  python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" --auto-upload

  # Specify start time and duration
  python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" --start 00:01:20 --duration 45

  # Custom caption and hashtags
  python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" \\
    --caption "🔥 Must watch!" --hashtags "#fyp #viral #trending" --auto-upload

  # Dry run (no upload)
  python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" --dry-run

  # Auto-detect best segment
  python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" --auto-detect --auto-upload
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='YouTube video URL'
    )

    parser.add_argument(
        '--start',
        help='Start timestamp (HH:MM:SS or MM:SS or SS)'
    )

    parser.add_argument(
        '--duration',
        type=int,
        default=DEFAULT_DURATION,
        help=f'Clip duration in seconds (default: {DEFAULT_DURATION}, max: {TIKTOK_MAX_DURATION})'
    )

    parser.add_argument(
        '--caption',
        help='Custom caption text'
    )

    parser.add_argument(
        '--hashtags',
        help='Custom hashtags (space or comma separated)'
    )

    parser.add_argument(
        '--watermark',
        help='Watermark text to add at bottom of video'
    )

    parser.add_argument(
        '--privacy',
        choices=['public', 'friends', 'private'],
        default='public',
        help='Privacy setting for TikTok upload (default: public)'
    )

    parser.add_argument(
        '--auto-upload',
        action='store_true',
        help='Automatically upload to TikTok after conversion'
    )

    parser.add_argument(
        '--auto-detect',
        action='store_true',
        help='Auto-detect best segment if --start not provided'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process video but skip TikTok upload (for testing)'
    )

    parser.add_argument(
        '--output',
        help='Output filename (default: auto-generated)'
    )

    return parser.parse_args()


def main():
    """Main execution flow"""
    args = parse_args()

    # Setup logger
    logger = setup_logger()

    # Print header
    console.print(Panel.fit(
        "[bold cyan]yt2tik[/bold cyan] - YouTube to TikTok Converter",
        border_style="cyan"
    ))

    try:
        # Validate duration
        if args.duration > TIKTOK_MAX_DURATION:
            console.print(f"[yellow]⚠️  Duration capped at {TIKTOK_MAX_DURATION}s (TikTok limit)[/yellow]")
            args.duration = TIKTOK_MAX_DURATION

        # Step 1: Download YouTube video
        console.print("\n[bold]Step 1/4:[/bold] Downloading YouTube video...")
        video_data = download_youtube_video(args.url)

        # Step 2: Convert to TikTok format
        console.print("\n[bold]Step 2/4:[/bold] Converting to TikTok format...")

        output_filename = args.output or f"tiktok_{Path(video_data['video_path']).stem}.mp4"

        converted_path = convert_to_tiktok_format(
            input_path=video_data['video_path'],
            output_filename=output_filename,
            start_time=args.start,
            duration=args.duration,
            watermark=args.watermark,
            auto_detect=args.auto_detect and not args.start
        )

        # Step 3: Generate caption
        console.print("\n[bold]Step 3/4:[/bold] Generating caption...")

        caption = generate_caption(
            title=video_data['title'],
            description=video_data['description'],
            custom_caption=args.caption,
            custom_hashtags=args.hashtags
        )

        if not validate_caption(caption):
            raise Exception("Generated caption is invalid")

        # Step 4: Upload to TikTok
        if args.auto_upload and not args.dry_run:
            console.print("\n[bold]Step 4/4:[/bold] Uploading to TikTok...")

            video_url = upload_to_tiktok(
                video_path=converted_path,
                caption=caption,
                privacy=args.privacy
            )

            # Success summary
            console.print("\n" + "="*60)
            console.print("[bold green]✅ Upload Complete![/bold green]\n")

            # Create summary table
            table = Table(show_header=False, box=None)
            table.add_column("Label", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("📹 TikTok URL:", video_url)
            table.add_row("📊 Video Duration:", f"{args.duration}s")

            file_size = Path(converted_path).stat().st_size / (1024 * 1024)
            table.add_row("💾 File Size:", f"{file_size:.1f}MB")
            table.add_row("📝 Caption Length:", f"{len(caption)} chars")
            table.add_row("🔒 Privacy:", args.privacy.capitalize())

            console.print(table)
            console.print("="*60)

        elif args.dry_run:
            console.print("\n[bold yellow]🏁 Dry Run Complete (Upload Skipped)[/bold yellow]\n")

            table = Table(show_header=False, box=None)
            table.add_column("Label", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("📁 Output File:", converted_path)
            table.add_row("📊 Video Duration:", f"{args.duration}s")

            file_size = Path(converted_path).stat().st_size / (1024 * 1024)
            table.add_row("💾 File Size:", f"{file_size:.1f}MB")
            table.add_row("📝 Caption:", caption[:100] + "..." if len(caption) > 100 else caption)

            console.print(table)
            console.print("\n[dim]Run without --dry-run and with --auto-upload to upload to TikTok[/dim]")

        else:
            console.print("\n[bold green]✅ Conversion Complete![/bold green]\n")

            table = Table(show_header=False, box=None)
            table.add_column("Label", style="cyan")
            table.add_column("Value", style="white")

            table.add_row("📁 Output File:", converted_path)
            table.add_row("📊 Video Duration:", f"{args.duration}s")

            file_size = Path(converted_path).stat().st_size / (1024 * 1024)
            table.add_row("💾 File Size:", f"{file_size:.1f}MB")
            table.add_row("📝 Caption:", caption[:100] + "..." if len(caption) > 100 else caption)

            console.print(table)
            console.print("\n[dim]Add --auto-upload flag to upload to TikTok[/dim]")

        return 0

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        return 130

    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}")
        logger.exception("Fatal error")
        return 1


if __name__ == '__main__':
    sys.exit(main())
