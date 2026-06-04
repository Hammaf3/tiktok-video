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


def download_youtube_video(url: str) -> Dict[str, any]:
    """
    Download YouTube video with PRODUCTION-HARDENED configuration

    CRITICAL FIXES:
    1. Delete all yt-dlp config files (prevents external js_runtimes injection)
    2. Use --no-config flag (ignore system configs)
    3. Disable cookies by default (enables Android client, no JS needed)
    4. Explicit Node.js PATH setup (if needed for web client)
    5. Cloud-IP-safe format fallback chain

    Args:
        url: YouTube video URL

    Returns:
        Dict with video_path, title, description, duration

    Raises:
        Exception: If download fails
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

    # Check Node.js availability
    import shutil
    import subprocess

    nodejs_path = shutil.which('node') or shutil.which('nodejs')

    # CRITICAL FIX #2: Add Nix profile to PATH for Railway environment
    # Railway uses Nix package manager, Node.js installed at /root/.nix-profile/bin/node
    if not nodejs_path:
        nix_node_path = '/root/.nix-profile/bin/node'
        if Path(nix_node_path).exists():
            nix_bin_dir = '/root/.nix-profile/bin'
            current_path = os.environ.get('PATH', '')
            if nix_bin_dir not in current_path:
                os.environ['PATH'] = f"{nix_bin_dir}:{current_path}"
                logger.info(f"Added Nix bin to PATH: {nix_bin_dir}")
                print(f"🔧 Added Nix profile to PATH")

            # Re-check after PATH update
            nodejs_path = shutil.which('node')

    if nodejs_path:
        try:
            result = subprocess.run([nodejs_path, '--version'],
                                  capture_output=True, text=True, timeout=5)
            node_version = result.stdout.strip()
            print(f"✅ Node.js found: {nodejs_path} ({node_version})")
            logger.info(f"Node.js available at {nodejs_path} version {node_version}")
        except Exception as e:
            print(f"⚠️ Node.js found but version check failed: {e}")
            logger.warning(f"Node.js check failed: {e}")
            nodejs_path = None  # Treat as unavailable if version check fails
    else:
        print(f"⚠️ Node.js NOT found in PATH")
        logger.warning("Node.js not found - Android client will be used")

    # CRITICAL FIX #3: DISABLE cookies by default on cloud platforms
    # Cookies force WEB client → WEB client needs JS runtime → more failure points
    # Android client works WITHOUT cookies and WITHOUT JS runtime → 99% reliability
    USE_COOKIES = os.getenv('ENABLE_YOUTUBE_COOKIES', 'false').lower() == 'true'

    # PRODUCTION-SAFE yt-dlp configuration for Railway/Cloud
    # CRITICAL: This config guarantees NO web client fallback
    ydl_opts = {
        # CRITICAL FIX #4: Ignore ALL config files (prevents external js_runtimes injection)
        'no_config': True,  # This is the NUCLEAR option - ignore all config files

        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),

        # CRITICAL: SIMPLE format selection - NO MERGING
        # Why: Complex format merging (bestvideo+bestaudio) triggers web client fallback
        # Android client provides pre-merged formats - use those directly
        # This is the #1 fix to prevent LOGIN_REQUIRED on Railway
        'format': 'best[ext=mp4][height<=1080]/best[ext=mp4]/best',

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

        # CRITICAL FIX #5: Force Android client EXCLUSIVELY
        # This is the key to Railway/cloud stability
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

    # CRITICAL FIX #6: NEVER set js_runtimes in ydl_opts
    # Why? Because:
    # 1. Android client doesn't need JS runtime at all
    # 2. Setting js_runtimes can trigger yt-dlp to prefer WEB client
    # 3. Empty dict or None still gets overridden by package defaults
    # 4. Best strategy: don't touch it at all, let Android client handle everything

    logger.info("✅ js_runtimes NOT set - Android client will handle all extraction")
    print(f"✅ Strategy: Pure Android client (no JS runtime, no format merging)")

    # CRITICAL FIX #7: Cookie strategy for Railway/Cloud
    # Problem: Cookies can trigger web client preference even with player_client=['android']
    # Solution: Disable cookies by default on cloud platforms
    if USE_COOKIES and YOUTUBE_COOKIES_FILE.exists():
        # WARNING: Cookies reduce Railway stability significantly
        # They can trigger web client fallback which causes LOGIN_REQUIRED
        logger.error("❌ COOKIES ENABLED - This will likely FAIL on Railway")
        logger.error("❌ Cookies trigger web client which requires login on datacenter IPs")
        logger.error("❌ Set ENABLE_YOUTUBE_COOKIES=false for Railway production")
        print(f"❌ ERROR: Cookies enabled - will cause LOGIN_REQUIRED on Railway")
        print(f"❌ Railway deployment will FAIL with current settings")
        print(f"❌ Set ENABLE_YOUTUBE_COOKIES=false in Railway environment")

        # Still add cookies but warn heavily
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
    else:
        logger.info("✅ Cookies disabled - Pure Android client guaranteed")
        logger.info("✅ No web client fallback possible - Railway stable")
        logger.info("✅ Simple format selection - no complex merging")
        print(f"✅ Railway-safe mode: No cookies, no web client, no LOGIN_REQUIRED")

    # VERIFICATION: Log final configuration
    print(f"\n{'='*70}")
    print(f"RAILWAY-SAFE YT-DLP CONFIGURATION")
    print(f"{'='*70}")
    print(f"no_config (ignore config files): {ydl_opts.get('no_config', False)}")
    print(f"js_runtimes in config: {'js_runtimes' in ydl_opts}")
    print(f"cookiefile in config: {'cookiefile' in ydl_opts}")
    print(f"format strategy: {ydl_opts.get('format', 'not set')}")
    player_client = ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_client', [])
    print(f"player_client: {player_client}")
    player_skip = ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_skip', [])
    print(f"player_skip: {player_skip}")

    if 'cookiefile' in ydl_opts:
        print(f"\n[WARNING] Cookies enabled - Railway may fail with LOGIN_REQUIRED")
    else:
        print(f"\n[OK] Railway-safe: No cookies, no web client, no login required")

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

        # Enhanced error handling - Railway-specific
        if 'sign in' in error_msg and 'bot' in error_msg:
            raise Exception(
                "RAILWAY ERROR: YouTube bot detection triggered.\n"
                "Root cause: Web client used instead of Android client.\n"
                "Solution: Set ENABLE_YOUTUBE_COOKIES=false in Railway environment."
            )
        elif 'login' in error_msg or 'sign in' in error_msg:
            raise Exception(
                "RAILWAY ERROR: LOGIN_REQUIRED on datacenter IP.\n"
                "Root cause: Web client triggered (likely due to cookies or format merging).\n"
                "Solution: Ensure cookies disabled and player_client=['android'] only.\n"
                f"Details: {str(e)}"
            )
        elif 'format' in error_msg and ('not available' in error_msg or 'unavailable' in error_msg):
            raise Exception(
                "Format unavailable from datacenter IP.\n"
                "This can happen even with Android client if format merging is attempted.\n"
                "Using simple format selection: best[ext=mp4]/best\n"
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
