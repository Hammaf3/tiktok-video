"""
PRODUCTION YouTube Downloader - Cloud Stable with Fallback Chain
Handles LOGIN_REQUIRED, age-restricted, and bot detection gracefully
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


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:200]


def download_youtube_video(
    url: str,
    use_cookies: bool = None,
    max_retries: int = 3
) -> Dict:
    """
    Production YouTube downloader with fallback chain

    Fallback order:
    1. Android client (most stable, no JS runtime)
    2. Web client (if android fails)
    3. iOS client (last resort)

    Args:
        url: YouTube video URL
        use_cookies: Auto-detect if None, force enable/disable if bool
        max_retries: Retry attempts per client (default: 3)

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        Exception with structured error info
    """
    logger.info(f"[DOWNLOAD] Starting: {url}")

    # Auto-detect cookies
    if use_cookies is None:
        use_cookies = YOUTUBE_COOKIES_FILE.exists()

    if use_cookies and YOUTUBE_COOKIES_FILE.exists():
        logger.info(f"[COOKIES] Using cookies from {YOUTUBE_COOKIES_FILE}")
        print(f"[COOKIES] Authentication enabled")
    else:
        logger.info(f"[COOKIES] No cookies - public access only")
        print(f"[COOKIES] Public mode (add youtube_cookies.txt for age-restricted videos)")
        use_cookies = False

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Client fallback chain
    clients = [
        {
            'name': 'android',
            'config': {
                'player_client': ['android'],
                'player_skip': ['webpage', 'configs'],
            },
            'format': 'best[ext=mp4][height<=1080]/best[height<=1080]/best',
        },
        {
            'name': 'web',
            'config': {
                'player_client': ['web'],
            },
            'format': 'best[ext=mp4][height<=1080]/best[height<=1080]/best',
        },
        {
            'name': 'ios',
            'config': {
                'player_client': ['ios'],
                'player_skip': ['webpage'],
            },
            'format': 'best[ext=mp4]/best',
        }
    ]

    last_error = None

    # Try each client in order
    for client in clients:
        logger.info(f"[CLIENT] Trying {client['name']} client...")
        print(f"[CLIENT] Attempting {client['name']} client...")

        try:
            result = _download_with_client(
                url=url,
                client_name=client['name'],
                client_config=client['config'],
                format_selector=client['format'],
                use_cookies=use_cookies,
                max_retries=max_retries
            )

            if result:
                logger.info(f"[SUCCESS] Downloaded using {client['name']} client")
                print(f"[SUCCESS] {client['name']} client worked!")
                return result

        except Exception as e:
            last_error = e
            error_msg = str(e).lower()

            # Check if error is retryable with next client
            is_retryable = any(keyword in error_msg for keyword in [
                'format', 'unavailable', 'extraction', 'player'
            ])

            if is_retryable:
                logger.warning(f"[FALLBACK] {client['name']} failed, trying next client...")
                print(f"[FALLBACK] {client['name']} failed, trying next...")
                continue
            else:
                # Non-retryable error (age-restricted, private, etc.)
                raise

    # All clients failed
    raise Exception(f"All extraction clients failed. Last error: {str(last_error)}")


def _download_with_client(
    url: str,
    client_name: str,
    client_config: dict,
    format_selector: str,
    use_cookies: bool,
    max_retries: int
) -> Optional[Dict]:
    """
    Download with specific client configuration
    """

    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s_%(id)s.%(ext)s'),
        'format': format_selector,
        'noplaylist': True,
        'quiet': False,
        'no_warnings': False,
        'retries': max_retries,
        'fragment_retries': max_retries,
        'skip_unavailable_fragments': True,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'extractor_args': {
            'youtube': client_config
        },
    }

    # Add cookies if available
    if use_cookies and YOUTUBE_COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)

    # JS runtime handling - disable for cloud stability
    ydl_opts['extractor_args']['youtube']['js'] = False

    attempt = 0
    while attempt < max_retries:
        attempt += 1

        try:
            logger.info(f"[ATTEMPT] {client_name} client: {attempt}/{max_retries}")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise Exception("Failed to extract video information")

                # Check restrictions
                if info.get('is_live'):
                    raise Exception(json.dumps({
                        'reason': 'LIVE_STREAM',
                        'solution': 'Cannot download live streams'
                    }))

                age_limit = info.get('age_limit', 0)
                if age_limit > 0 and not use_cookies:
                    raise Exception(json.dumps({
                        'reason': 'AGE_RESTRICTED',
                        'solution': 'Add youtube_cookies.txt for age-restricted videos'
                    }))

                availability = info.get('availability')
                if availability and availability != 'public':
                    if availability == 'needs_auth':
                        raise Exception(json.dumps({
                            'reason': 'LOGIN_REQUIRED',
                            'solution': 'Video requires authentication - add cookies.txt'
                        }))
                    elif availability == 'premium_only':
                        raise Exception(json.dumps({
                            'reason': 'MEMBERS_ONLY',
                            'solution': 'Members-only video'
                        }))
                    elif availability == 'private':
                        raise Exception(json.dumps({
                            'reason': 'PRIVATE',
                            'solution': 'Video is private'
                        }))

                title = info.get('title', 'Unknown')
                description = info.get('description', '')
                duration = info.get('duration', 0)
                video_id = info.get('id', 'unknown')

                logger.info(f"[VIDEO] {title} ({duration}s)")
                print(f"[VIDEO] {title}")

                # Verify formats available
                formats = info.get('formats', [])
                if not formats:
                    raise Exception("No downloadable formats available")

                # Download
                logger.info(f"[DOWNLOAD] Starting download...")
                start_time = time.time()
                ydl.download([url])
                elapsed = time.time() - start_time

                logger.info(f"[DOWNLOAD] Completed in {elapsed:.1f}s")

                # Find downloaded file
                video_files = list(DOWNLOAD_DIR.glob(f"*{video_id}*.mp4"))

                if not video_files:
                    sanitized_title = sanitize_filename(title)
                    video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized_title[:30]}*.mp4"))

                if not video_files:
                    for ext in ['mp4', 'webm', 'mkv']:
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
                file_size = video_path.stat().st_size / (1024 * 1024)

                if file_size < 0.1:
                    raise Exception("Downloaded file too small (corrupted)")

                logger.info(f"[SUCCESS] {video_path.name} ({file_size:.1f}MB)")

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

            # Check if should retry
            if any(keyword in error_msg for keyword in ['timeout', 'network', 'connection']):
                if attempt < max_retries:
                    wait = 2 * attempt
                    logger.warning(f"[RETRY] Network error, waiting {wait}s...")
                    time.sleep(wait)
                    continue

            # Parse specific errors
            if 'sign in' in error_msg or 'login' in error_msg:
                raise Exception(json.dumps({
                    'reason': 'LOGIN_REQUIRED',
                    'solution': 'Video requires sign-in - add cookies.txt or try different video'
                }))
            elif 'private' in error_msg:
                raise Exception(json.dumps({
                    'reason': 'PRIVATE',
                    'solution': 'Video is private'
                }))
            elif 'unavailable' in error_msg:
                raise Exception(json.dumps({
                    'reason': 'UNAVAILABLE',
                    'solution': 'Video unavailable (deleted or region-blocked)'
                }))
            elif 'http error 429' in error_msg:
                raise Exception(json.dumps({
                    'reason': 'RATE_LIMIT',
                    'solution': 'Rate limit reached - wait a few minutes'
                }))

            raise

        except Exception as e:
            error_str = str(e)

            # Don't retry known restrictions
            if any(keyword in error_str.lower() for keyword in [
                'age_restricted', 'login_required', 'private', 'members_only'
            ]):
                raise

            if attempt < max_retries:
                logger.warning(f"[RETRY] Attempt {attempt} failed, retrying...")
                time.sleep(2)
                continue

            raise

    return None


def cleanup_old_downloads(days: int = 1):
    """Remove old downloaded files"""
    try:
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 86400)

        deleted = 0
        for file_path in DOWNLOAD_DIR.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted += 1

        if deleted > 0:
            logger.info(f"[CLEANUP] Deleted {deleted} old files")
    except Exception as e:
        logger.warning(f"[CLEANUP] Failed: {e}")
