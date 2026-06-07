"""
PRODUCTION YouTube Downloader - Cloud-Stable yt-dlp Configuration
Handles all edge cases: LOGIN_REQUIRED, age-restricted, member-only, bot detection
"""
import os
import re
import base64
from pathlib import Path
from typing import Dict, Optional
import yt_dlp
from .config import DOWNLOAD_DIR, YOUTUBE_COOKIES_FILE
from .logger import get_logger

logger = get_logger()


class DownloadError(Exception):
    """Custom exception with error codes"""
    def __init__(self, message: str, reason: str, solution: str):
        super().__init__(message)
        self.reason = reason
        self.solution = solution


def setup_cookies_from_env() -> bool:
    """Load cookies from environment variable (base64 encoded)"""
    env_cookies = os.getenv('YOUTUBE_COOKIES_BASE64')

    if env_cookies:
        try:
            YOUTUBE_COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            decoded = base64.b64decode(env_cookies).decode('utf-8')
            YOUTUBE_COOKIES_FILE.write_text(decoded, encoding='utf-8')
            logger.info(f"✅ Cookies loaded from environment")
            return True
        except Exception as e:
            logger.error(f"Failed to decode cookies: {e}")
            return False

    if YOUTUBE_COOKIES_FILE.exists():
        logger.info(f"✅ Using existing cookies file")
        return True

    logger.info("ℹ️  No cookies - public videos only")
    return False


def get_ydl_config(use_cookies: bool = False, client: str = 'android') -> dict:
    """
    Get yt-dlp configuration for cloud deployment

    Args:
        use_cookies: Enable cookie authentication (for age-restricted videos)
        client: Client to use ('android', 'web', 'ios')

    Returns:
        yt-dlp configuration dict
    """
    config = {
        # Ignore external config files
        'no_config': True,

        # Output template
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),

        # Simple format - no merging (critical for cloud stability)
        'format': 'best[ext=mp4]/best',

        # Single video only
        'noplaylist': True,

        # Logging
        'quiet': False,
        'no_warnings': False,

        # Retry strategy
        'retries': 3,
        'fragment_retries': 3,

        # Disable JS runtime (not needed for android/ios clients)
        'js_runtimes': {},

        # HTTP headers
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; US) gzip',
            'Accept-Language': 'en-US,en;q=0.9',
        },
    }

    # Client-specific configuration
    if client == 'android':
        config['extractor_args'] = {
            'youtube': {
                'player_client': ['android'],
                'player_skip': ['webpage', 'configs'],
                'skip': ['hls', 'dash'],
            }
        }
    elif client == 'ios':
        config['extractor_args'] = {
            'youtube': {
                'player_client': ['ios'],
                'player_skip': ['webpage'],
            }
        }
    elif client == 'web':
        config['extractor_args'] = {
            'youtube': {
                'player_client': ['web'],
            }
        }

    # Add cookies if available and requested
    if use_cookies and YOUTUBE_COOKIES_FILE.exists():
        config['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
        logger.info(f"🍪 Cookies enabled (client: {client})")
    else:
        logger.info(f"🚀 Public mode (client: {client})")

    return config


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    filename = filename.replace(' ', '_')
    return filename[:200]


def download_youtube_video(url: str, max_retries: int = 3) -> Dict:
    """
    Download YouTube video with multi-client fallback strategy

    Strategy:
    1. Try android client (no cookies) - works for 95% of public videos
    2. Try android client (with cookies) - works for age-restricted
    3. Try ios client (with cookies) - fallback for special cases
    4. Try web client (with cookies) - last resort

    Args:
        url: YouTube video URL
        max_retries: Number of retry attempts per client

    Returns:
        Dict with video_path, title, description, duration, url

    Raises:
        DownloadError: With structured error information
    """
    logger.info(f"📥 Starting download: {url}")

    # Setup cookies from environment
    has_cookies = setup_cookies_from_env()

    # Define fallback chain
    fallback_chain = [
        ('android', False),  # Android without cookies (fastest, most reliable)
    ]

    if has_cookies:
        fallback_chain.extend([
            ('android', True),   # Android with cookies (age-restricted)
            ('ios', True),       # iOS with cookies (fallback)
            ('web', True),       # Web with cookies (last resort)
        ])

    last_error = None

    for attempt_num, (client, use_cookies) in enumerate(fallback_chain, 1):
        try:
            logger.info(f"🔄 Attempt {attempt_num}/{len(fallback_chain)}: client={client}, cookies={use_cookies}")

            config = get_ydl_config(use_cookies=use_cookies, client=client)

            with yt_dlp.YoutubeDL(config) as ydl:
                # Extract info
                logger.info("📊 Extracting video info...")
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise Exception("Failed to extract video info")

                # Check restrictions
                if info.get('is_live'):
                    raise DownloadError(
                        "Cannot download live streams",
                        "LIVE_STREAM",
                        "Wait for stream to end or use a regular video"
                    )

                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)

                logger.info(f"📹 Video: {title} ({duration}s)")

                # Verify formats available
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']

                if not video_formats:
                    logger.warning(f"No video formats found with {client} client")
                    continue  # Try next client

                logger.info(f"✅ {len(video_formats)} formats available")

                # Download
                logger.info("⬇️  Downloading...")
                ydl.download([url])

                # Find downloaded file
                sanitized = sanitize_filename(title)
                video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized[:50]}*.mp4"))

                if not video_files:
                    # Try any recent MP4
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
            logger.warning(f"❌ {client} client failed: {str(e)}")

            # Check if this is a fatal error (don't retry)
            if 'private video' in error_msg:
                raise DownloadError(
                    "This video is private",
                    "PRIVATE_VIDEO",
                    "Video owner must change privacy settings"
                )
            elif 'video unavailable' in error_msg:
                raise DownloadError(
                    "Video unavailable",
                    "UNAVAILABLE",
                    "Video may be deleted or region-locked"
                )
            elif 'copyright' in error_msg:
                raise DownloadError(
                    "Video removed due to copyright",
                    "COPYRIGHT",
                    "Try a different video"
                )
            elif 'members-only' in error_msg or 'join this channel' in error_msg:
                raise DownloadError(
                    "Members-only video",
                    "MEMBERS_ONLY",
                    "This video requires channel membership"
                )

            # Retriable errors - continue to next client
            last_error = e
            continue

        except Exception as e:
            logger.warning(f"❌ {client} client failed: {str(e)}")
            last_error = e
            continue

    # All clients failed
    if last_error:
        error_msg = str(last_error).lower()

        if 'sign in' in error_msg or 'login' in error_msg or 'bot' in error_msg:
            if has_cookies:
                raise DownloadError(
                    "YouTube bot detection triggered",
                    "BOT_DETECTION",
                    "Cookies may be invalid. Try refreshing cookies or use a different video."
                )
            else:
                raise DownloadError(
                    "Age-restricted or login required",
                    "LOGIN_REQUIRED",
                    "Add YouTube cookies to enable age-restricted videos"
                )
        elif 'age' in error_msg:
            raise DownloadError(
                "Age-restricted video",
                "AGE_RESTRICTED",
                "Add YouTube cookies via YOUTUBE_COOKIES_BASE64 environment variable"
            )
        else:
            raise DownloadError(
                f"Download failed: {str(last_error)}",
                "DOWNLOAD_FAILED",
                "Check video URL or try a different video"
            )
    else:
        raise DownloadError(
            "All download attempts failed",
            "ALL_CLIENTS_FAILED",
            "Video may be incompatible or unavailable from your location"
        )


def get_video_info(url: str) -> Dict:
    """Get video info without downloading"""
    config = get_ydl_config(use_cookies=False, client='android')
    config['quiet'] = True
    config['no_warnings'] = True

    try:
        with yt_dlp.YoutubeDL(config) as ydl:
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
        raise DownloadError(
            f"Failed to get video info: {str(e)}",
            "INFO_FAILED",
            "Check video URL"
        )
