"""
Production-Ready YouTube Downloader with Retry Logic
Handles LOGIN_REQUIRED errors and Railway deployment issues
"""
import re
import os
import time
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
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def download_youtube_video(url: str, max_retries: int = 2) -> Dict:
    """
    Download YouTube video with production-safe configuration

    Features:
    - Automatic retry on LOGIN_REQUIRED errors
    - Optional cookies.txt support
    - Clean error messages
    - Railway/cloud platform compatible

    Args:
        url: YouTube video URL
        max_retries: Number of retry attempts (default: 2)

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        Exception: With clear error message if download fails
    """
    logger.info(f"[DOWNLOAD] Starting: {url}")

    # Ensure download directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Check if cookies file exists
    use_cookies = YOUTUBE_COOKIES_FILE.exists()

    if use_cookies:
        logger.info(f"[COOKIES] Using cookies from: {YOUTUBE_COOKIES_FILE}")
        print(f"[INFO] Cookies file found - authentication enabled")
    else:
        logger.info(f"[COOKIES] No cookies file - using public access only")
        print(f"[INFO] No cookies - public videos only")

    # Production-safe yt-dlp configuration
    ydl_opts = {
        # Output configuration
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s_%(id)s.%(ext)s'),

        # Format: prefer MP4, avoid complex merging
        'format': 'best[ext=mp4][height<=1080]/best[height<=1080]/best',

        # Single video only
        'noplaylist': True,

        # Logging
        'quiet': False,
        'no_warnings': False,

        # Retry configuration
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,

        # Timeout (5 minutes total)
        'socket_timeout': 30,

        # HTTP headers (standard browser)
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        },

        # Cookies (optional)
        'cookiefile': str(YOUTUBE_COOKIES_FILE) if use_cookies else None,

        # Error handling
        'ignoreerrors': False,
        'abort_on_error': True,
    }

    attempt = 0
    last_error = None

    while attempt <= max_retries:
        attempt += 1

        try:
            logger.info(f"[ATTEMPT] {attempt}/{max_retries + 1}")
            print(f"[ATTEMPT] Downloading... (attempt {attempt}/{max_retries + 1})")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first (without downloading)
                logger.info("[INFO] Extracting video information...")
                print(f"[INFO] Extracting video information...")

                try:
                    info = ydl.extract_info(url, download=False)
                except yt_dlp.utils.DownloadError as e:
                    error_msg = str(e).lower()

                    # Handle specific YouTube errors
                    if 'sign in' in error_msg or 'login required' in error_msg:
                        if not use_cookies:
                            raise Exception(
                                "This video requires sign-in (age-restricted or members-only). "
                                "Add youtube_cookies.txt file to download age-restricted videos."
                            )
                        else:
                            raise Exception(
                                "Login required even with cookies. Video may be members-only or your cookies expired."
                            )
                    elif 'private video' in error_msg:
                        raise Exception("This video is private and cannot be accessed.")
                    elif 'video unavailable' in error_msg:
                        raise Exception("Video unavailable - it may be deleted or region-blocked.")
                    elif 'copyright' in error_msg:
                        raise Exception("Video removed due to copyright claim.")
                    else:
                        # Re-raise for retry logic
                        raise

                if info is None:
                    raise Exception("Failed to extract video information")

                # Check restrictions BEFORE downloading
                if info.get('is_live'):
                    raise Exception("Cannot download live streams")

                age_limit = info.get('age_limit', 0)
                if age_limit > 0 and not use_cookies:
                    raise Exception(
                        f"Age-restricted video ({age_limit}+). "
                        "Add youtube_cookies.txt from a signed-in browser to download it."
                    )

                # Get metadata
                title = info.get('title', 'Unknown')
                description = info.get('description', '')
                duration = info.get('duration', 0)
                video_id = info.get('id', 'unknown')

                logger.info(f"[VIDEO] {title} ({duration}s)")
                print(f"[VIDEO] {title}")
                print(f"[DURATION] {duration} seconds")

                # Check if formats are available
                formats = info.get('formats', [])
                if not formats:
                    raise Exception(
                        "No downloadable formats found. Video may require authentication or have restrictions."
                    )

                # Download the video
                logger.info("[DOWNLOAD] Starting download...")
                print(f"[DOWNLOAD] Downloading video...")

                start_time = time.time()
                ydl.download([url])
                elapsed = time.time() - start_time

                logger.info(f"[SUCCESS] Downloaded in {elapsed:.1f}s")
                print(f"[SUCCESS] Download completed in {elapsed:.1f} seconds")

                # Find the downloaded file
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
                    raise Exception("Download completed but file not found in output directory")

                video_path = video_files[0]
                file_size = video_path.stat().st_size / (1024 * 1024)  # MB

                logger.info(f"[FILE] {video_path.name} ({file_size:.1f}MB)")
                print(f"[FILE] {video_path.name} ({file_size:.1f} MB)")

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

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            last_error = e

            logger.warning(f"[RETRY] Attempt {attempt} failed: {str(e)}")

            # Check if error is retryable
            is_retryable = any(keyword in error_msg for keyword in [
                'timeout', 'timed out', 'connection', 'network',
                'http error 429', 'http error 503', 'http error 500'
            ])

            if is_retryable and attempt <= max_retries:
                wait_time = 2 * attempt  # Exponential backoff: 2s, 4s, 6s
                logger.info(f"[WAIT] Retrying in {wait_time} seconds...")
                print(f"[RETRY] Network error, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue

            # Non-retryable errors or max retries exceeded
            if 'http error 429' in error_msg:
                raise Exception("YouTube rate limit reached. Please try again in a few minutes.")
            elif 'http error 403' in error_msg:
                raise Exception("Access forbidden. Video may have geographic restrictions.")
            elif 'http error 404' in error_msg:
                raise Exception("Video not found. It may have been deleted.")
            else:
                raise Exception(f"Download failed: {str(e)}")

        except Exception as e:
            error_str = str(e)
            last_error = e

            # Don't retry if it's a clear restriction error
            if any(keyword in error_str.lower() for keyword in [
                'private', 'age-restricted', 'sign-in', 'members-only',
                'blocked', 'unavailable', 'copyright', 'live stream',
                'requires authentication'
            ]):
                raise

            # Retry for other errors
            if attempt <= max_retries:
                logger.warning(f"[RETRY] Attempt {attempt} failed: {error_str}")
                print(f"[RETRY] Error occurred, retrying...")
                time.sleep(2)
                continue
            else:
                raise Exception(f"Download failed: {error_str}")

    # Should never reach here, but just in case
    raise Exception(f"Download failed after {max_retries + 1} attempts: {str(last_error)}")


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
            logger.info(f"[CLEANUP] Deleted {deleted_count} old files, freed {freed_mb:.1f}MB")

    except Exception as e:
        logger.warning(f"[CLEANUP] Cleanup failed: {str(e)}")
