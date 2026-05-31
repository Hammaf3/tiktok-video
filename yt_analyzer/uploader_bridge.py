"""
Bridge to yt2tik uploader
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict


def upload_video_to_tiktok(video: Dict, dry_run: bool = False) -> bool:
    """
    Upload video to TikTok using yt2tik

    Args:
        video: Video data dict with url, title, etc.
        dry_run: If True, skip actual upload

    Returns:
        True if successful
    """
    # Build command
    cmd = [
        sys.executable,
        '-m',
        'yt2tik.main',
        '--url', video['url'],
        '--auto-detect',
        '--duration', '45',  # Default to 45s for viral content
    ]

    if not dry_run:
        cmd.append('--auto-upload')
    else:
        cmd.append('--dry-run')

    # Add caption from title
    caption = f"🔥 {video['title'][:100]}"
    cmd.extend(['--caption', caption])

    try:
        # Run yt2tik
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=False,
            text=True
        )

        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Upload failed: {e}")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False
