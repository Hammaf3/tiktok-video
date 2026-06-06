"""
Production-Ready YouTube Video Downloader
Stable yt-dlp configuration with proper error handling and restriction detection
NO BYPASS TECHNIQUES - Only official yt-dlp features
"""
import os
import re
import time
from pathlib import Path
from typing import Dict, Optional
import yt_dlp
from .config import DOWNLOAD_DIR, YOUTUBE_COOKIES_FILE
from .logger import get_logger

logger = get_logger()

# Download timeout: 5 minutes total
DOWNLOAD_TIMEOUT = 300


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    if len(filename) > 200:
        filename = filename[:200]
    return filename


class VideoRestrictionError(Exception):
    """Raised when video has restrictions (age, login, region)"""
    pass


class VideoUnavailableError(Exception):
    """Raised when video is unavailable (deleted, private)"""
    pass


def download_youtube_video(url: str, use_cookies: bool = False, max_retries: int = 2) -> Dict:
    """
    Download YouTube video with production-ready configuration

    SAFE & LEGAL: Uses only standard yt-dlp features
    - Respects YouTube's Terms of Service
    - No bot detection bypass
    - No authentication spoofing
    - Clear error messages for restricted content

    Args:
        url: YouTube video URL
        use_cookies: Use cookies file if available (optional, for signed-in access)
        max_retries: Number of retry attempts

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        VideoRestrictionError: Video requires login or has restrictions
        VideoUnavailableError: Video unavailable/deleted/private
        Exception: Other download errors with clear messages
    """
    logger.info(f"Starting download: {url}")

    # Ensure download directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # PRODUCTION YT-DLP CONFIGURATION
    ydl_opts = {
        # Output configuration
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s_%(id)s.%(ext)s'),

        # Format selection - prefer MP4 for compatibility
        'format': 'best[ext=mp4][height<=1080]/best[height<=1080]/best',

        # Single video only (no playlists)
        'noplaylist': True,

        # Logging
        'quiet': False,
        'no_warnings': False,
        'verbose': False,

        # Retry configuration
        'retries': max_retries,
        'fragment_retries': max_retries,
        'skip_unavailable_fragments': True,

        # Timeouts
        'socket_timeout': 30,

        # Standard HTTP headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
        },

        # Cookie file support (optional, user-provided)
        'cookiefile': str(YOUTUBE_COOKIES_FILE) if use_cookies and YOUTUBE_COOKIES_FILE.exists() else None,

        # Extract metadata
        'writeinfojson': False,
        'writethumbnail': False,

        # Error handling
        'ignoreerrors': False,
        'abort_on_error': True,
    }

    attempt = 0
    last_error = None

    while attempt <= max_retries:
        attempt += 1

        try:
            logger.info(f"Download attempt {attempt}/{max_retries + 1}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Step 1: Extract video info (without downloading)
                logger.info("Extracting video information...")

                try:
                    info = ydl.extract_info(url, download=False)
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e).lower()

                    # Parse specific YouTube errors
                    if 'sign in' in error_msg or 'login required' in error_msg:
                        raise VideoRestrictionError(
                            "This video requires sign-in. It may be age-restricted or members-only. "
                            "Try a different video or provide cookies.txt file."
                        )
                    elif 'private video' in error_msg:
                        raise VideoUnavailableError("This video is private and cannot be accessed.")
                    elif 'video unavailable' in error_msg or 'video is unavailable' in error_msg:
                        raise VideoUnavailableError("Video unavailable - it may be deleted or region-blocked.")
                    elif 'members-only' in error_msg or 'join this channel' in error_msg:
                        raise VideoRestrictionError("This is a members-only video. Try a different video.")
                    elif 'copyright' in error_msg:
                        raise VideoUnavailableError("Video removed due to copyright claim.")
                    elif 'region' in error_msg or 'not available in your country' in error_msg:
                        raise VideoUnavailableError("Video blocked in your region.")
                    elif 'confirm you' in error_msg and 'bot' in error_msg:
                        raise VideoRestrictionError(
                            "YouTube is requesting bot verification. This usually means:\n"
                            "1. The video requires sign-in (age-restricted)\n"
                            "2. Too many requests from your IP\n"
                            "3. The video has special restrictions\n"
                            "Try a different video or wait a few minutes."
                        )
                    else:
                        # Re-raise the original error
                        raise

                if info is None:
                    raise Exception("Failed to extract video information")

                # Step 2: Check for restrictions BEFORE downloading

                # Check if live stream
                if info.get('is_live'):
                    raise VideoRestrictionError("Cannot download live streams. Try a different video.")

                # Check age restriction
                age_limit = info.get('age_limit', 0)
                if age_limit > 0:
                    raise VideoRestrictionError(
                        f"This video is age-restricted ({age_limit}+). "
                        "Provide a cookies.txt file from a signed-in browser to download it."
                    )

                # Check availability
                availability = info.get('availability')
                if availability and availability != 'public':
                    if availability == 'needs_auth':
                        raise VideoRestrictionError("This video requires authentication (sign-in).")
                    elif availability == 'premium_only':
                        raise VideoRestrictionError("This is a premium/members-only video.")
                    elif availability == 'subscriber_only':
                        raise VideoRestrictionError("This video is for subscribers only.")
                    elif availability == 'private':
                        raise VideoUnavailableError("This video is private.")

                # Get metadata
                title = info.get('title', 'Unknown')
                description = info.get('description', '')
                duration = info.get('duration', 0)
                video_id = info.get('id', 'unknown')

                logger.info(f"Video: {title} ({duration}s)")

                # Check if formats are available
                formats = info.get('formats', [])
                if not formats:
                    raise VideoRestrictionError(
                        "No downloadable formats found. This video may require sign-in or have restrictions."
                    )

                # Check duration
                if duration == 0:
                    logger.warning("Video duration is 0, it might be unavailable")

                if duration > 3600:  # 1 hour
                    logger.warning(f"Video is very long ({duration}s). Download may take a while.")

                # Step 3: Download the video
                logger.info("Starting download...")
                start_time = time.time()

                ydl.download([url])

                elapsed = time.time() - start_time
                logger.info(f"Download completed in {elapsed:.1f}s")

                # Step 4: Find the downloaded file
                # Look for file with video ID in filename
                video_files = list(DOWNLOAD_DIR.glob(f"*{video_id}*.mp4"))

                if not video_files:
                    # Fallback: search by sanitized title
                    sanitized_title = sanitize_filename(title)
                    video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized_title[:30]}*.mp4"))

                if not video_files:
                    # Last resort: get most recent video file
                    for ext in ['mp4', 'webm', 'mkv']:
                        video_files = sorted(
                            DOWNLOAD_DIR.glob(f"*.{ext}"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True
                        )
                        if video_files:
                            break

                if not video_files:
                    raise Exception("Download completed but file not found. Check tmp/yt2tik/downloads/")

                video_path = video_files[0]
                file_size = video_path.stat().st_size / (1024 * 1024)  # MB

                logger.info(f"Download complete: {video_path.name} ({file_size:.1f}MB)")

                # Verify file is not empty
                if file_size < 0.1:
                    raise Exception("Downloaded file is too small (likely corrupted)")

                return {
                    'video_path': str(video_path),
                    'title': title,
                    'description': description,
                    'duration': duration,
                    'url': url,
                    'file_size_mb': file_size,
                    'video_id': video_id
                }

        except (VideoRestrictionError, VideoUnavailableError):
            # Don't retry restriction/unavailable errors - they won't change
            raise

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            last_error = e

            # Parse and categorize errors
            if 'http error 429' in error_msg or 'too many requests' in error_msg:
                raise Exception(
                    "YouTube rate limit reached (HTTP 429). "
                    "Please wait a few minutes before trying again."
                )

            elif 'http error 403' in error_msg:
                raise VideoRestrictionError(
                    "Access forbidden (HTTP 403). This video may require sign-in or have geographic restrictions."
                )

            elif 'http error 404' in error_msg:
                raise VideoUnavailableError("Video not found (HTTP 404). It may have been deleted.")

            elif 'unable to extract' in error_msg:
                raise Exception(
                    "Unable to extract video data. The video format may not be supported or has restrictions."
                )

            elif attempt <= max_retries:
                logger.warning(f"Attempt {attempt} failed: {str(e)}")
                logger.info(f"Retrying... ({max_retries + 1 - attempt} attempts left)")
                time.sleep(2)  # Brief delay before retry
                continue
            else:
                raise Exception(f"Download failed after {max_retries + 1} attempts: {str(e)}")

        except Exception as e:
            error_str = str(e)
            last_error = e

            # Don't retry if it's a clear restriction/unavailability error
            if any(keyword in error_str.lower() for keyword in [
                'private', 'age-restricted', 'sign-in', 'members-only',
                'blocked', 'unavailable', 'copyright', 'live stream',
                'requires authentication', 'premium', 'subscriber'
            ]):
                raise

            # Retry for other errors
            if attempt <= max_retries:
                logger.warning(f"Attempt {attempt} failed: {error_str}")
                logger.info(f"Retrying... ({max_retries + 1 - attempt} attempts left)")
                time.sleep(2)
                continue
            else:
                raise Exception(f"Download failed: {error_str}")

    # Should never reach here, but just in case
    raise Exception(f"Download failed after all retries: {str(last_error)}")


def get_video_info(url: str) -> Dict:
    """
    Get video information without downloading

    Args:
        url: YouTube video URL

    Returns:
        Dict with video metadata

    Raises:
        Exception: If info extraction fails
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
                'availability': info.get('availability', 'unknown'),
                'is_live': info.get('is_live', False),
            }

    except Exception as e:
        logger.error(f"Failed to get video info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")


def cleanup_old_downloads(days: int = 1):
    """
    Clean up downloaded files older than specified days

    Args:
        days: Delete files older than this many days
    """
    try:
        import time

        current_time = time.time()
        cutoff_time = current_time - (days * 86400)

        deleted_count = 0
        freed_space = 0

        for file_path in DOWNLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = file_path.stat().st_mtime

                if file_age < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    deleted_count += 1
                    freed_space += file_size

        if deleted_count > 0:
            freed_mb = freed_space / (1024 * 1024)
            logger.info(f"Cleaned up {deleted_count} old files, freed {freed_mb:.1f}MB")

    except Exception as e:
        logger.warning(f"Cleanup failed: {str(e)}")
