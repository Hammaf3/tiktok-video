"""
YouTube Downloader - Respects YouTube Restrictions
Returns clear errors when videos require authentication or are restricted
"""
import re
import os
from pathlib import Path
from typing import Dict
import yt_dlp
from .config import DOWNLOAD_DIR, YOUTUBE_COOKIES_FILE
from .logger import get_logger

logger = get_logger()


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:200]


def download_youtube_video(url: str) -> Dict:
    """
    Download YouTube video with graceful error handling

    Returns structured data or raises exception with clear error message
    """
    logger.info(f"📥 Attempting to download: {url}")

    # Simple, honest yt-dlp configuration
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'fragment_retries': 3,
    }

    # Add cookies if available (user must provide their own authenticated cookies)
    if YOUTUBE_COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
        logger.info("🍪 Using cookies file")
    else:
        logger.info("ℹ️  No cookies file - public videos only")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract video info
            logger.info("📊 Extracting video information...")
            info = ydl.extract_info(url, download=False)

            if not info:
                raise Exception("Failed to extract video information")

            # Check if video is restricted
            if info.get('is_live'):
                raise Exception("LIVE_STREAM: Cannot download live streams")

            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            logger.info(f"📹 Video: {title} ({duration}s)")

            # Download the video
            logger.info("⬇️  Downloading video...")
            ydl.download([url])

            # Find downloaded file
            sanitized = sanitize_filename(title)
            video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized[:50]}*.mp4"))

            if not video_files:
                video_files = sorted(
                    DOWNLOAD_DIR.glob("*.mp4"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True
                )

            if not video_files:
                raise Exception("Downloaded file not found")

            video_path = video_files[0]
            file_size_mb = video_path.stat().st_size / (1024 * 1024)

            logger.info(f"✅ Download complete: {video_path.name} ({file_size_mb:.1f} MB)")

            return {
                'video_path': str(video_path),
                'title': title,
                'description': info.get('description', ''),
                'duration': duration,
                'url': url
            }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        logger.error(f"❌ yt-dlp error: {str(e)}")

        # Detect YouTube restriction errors
        if any(phrase in error_msg for phrase in [
            'sign in', 'login', 'bot', 'confirm you', 'requires payment',
            'members-only', 'members only', 'join this channel'
        ]):
            raise Exception(
                "RESTRICTED: This video cannot be downloaded because YouTube requires "
                "authentication or restricts access. This may be due to: age restrictions, "
                "membership requirements, or bot detection."
            )
        elif 'private video' in error_msg:
            raise Exception("RESTRICTED: This video is private and cannot be accessed")
        elif 'video unavailable' in error_msg:
            raise Exception("UNAVAILABLE: Video is unavailable, deleted, or region-locked")
        elif 'copyright' in error_msg:
            raise Exception("COPYRIGHT: Video removed due to copyright claim")
        elif any(phrase in error_msg for phrase in ['age', 'age-restricted', 'inappropriate']):
            raise Exception(
                "RESTRICTED: This video is age-restricted and requires authentication"
            )
        else:
            raise Exception(f"DOWNLOAD_FAILED: {str(e)}")

    except Exception as e:
        error_str = str(e)
        logger.error(f"❌ Download failed: {error_str}")

        # If already formatted error, re-raise
        if error_str.startswith(('RESTRICTED:', 'UNAVAILABLE:', 'COPYRIGHT:', 'DOWNLOAD_FAILED:', 'LIVE_STREAM:')):
            raise
        else:
            raise Exception(f"DOWNLOAD_FAILED: {error_str}")


def get_video_info(url: str) -> Dict:
    """Get video info without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    if YOUTUBE_COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'description': info.get('description', ''),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'channel': info.get('channel', 'Unknown'),
                'upload_date': info.get('upload_date', ''),
            }
    except Exception as e:
        raise Exception(f"Failed to get video info: {str(e)}")
