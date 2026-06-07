"""
Enhanced YouTube Downloader with Comprehensive Error Detection
Handles HTTP 429, login requirements, private videos, and network failures
"""
import re
import os
import time
from pathlib import Path
from typing import Dict, Optional
import yt_dlp
from .config import DOWNLOAD_DIR, YOUTUBE_COOKIES_FILE
from .logger import get_logger

logger = get_logger()


class DownloadError(Exception):
    """Custom exception for download errors with error codes"""
    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:200]


def exponential_backoff_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry with exponential backoff for temporary network failures

    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)

    Returns:
        Function result or raises last exception
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            error_msg = str(e).lower()

            # Don't retry on permanent errors
            if any(phrase in error_msg for phrase in [
                'private video', 'video unavailable', 'copyright',
                'members-only', 'requires payment', 'age-restricted',
                'sign in to confirm', 'login required'
            ]):
                logger.info(f"Permanent error detected, not retrying: {str(e)}")
                raise

            # Retry on temporary network errors
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed")
                raise last_exception


def detect_error_type(error_msg: str) -> tuple[str, str]:
    """
    Detect specific error types from yt-dlp error messages

    Returns:
        (error_code, user_friendly_message)
    """
    error_lower = error_msg.lower()

    # HTTP 429 - Rate limiting
    if '429' in error_msg or 'too many requests' in error_lower:
        return (
            'HTTP_429',
            'YouTube is rate limiting requests. This video cannot be downloaded right now. '
            'Please try again in a few minutes, or try a different video.'
        )

    # Login required / Bot detection
    if any(phrase in error_lower for phrase in [
        'sign in', 'login', 'bot', 'confirm you', 'confirm your',
        'unusual traffic', 'captcha'
    ]):
        return (
            'LOGIN_REQUIRED',
            'YouTube requires authentication to download this video. This may be due to bot detection '
            'or unusual traffic patterns. Please try a different video or wait a few minutes.'
        )

    # Private video
    if 'private video' in error_lower or 'private' in error_lower:
        return (
            'PRIVATE_VIDEO',
            'This video is private and cannot be accessed. Only the video owner can view private videos.'
        )

    # Membership/payment required
    if any(phrase in error_lower for phrase in [
        'members-only', 'members only', 'join this channel', 'requires payment'
    ]):
        return (
            'MEMBERSHIP_REQUIRED',
            'This video requires channel membership or payment to access. Only members can download this content.'
        )

    # Video unavailable
    if 'video unavailable' in error_lower or 'unavailable' in error_lower:
        return (
            'VIDEO_UNAVAILABLE',
            'This video is unavailable. It may have been deleted, made private, or is region-locked.'
        )

    # Copyright takedown
    if 'copyright' in error_lower:
        return (
            'COPYRIGHT_CLAIM',
            'This video has been removed due to a copyright claim and cannot be downloaded.'
        )

    # Age-restricted
    if any(phrase in error_lower for phrase in ['age', 'age-restricted', 'inappropriate']):
        return (
            'AGE_RESTRICTED',
            'This video is age-restricted and requires authentication. Please try a different video.'
        )

    # Live stream
    if 'live' in error_lower and 'stream' in error_lower:
        return (
            'LIVE_STREAM',
            'Cannot download live streams. Please wait until the stream ends and try again.'
        )

    # Network/connection errors (temporary)
    if any(phrase in error_lower for phrase in [
        'connection', 'timeout', 'network', 'unable to connect',
        'failed to establish', 'timed out'
    ]):
        return (
            'NETWORK_ERROR',
            'Network connection error. Please check your internet connection and try again.'
        )

    # Generic download failure
    return (
        'DOWNLOAD_FAILED',
        f'Download failed: {error_msg[:200]}'
    )


def download_youtube_video(url: str) -> Dict:
    """
    Download YouTube video with comprehensive error handling and retry logic

    Args:
        url: YouTube video URL

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        DownloadError: With specific error code and user-friendly message
    """
    logger.info(f"📥 Starting download: {url}")

    # Configure yt-dlp with production-ready settings
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'format': 'best[ext=mp4]/best',
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'fragment_retries': 3,
        'socket_timeout': 30,
        'http_chunk_size': 10485760,  # 10MB chunks
    }

    # Add cookies if available
    if YOUTUBE_COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
        logger.info("🍪 Using cookies file for authentication")
    else:
        logger.info("ℹ️  No cookies file - downloading public videos only")

    def download_attempt():
        """Single download attempt wrapped for retry logic"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info first
                logger.info("📊 Extracting video information...")
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise DownloadError(
                        "Failed to extract video information",
                        "EXTRACTION_FAILED"
                    )

                # Check if video is a live stream
                if info.get('is_live'):
                    raise DownloadError(
                        "Cannot download live streams",
                        "LIVE_STREAM"
                    )

                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)

                logger.info(f"📹 Video: {title} ({duration}s)")

                # Download the video
                logger.info("⬇️  Downloading video...")
                ydl.download([url])

                # Find the downloaded file
                sanitized = sanitize_filename(title)
                video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized[:50]}*.mp4"))

                if not video_files:
                    # Fallback: find most recent mp4
                    video_files = sorted(
                        DOWNLOAD_DIR.glob("*.mp4"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )

                if not video_files:
                    raise DownloadError(
                        "Downloaded file not found on disk",
                        "FILE_NOT_FOUND"
                    )

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
            error_msg = str(e)
            logger.error(f"❌ yt-dlp error: {error_msg}")

            # Detect specific error type
            error_code, user_message = detect_error_type(error_msg)
            raise DownloadError(user_message, error_code)

        except DownloadError:
            # Re-raise our custom errors
            raise

        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Unexpected error: {error_msg}")
            raise DownloadError(
                f"Unexpected error during download: {error_msg[:200]}",
                "UNKNOWN_ERROR"
            )

    # Execute with retry logic
    try:
        return exponential_backoff_retry(download_attempt, max_retries=3, base_delay=2.0)
    except DownloadError:
        # Re-raise with original error code
        raise
    except Exception as e:
        # Wrap any other exception
        error_code, user_message = detect_error_type(str(e))
        raise DownloadError(user_message, error_code)


def get_video_info(url: str) -> Optional[Dict]:
    """
    Get video information without downloading

    Args:
        url: YouTube video URL

    Returns:
        Video info dict or None on error
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 10,
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
                'is_live': info.get('is_live', False),
            }
    except Exception as e:
        logger.error(f"Failed to get video info: {str(e)}")
        return None
