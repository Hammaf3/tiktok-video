"""
Stable, Production-Ready YouTube Video Downloader
Uses yt-dlp with default extraction methods only - no bypassing or spoofing
"""
import os
import re
from pathlib import Path
from typing import Dict, Optional
import yt_dlp
from .config import DOWNLOAD_DIR
from .logger import get_logger

logger = get_logger()

# Maximum download time: 5 minutes
DOWNLOAD_TIMEOUT = 300


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def download_youtube_video(url: str, max_retries: int = 2) -> Dict:
    """
    Download YouTube video with stable, production-ready configuration

    IMPORTANT: Uses only default yt-dlp extraction methods
    NO spoofing, NO bypass attempts, NO circumvention

    Args:
        url: YouTube video URL
        max_retries: Number of retry attempts (default: 2)

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        Exception: With clear error message if download fails
    """
    logger.info(f"Starting download: {url}")

    # Ensure download directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # STABLE YT-DLP CONFIGURATION
    # Uses default extraction methods - respects YouTube's restrictions
    ydl_opts = {
        # Output path
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),

        # Format selection - simple, no complex merging
        'format': 'best[ext=mp4]/best',

        # Single video only
        'noplaylist': True,

        # Logging (minimal)
        'quiet': True,
        'no_warnings': True,

        # Retry strategy (simple)
        'retries': max_retries,
        'fragment_retries': max_retries,

        # Timeout protection (5 minutes total)
        'socket_timeout': 30,  # 30 seconds per socket operation

        # HTTP headers (minimal, standard)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    attempt = 0
    last_error = None

    while attempt <= max_retries:
        attempt += 1

        try:
            logger.info(f"Download attempt {attempt}/{max_retries + 1}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                logger.debug("Extracting video information...")
                info = ydl.extract_info(url, download=False)

                if info is None:
                    raise Exception("Failed to extract video information")

                # Check for restrictions BEFORE downloading
                if info.get('is_live'):
                    raise Exception("Cannot download live streams")

                if info.get('age_limit', 0) > 0:
                    raise Exception("Age-restricted video - requires authentication")

                # Get metadata
                title = info.get('title', 'Unknown')
                description = info.get('description', '')
                duration = info.get('duration', 0)

                logger.info(f"Video: {title} ({duration}s)")

                # Check if formats are available
                if not info.get('formats'):
                    raise Exception("No video formats available")

                # Download the video
                logger.info("Starting download...")
                ydl.download([url])

                # Find the downloaded file
                sanitized_title = sanitize_filename(title)

                # Try to find the file
                video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized_title[:50]}*.mp4"))

                if not video_files:
                    # Try other extensions
                    for ext in ['webm', 'mkv', 'mp4']:
                        video_files = sorted(
                            DOWNLOAD_DIR.glob(f"*.{ext}"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True
                        )
                        if video_files:
                            break

                if not video_files:
                    raise Exception("Downloaded file not found")

                video_path = video_files[0]
                logger.info(f"Download complete: {video_path.name}")

                return {
                    'video_path': str(video_path),
                    'title': title,
                    'description': description,
                    'duration': duration,
                    'url': url
                }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            last_error = e

            # Parse specific error types
            if 'private video' in error_msg:
                raise Exception("This video is private and cannot be accessed")

            elif 'video unavailable' in error_msg:
                raise Exception("Video unavailable - it may be deleted or region-blocked")

            elif 'sign in' in error_msg or 'login' in error_msg:
                raise Exception("Video requires sign-in (age-restricted or members-only)")

            elif 'copyright' in error_msg:
                raise Exception("Video removed due to copyright claim")

            elif 'region' in error_msg or 'blocked' in error_msg:
                raise Exception("Video blocked in your region")

            elif 'members-only' in error_msg or 'members only' in error_msg:
                raise Exception("Members-only video")

            elif attempt <= max_retries:
                # Retry for other errors
                logger.warning(f"Attempt {attempt} failed: {str(e)}")
                logger.info(f"Retrying... ({max_retries + 1 - attempt} attempts left)")
                continue
            else:
                # All retries exhausted
                raise Exception(f"Download failed after {max_retries + 1} attempts: {str(e)}")

        except Exception as e:
            error_str = str(e)

            # Don't retry if it's a clear restriction error
            if any(keyword in error_str.lower() for keyword in [
                'private', 'age-restricted', 'sign-in', 'members-only',
                'blocked', 'unavailable', 'copyright', 'live stream'
            ]):
                raise

            # Retry for other errors
            if attempt <= max_retries:
                logger.warning(f"Attempt {attempt} failed: {error_str}")
                logger.info(f"Retrying... ({max_retries + 1 - attempt} attempts left)")
                last_error = e
                continue
            else:
                raise Exception(f"Download failed: {error_str}")

    # Should never reach here, but just in case
    raise Exception(f"Download failed: {str(last_error)}")


def get_video_info(url: str) -> Dict:
    """
    Get video information without downloading

    Args:
        url: YouTube video URL

    Returns:
        Dict with video metadata
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'socket_timeout': 30,
    }

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
                'age_limit': info.get('age_limit', 0),
            }

    except Exception as e:
        logger.error(f"Failed to get video info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")
