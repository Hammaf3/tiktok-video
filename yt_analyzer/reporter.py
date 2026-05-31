"""
Markdown report generator
"""
from datetime import datetime
from typing import List, Dict
from pathlib import Path


def format_number(num: int) -> str:
    """Format large numbers with K/M suffix"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def format_duration(seconds: int) -> str:
    """Format duration as MM:SS or HH:MM:SS"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def extract_keywords_from_videos(videos: List[Dict], top_n: int = 10) -> List[str]:
    """Extract most common keywords from video titles"""
    from collections import Counter
    import re

    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'this', 'that', 'how', 'what', 'why', 'when', 'where', 'who'
    }

    words = []
    for video in videos:
        title = video['title'].lower()
        # Remove special characters
        title = re.sub(r'[^\w\s]', ' ', title)
        # Split and filter
        words.extend([w for w in title.split() if w not in stopwords and len(w) > 3])

    # Count frequency
    word_counts = Counter(words)
    return [word for word, count in word_counts.most_common(top_n)]


def calculate_insights(videos: List[Dict]) -> Dict:
    """Calculate insights from video data"""
    if not videos:
        return {}

    # Best performing duration
    duration_buckets = {
        '0-30s': [],
        '30-60s': [],
        '60-180s': [],
        '180-600s': [],
        '600+s': []
    }

    for video in videos:
        duration = video['duration_seconds']
        score = video['viral_score']

        if duration <= 30:
            duration_buckets['0-30s'].append(score)
        elif duration <= 60:
            duration_buckets['30-60s'].append(score)
        elif duration <= 180:
            duration_buckets['60-180s'].append(score)
        elif duration <= 600:
            duration_buckets['180-600s'].append(score)
        else:
            duration_buckets['600+s'].append(score)

    # Find best duration range
    best_duration = max(
        duration_buckets.items(),
        key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0
    )[0]

    # Average engagement rate
    avg_engagement = sum(v['engagement_rate'] for v in videos) / len(videos)

    # Peak upload days
    from collections import Counter
    upload_days = [v['published_at'].strftime('%A') for v in videos]
    day_counts = Counter(upload_days)
    peak_days = [day for day, count in day_counts.most_common(2)]

    # Top keywords
    top_keywords = extract_keywords_from_videos(videos, top_n=5)

    return {
        'best_duration': best_duration,
        'avg_engagement': avg_engagement,
        'peak_days': peak_days,
        'top_keywords': top_keywords
    }


def generate_markdown_report(
    videos: List[Dict],
    query: str,
    mode: str,
    output_path: str
) -> str:
    """
    Generate markdown report

    Args:
        videos: List of scored videos
        query: Search query or channel name
        mode: Analysis mode (channel/search)
        output_path: Path to save report

    Returns:
        Path to generated report
    """
    if not videos:
        raise Exception("No videos to report")

    # Calculate insights
    insights = calculate_insights(videos)

    # Generate report content
    lines = []

    # Header
    lines.append("# 📊 YouTube Analysis Report\n")
    lines.append(f"**Query:** {query}  ")
    lines.append(f"**Mode:** {mode.capitalize()}  ")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} PKT  ")
    lines.append(f"**Total Videos Analyzed:** {len(videos)}  ")

    if insights.get('top_keywords'):
        lines.append(f"**Top Keywords:** {', '.join(insights['top_keywords'])}\n")

    lines.append("\n---\n")

    # Top videos table
    lines.append(f"## 🏆 Top {len(videos)} Videos by Viral Score\n")

    lines.append("| Rank | Title | Channel | Views | Likes | Comments | Duration | Days Old | Viral Score | Category |")
    lines.append("|------|-------|---------|-------|-------|----------|----------|----------|-------------|----------|")

    for i, video in enumerate(videos, 1):
        title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
        title_link = f"[{title}]({video['url']})"
        channel = video['channel_title'][:20]

        lines.append(
            f"| #{i} | {title_link} | {channel} | "
            f"{format_number(video['view_count'])} | "
            f"{format_number(video['like_count'])} | "
            f"{format_number(video['comment_count'])} | "
            f"{format_duration(video['duration_seconds'])} | "
            f"{int(video['days_old'])} | "
            f"{video['viral_score']:.1f} | "
            f"{video['category']} |"
        )

    lines.append("\n---\n")

    # Insights section
    lines.append("## 📈 Insights\n")

    if insights:
        lines.append(f"- **Best performing duration:** {insights.get('best_duration', 'N/A')}")
        lines.append(f"- **Peak upload days:** {', '.join(insights.get('peak_days', ['N/A']))}")
        lines.append(f"- **Avg engagement rate:** {insights.get('avg_engagement', 0):.2f}%")

        if insights.get('top_keywords'):
            lines.append(f"- **Top keywords:** {', '.join(insights['top_keywords'])}")

    lines.append("\n---\n")

    # Recommended video section
    if videos:
        top_video = videos[0]
        lines.append("## 🎯 Recommended Video to Convert\n")
        lines.append(f"**Title:** {top_video['title']}  ")
        lines.append(f"**URL:** {top_video['url']}  ")
        lines.append(f"**Channel:** {top_video['channel_title']}  ")
        lines.append(f"**Why:** Highest viral score ({top_video['viral_score']:.1f}), "
                    f"{format_number(top_video['view_count'])} views in "
                    f"{int(top_video['days_old'])} days, "
                    f"{format_duration(top_video['duration_seconds'])} duration — "
                    f"perfect for TikTok\n")

        lines.append("\n*Run with `--auto-upload-top` to automatically convert and upload this video to TikTok*\n")

    # Write to file
    report_content = '\n'.join(lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return output_path


def print_summary(videos: List[Dict], limit: int = 10):
    """Print summary to console"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not videos:
        console.print("[yellow]No videos found[/yellow]")
        return

    # Create table
    table = Table(title=f"Top {min(limit, len(videos))} Videos", show_lines=True)

    table.add_column("Rank", style="cyan", width=5)
    table.add_column("Title", style="white", width=40)
    table.add_column("Views", style="green", justify="right")
    table.add_column("Score", style="yellow", justify="right")
    table.add_column("Category", style="magenta")

    for i, video in enumerate(videos[:limit], 1):
        title = video['title'][:37] + "..." if len(video['title']) > 40 else video['title']

        table.add_row(
            f"#{i}",
            title,
            format_number(video['view_count']),
            f"{video['viral_score']:.1f}",
            video['category']
        )

    console.print(table)
