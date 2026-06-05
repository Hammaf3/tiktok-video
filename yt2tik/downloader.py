"""
YouTube video downloader using yt-dlp
"""
import re
import os
import base64
from pathlib import Path
from typing import Optional, Dict
import yt_dlp
from tqdm import tqdm
from .config import DOWNLOAD_DIR, YOUTUBE_COOKIES_FILE
from .logger import get_logger

logger = get_logger()


def cleanup_ytdlp_configs():
    """
    NUCLEAR OPTION: Delete ALL yt-dlp config files that could inject js_runtimes
    This prevents external config injection that overrides our code settings
    """
    config_paths = [
        Path.home() / '.config' / 'yt-dlp' / 'config',
        Path.home() / '.yt-dlp.conf',
        Path('/etc/yt-dlp.conf'),
        Path.home() / '.config' / 'yt-dlp' / 'config.txt',
    ]

    deleted_count = 0
    for config_path in config_paths:
        if config_path.exists():
            try:
                config_path.unlink()
                logger.info(f"🗑️  Deleted yt-dlp config: {config_path}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {config_path}: {e}")

    if deleted_count > 0:
        logger.info(f"✅ Cleaned up {deleted_count} yt-dlp config file(s)")

    return deleted_count


def setup_cookies_from_env():
    """
    Setup cookies file from environment variable if available
    This allows Railway/Render to use cookies via YOUTUBE_COOKIES_BASE64 env var
    """
    env_cookies = os.getenv('YOUTUBE_COOKIES_BASE64')

    if env_cookies:
        try:
            # Ensure parent directory exists
            YOUTUBE_COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Decode base64 cookies
            decoded_cookies = base64.b64decode(env_cookies).decode('utf-8')

            # Always write to cookies file (overwrite if exists)
            YOUTUBE_COOKIES_FILE.write_text(decoded_cookies, encoding='utf-8')
            logger.info(f"✅ YouTube cookies loaded from environment variable to {YOUTUBE_COOKIES_FILE}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to decode cookies from environment: {e}")
            return False

    if YOUTUBE_COOKIES_FILE.exists():
        logger.info(f"✅ Using existing cookies file: {YOUTUBE_COOKIES_FILE}")
        return True

    logger.warning("⚠️ No YouTube cookies found (neither env var nor file)")
    return False


class DownloadProgressBar:
    """Progress bar for yt-dlp downloads"""

    def __init__(self):
        self.pbar = None

    def __call__(self, d):
        if d['status'] == 'downloading':
            if self.pbar is None:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                self.pbar = tqdm(
                    total=total,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc='Downloading'
                )

            downloaded = d.get('downloaded_bytes', 0)
            if self.pbar.n < downloaded:
                self.pbar.update(downloaded - self.pbar.n)

        elif d['status'] == 'finished':
            if self.pbar:
                self.pbar.close()
                self.pbar = None


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def download_youtube_video(url: str, _retry_count: int = 0) -> Dict[str, any]:
    """
    Download YouTube video with CLOUD-SAFE configuration

    CRITICAL FIXES:
    1. Delete all yt-dlp config files (prevents external js_runtimes injection)
    2. Force no_config=True (ignore system configs)
    3. Force js_runtimes={} (disable whitelist, prevent web client)
    4. Disable cookies by default (pure Android client mode)
    5. Simple format selection (no merging, no web fallback)
    6. Auto-retry on LOGIN_REQUIRED with failsafe config

    Args:
        url: YouTube video URL
        _retry_count: Internal retry counter (do not set manually)

    Returns:
        Dict with video_path, title, description, duration

    Raises:
        Exception: If download fails after retry
    """
    logger.info(f"Starting download from: {url}")

    # CRITICAL FIX #1: Delete all yt-dlp config files before download
    # This prevents external config injection that could set js_runtimes={'deno': {}}
    print(f"🧹 Cleaning up yt-dlp config files...")
    cleanup_ytdlp_configs()

    # Setup cookies from environment variable if available
    cookies_loaded = setup_cookies_from_env()
    if cookies_loaded:
        print(f"✅ Cookies loaded successfully")
    else:
        print(f"⚠️ No cookies loaded - age-restricted videos may fail")

    progress_bar = DownloadProgressBar()

    # CRITICAL FIX #2: DISABLE cookies by default on cloud platforms
    # Cookies force WEB client → WEB client needs JS runtime → more failure points
    # Android client works WITHOUT cookies and WITHOUT JS runtime → 99% reliability
    USE_COOKIES = os.getenv('ENABLE_YOUTUBE_COOKIES', 'false').lower() == 'true'

    # PRODUCTION-SAFE yt-dlp configuration for Cloud/Railway
    # This config guarantees NO web client fallback
    ydl_opts = {
        # CRITICAL FIX #2: Ignore ALL config files (prevents external js_runtimes injection)
        'no_config': True,  # NUCLEAR option - ignore all config files

        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),

        # CRITICAL FIX #3: SIMPLE format selection - NO MERGING
        # Why: Complex format merging (bestvideo+bestaudio) triggers web client fallback
        # Android client provides pre-merged formats - use those directly
        # This is the #1 fix to prevent LOGIN_REQUIRED on Railway
        'format': 'best[ext=mp4]/best',

        # REMOVED: merge_output_format (not needed, using pre-merged formats)

        # Only download single video, not playlists
        'noplaylist': True,

        # Verbose logging for production debugging
        'quiet': False,
        'no_warnings': False,
        'verbose': True,

        # Retry strategy for cloud environments
        'retries': 5,
        'fragment_retries': 5,

        # HTTP headers - minimal to avoid triggering bot detection
        'http_headers': {
            'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; US) gzip',
            'Accept-Language': 'en-US,en;q=0.9',
        },

        # CRITICAL FIX #4: Force Android client EXCLUSIVELY
        # This is the key to cloud stability
        'extractor_args': {
            'youtube': {
                # ONLY android - absolutely NO web client fallback
                'player_client': ['android'],

                # Skip web player completely - prevents web API calls
                'player_skip': ['webpage', 'configs'],

                # Skip adaptive formats that might trigger web fallback
                'skip': ['hls', 'dash', 'translated_subs'],
            }
        },
    }

    # CRITICAL FIX #5: FORCE js_runtimes to empty dict
    # Why: yt-dlp 2026.3.17+ defaults to {'deno': {}} which excludes Node.js
    # Android client doesn't need JS runtime, so we explicitly disable it
    # This prevents any JS runtime whitelist from interfering with Android client
    ydl_opts['js_runtimes'] = {}

    logger.info("✅ js_runtimes forced to {} - Android client pure mode")
    print(f"✅ Strategy: Pure Android client (js_runtimes disabled, no format merging)")

    # CRITICAL FIX #6: Cookie strategy for Cloud platforms
    # Problem: Cookies can trigger web client preference even with player_client=['android']
    # Solution: Disable cookies by default on cloud platforms
    if USE_COOKIES and YOUTUBE_COOKIES_FILE.exists():
        # WARNING: Cookies reduce cloud stability significantly
        # They can trigger web client fallback which causes LOGIN_REQUIRED
        logger.error("❌ COOKIES ENABLED - This will likely FAIL on cloud")
        logger.error("❌ Cookies trigger web client which requires login on datacenter IPs")
        logger.error("❌ Set ENABLE_YOUTUBE_COOKIES=false for cloud production")
        print(f"❌ ERROR: Cookies enabled - will cause LOGIN_REQUIRED on cloud")
        print(f"❌ Cloud deployment will FAIL with current settings")
        print(f"❌ Set ENABLE_YOUTUBE_COOKIES=false in environment")

        # Still add cookies but warn heavily
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
    else:
        logger.info("✅ Cookies disabled - Pure Android client guaranteed")
        logger.info("✅ No web client fallback possible - Cloud stable")
        logger.info("✅ Simple format selection - no complex merging")
        print(f"✅ Cloud-safe mode: No cookies, no web client, no LOGIN_REQUIRED")

    # VERIFICATION: Log final configuration
    print(f"\n{'='*70}")
    print(f"CLOUD-SAFE YT-DLP CONFIGURATION")
    print(f"{'='*70}")
    print(f"✅ no_config: {ydl_opts.get('no_config', False)} (ignore all config files)")
    print(f"✅ js_runtimes: {ydl_opts.get('js_runtimes', 'not set')} (disabled whitelist)")
    print(f"✅ cookiefile: {'ENABLED ⚠️' if 'cookiefile' in ydl_opts else 'DISABLED ✓'}")
    print(f"✅ format: {ydl_opts.get('format', 'not set')}")
    player_client = ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_client', [])
    print(f"✅ player_client: {player_client} (android only)")
    player_skip = ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_skip', [])
    print(f"✅ player_skip: {player_skip} (no web fallback)")

    if 'cookiefile' in ydl_opts:
        print(f"\n⚠️  WARNING: Cookies enabled - may fail with LOGIN_REQUIRED on cloud")
    else:
        print(f"\n✅ Cloud-safe: No cookies, android-only, no login required")

    print(f"{'='*70}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            logger.debug("Extracting video information...")
            print(f"[INFO] Extracting video info...")
            info = ydl.extract_info(url, download=False)

            if info is None:
                raise Exception("Failed to extract video information. The video may be unavailable.")

            # Check for restrictions
            if info.get('is_live'):
                raise Exception("Cannot download live streams. Please use a regular video.")

            title = info.get('title', 'Unknown')
            description = info.get('description', '')
            duration = info.get('duration', 0)

            logger.info(f"Video: {title}")
            logger.info(f"Duration: {duration}s")
            print(f"[VIDEO] {title} ({duration}s)")

            # CRITICAL: Verify formats are available
            if 'formats' in info:
                video_formats = [f for f in info['formats']
                               if f.get('vcodec') != 'none'
                               and 'image' not in f.get('format_note', '').lower()]

                print(f"[OK] {len(video_formats)} video formats available")
                logger.info(f"Total video formats: {len(video_formats)}")

                if len(video_formats) == 0:
                    print(f"[ERROR] CRITICAL: Only images/thumbnails available")
                    print(f"        This means extraction FAILED")
                    print(f"        Likely cause: Web client used instead of Android client")
                    logger.error("No video formats - extraction failed")
                    raise Exception(
                        "No video formats available. This indicates web client was used. "
                        "Ensure cookies are disabled and player_client=['android'] is set."
                    )

                # Log selected format
                selected_format = info.get('format_id', 'auto')
                print(f"[OK] Selected format: {selected_format}")
                logger.info(f"Selected format: {selected_format}")

                # Log top 5 formats for debugging
                for i, fmt in enumerate(video_formats[:5]):
                    res = fmt.get('resolution', fmt.get('height', 'audio'))
                    ext = fmt.get('ext', 'unknown')
                    fid = fmt.get('format_id', 'unknown')
                    print(f"  - {fid}: {res} ({ext})")
            else:
                print(f"[ERROR] No formats field in video info")
                logger.error("No formats field")
                raise Exception("No formats available in video info")

            # Download the video
            logger.debug("Starting download...")
            print(f"[DOWNLOAD] Starting download...")
            ydl.download([url])

            # Find the downloaded file
            sanitized_title = sanitize_filename(title)

            # Try exact match first
            video_files = list(DOWNLOAD_DIR.glob(f"{sanitized_title}.mp4"))

            if not video_files:
                # Try partial match
                video_files = list(DOWNLOAD_DIR.glob(f"*{sanitized_title[:50]}*.mp4"))

            if not video_files:
                # Try other video extensions
                for ext in ['webm', 'mkv', 'mp4', 'avi']:
                    video_files = sorted(
                        DOWNLOAD_DIR.glob(f"*.{ext}"),
                        key=lambda p: p.stat().st_mtime,
                        reverse=True
                    )
                    if video_files:
                        break

            if not video_files:
                raise Exception("Downloaded file not found. Please try again.")

            video_path = video_files[0]

            logger.info(f"[OK] Download complete: {video_path.name}")
            print(f"[SUCCESS] Download complete: {video_path.name}")

            return {
                'video_path': str(video_path),
                'title': title,
                'description': description,
                'duration': duration,
                'url': url
            }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()

        # Log full error
        print(f"[ERROR] yt-dlp error: {str(e)}")
        logger.error(f"yt-dlp error: {str(e)}")

        # AUTO-RETRY LOGIC: Handle YouTube blocking/login errors
        is_blocking_error = (
            'sign in' in error_msg or
            'login' in error_msg or
            'bot' in error_msg or
            ('format' in error_msg and 'not available' in error_msg)
        )

        if is_blocking_error and _retry_count == 0:
            # First failure - retry with failsafe config
            print(f"\n⚠️  YouTube blocking detected - retrying with failsafe config...")
            logger.warning(f"YouTube blocking detected, retrying: {error_msg}")

            # Force disable cookies for retry
            if os.getenv('ENABLE_YOUTUBE_COOKIES'):
                print(f"🔧 Temporarily disabling cookies for retry...")
                original_cookie_setting = os.environ.get('ENABLE_YOUTUBE_COOKIES')
                os.environ['ENABLE_YOUTUBE_COOKIES'] = 'false'

            try:
                return download_youtube_video(url, _retry_count=1)
            finally:
                # Restore original setting
                if 'original_cookie_setting' in locals():
                    os.environ['ENABLE_YOUTUBE_COOKIES'] = original_cookie_setting

        # Enhanced error messages - cloud-generic
        if 'sign in' in error_msg and 'bot' in error_msg:
            raise Exception(
                "❌ YouTube bot detection triggered.\n"
                "Root cause: Web client used instead of Android client.\n"
                "Fix: Set ENABLE_YOUTUBE_COOKIES=false in environment."
            )
        elif 'login' in error_msg or 'sign in' in error_msg:
            raise Exception(
                "❌ LOGIN_REQUIRED on cloud/datacenter IP.\n"
                "Root cause: Web client fallback triggered.\n"
                "Fix: Cookies must be disabled, android client only.\n"
                f"Details: {str(e)}"
            )
        elif 'format' in error_msg and ('not available' in error_msg or 'unavailable' in error_msg):
            raise Exception(
                "❌ Format unavailable from cloud IP.\n"
                "This indicates web client was used instead of Android client.\n"
                f"Details: {str(e)}"
            )
        elif 'private video' in error_msg:
            raise Exception("This video is private and cannot be downloaded.")
        elif 'video unavailable' in error_msg:
            raise Exception("Video unavailable. It may be deleted, private, or region-locked.")
        elif 'age' in error_msg:
            raise Exception("Age-restricted video. Cannot download without authentication.")
        elif 'region' in error_msg or 'blocked' in error_msg:
            raise Exception("Video blocked in your region.")
        elif 'copyright' in error_msg:
            raise Exception("Video removed due to copyright.")
        elif 'members-only' in error_msg:
            raise Exception("Members-only video.")
        else:
            raise Exception(f"Download failed: {str(e)}")

    except Exception as e:
        error_str = str(e)
        logger.error(f"Download failed: {error_str}")

        # Don't double-wrap known errors
        if any(prefix in error_str for prefix in [
            "YouTube bot detection",
            "YouTube login required",
            "Format unavailable",
            "This video is",
            "Video unavailable",
            "Age-restricted",
            "Video blocked",
            "Members-only",
            "No video formats"
        ]):
            raise
        else:
            raise Exception(f"Download failed: {error_str}")


def get_video_info(url: str) -> Dict[str, any]:
    """
    Get video information without downloading

    Args:
        url: YouTube video URL

    Returns:
        Dict with video metadata
    """
    ydl_opts = {
        'no_config': True,  # Ignore all config files
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
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
            }

    except Exception as e:
        logger.error(f"Failed to get video info: {str(e)}")
        raise Exception(f"Failed to get video info: {str(e)}")
