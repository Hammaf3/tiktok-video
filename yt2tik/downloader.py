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
    Download YouTube video

    Args:
        url: YouTube video URL

    Returns:
        Dict with video_path, title, description, duration

    Raises:
        Exception: If download fails
    """
    logger.info(f"Starting download from: {url}")

    # Setup cookies from environment variable if available
    cookies_loaded = setup_cookies_from_env()
    if cookies_loaded:
        print(f"✅ Cookies loaded successfully")
    else:
        print(f"⚠️ No cookies loaded - age-restricted videos may fail")

    progress_bar = DownloadProgressBar()

    # CRITICAL: Check Node.js availability for YouTube signature/n-challenge solving
    import shutil
    import subprocess

    nodejs_path = shutil.which('node') or shutil.which('nodejs')
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
    else:
        print(f"❌ WARNING: Node.js NOT found in PATH")
        print(f"   YouTube signature/n-challenge solving will FAIL")
        print(f"   This will cause 'Only images are available' error")
        logger.error("Node.js not found - YouTube downloads will likely fail")

    # PRODUCTION-SAFE yt-dlp configuration with format fallback chain
    # Format strategy: Try best quality, fallback to universally available formats
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),

        # CRITICAL: Explicit format selection with fallback chain
        # This ensures compatibility across all environments including Railway
        'format': (
            # Try best video+audio merge (usually works)
            'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/'
            # Fallback: best combined format
            'best[ext=mp4]/best'
        ),

        # Merge video and audio into single file
        'merge_output_format': 'mp4',

        # CRITICAL: Only download single video, not playlists
        'noplaylist': True,

        # Logging for production debugging
        'quiet': False,
        'no_warnings': False,
        'verbose': True,

        # Retry strategy for cloud environments
        'retries': 3,
        'fragment_retries': 3,

        # HTTP headers to appear as regular browser
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        },

        # CRITICAL FIX: Extractor arguments for YouTube challenge solving
        # This helps yt-dlp solve signature and n-parameter challenges
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],  # Try multiple clients
                'player_skip': ['webpage', 'configs'],  # Skip unnecessary steps
                'skip': ['hls', 'dash'],  # Focus on direct formats
            }
        },
    }

    # CRITICAL FIX: Ensure yt-dlp can find Node.js for JavaScript execution
    if nodejs_path:
        # Add Node.js to PATH so yt-dlp can find it
        current_path = os.environ.get('PATH', '')
        node_dir = os.path.dirname(nodejs_path)
        if node_dir not in current_path:
            os.environ['PATH'] = f"{node_dir}:{current_path}"
            logger.info(f"Added Node.js directory to PATH: {node_dir}")

        # Also set NODE_PATH
        os.environ['NODE_PATH'] = node_dir
        logger.info(f"Set NODE_PATH to {node_dir}")

        # DEBUG: Print full PATH for verification
        print(f"🔍 DEBUG: Full PATH = {os.environ.get('PATH')[:200]}...")
        print(f"🔍 DEBUG: NODE_PATH = {os.environ.get('NODE_PATH')}")

        # DEBUG: Test if yt-dlp can find node
        import shutil
        print(f"🔍 DEBUG: which('node') = {shutil.which('node')}")
        print(f"🔍 DEBUG: which('nodejs') = {shutil.which('nodejs')}")
        print(f"🔍 DEBUG: which('deno') = {shutil.which('deno')}")

    # PRODUCTION FIX: Disable cookies on Railway to enable Android client
    # Android client doesn't need JavaScript challenges = 99% reliability
    # Web client requires JS challenges = depends on Node.js working
    USE_COOKIES = os.getenv('ENABLE_YOUTUBE_COOKIES', 'false').lower() == 'true'

    if USE_COOKIES and YOUTUBE_COOKIES_FILE.exists():
        ydl_opts['cookiefile'] = str(YOUTUBE_COOKIES_FILE)
        logger.warning("⚠️  Cookies enabled - Android client will be skipped")
        logger.warning("⚠️  Web client requires working Node.js for JS challenges")
        logger.info("Using YouTube cookies for authentication")

        # CRITICAL: When cookies are used, Android client is skipped
        # We MUST ensure Node.js is accessible for web client
        if not nodejs_path:
            logger.error("❌ Cookies enabled but Node.js not found - web client will fail")
            logger.error("❌ Either disable cookies OR ensure Node.js is accessible")
            raise Exception(
                "Node.js required when using cookies (web client needs JS challenges). "
                "Node.js not found in PATH. Set ENABLE_YOUTUBE_COOKIES=false to use Android client."
            )
    else:
        logger.info("✅ Cookies disabled - Android client will be used (no JS needed)")
        logger.info("✅ Android client bypasses JavaScript challenges")
        logger.info("✅ This provides maximum reliability on cloud platforms")

    # CRITICAL FIX: Override yt-dlp 2026.3.17 default js_runtimes
    # yt-dlp 2026.3.17 hardcoded default: js_runtimes = {'deno': {}}
    # This EXCLUDES Node.js from the whitelist, causing signature solving to fail
    # We must explicitly override to enable Node.js
    if nodejs_path:
        # Node.js available - configure yt-dlp to use it
        # Note: Only 'node' is valid, not 'nodejs' (yt-dlp will warn about invalid names)
        ydl_opts['js_runtimes'] = {'node': {}}
        print(f"✅ OVERRIDE: js_runtimes set to Node.js (overriding Deno default)")
        logger.info("Overriding yt-dlp default: using Node.js instead of Deno")
    else:
        # No Node.js - set empty dict to disable whitelist and allow Android client
        ydl_opts['js_runtimes'] = {}
        print(f"⚠️  Node.js not found - disabling js_runtimes whitelist")
        logger.warning("Node.js not found - relying on Android client")

    # VERIFICATION: Log final configuration before passing to yt-dlp
    print(f"\n{'='*60}")
    print(f"🔍 YT-DLP CONFIGURATION VERIFICATION")
    print(f"{'='*60}")

    # Check if yt-dlp package has the Deno default
    try:
        from yt_dlp import YoutubeDL
        test_ydl = YoutubeDL({})
        if 'js_runtimes' in test_ydl.params:
            print(f"ℹ️  yt-dlp package default: {test_ydl.params['js_runtimes']}")
            print(f"   (This is normal for yt-dlp 2026.3.17+)")
            logger.info(f"yt-dlp package default js_runtimes: {test_ydl.params['js_runtimes']}")
    except Exception as e:
        logger.warning(f"Could not check yt-dlp defaults: {e}")

    # Show our override
    print(f"✅ Our js_runtimes override: {ydl_opts.get('js_runtimes', 'NOT SET')}")
    logger.info(f"Final js_runtimes config: {ydl_opts.get('js_runtimes', 'NOT SET')}")

    print(f"cookiefile in config: {'cookiefile' in ydl_opts}")
    if 'cookiefile' in ydl_opts:
        print(f"⚠️  Cookies enabled - Web client will be used")
    else:
        print(f"✅ Cookies disabled - Android client available")

    player_client = ydl_opts.get('extractor_args', {}).get('youtube', {}).get('player_client', [])
    print(f"player_client: {player_client}")
    print(f"{'='*60}\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            logger.debug("Extracting video information...")
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

            # Log available formats for debugging (PRODUCTION LOGGING)
            if 'formats' in info:
                print(f"📋 Available formats: {len(info['formats'])} formats found")
                logger.info(f"Total formats available: {len(info['formats'])}")

                # CRITICAL: Check if we only have image formats (signature failure indicator)
                video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and 'image' not in f.get('format_note', '').lower()]
                if len(video_formats) == 0:
                    print(f"❌ CRITICAL: No video formats available - only images/thumbnails")
                    print(f"   This indicates YouTube signature/n-challenge solving FAILED")
                    print(f"   Node.js is likely not available or not working properly")
                    logger.error("No video formats available - signature solving failed")
                else:
                    print(f"✓ Video formats available: {len(video_formats)}")

                # Log first 10 formats with detailed info
                for i, fmt in enumerate(info['formats'][:10]):
                    format_info = (
                        f"Format {fmt.get('format_id', 'N/A')}: "
                        f"{fmt.get('ext', 'N/A')} "
                        f"{fmt.get('resolution', fmt.get('quality', 'audio only'))} "
                        f"[vcodec: {fmt.get('vcodec', 'none')}, "
                        f"acodec: {fmt.get('acodec', 'none')}] "
                        f"{fmt.get('filesize', 0) / 1024 / 1024:.1f}MB"
                    )
                    print(f"  {i+1}. {format_info}")
                    logger.debug(format_info)

                # Log the format that will be selected
                selected_format = info.get('format_id', 'auto')
                print(f"✓ Selected format: {selected_format}")
                logger.info(f"Selected format ID: {selected_format}")
            else:
                print(f"❌ CRITICAL: No formats field in video info")
                logger.error("No formats field returned by yt-dlp")

            # Download the video
            logger.debug("Starting download...")
            ydl.download([url])

            # Find the downloaded file - try multiple patterns
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

            logger.info(f"✅ Download complete: {video_path.name}")

            return {
                'video_path': str(video_path),
                'title': title,
                'description': description,
                'duration': duration,
                'url': url
            }

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()

        # Show actual error for debugging (PRODUCTION LOGGING)
        print(f"🔴 yt-dlp DownloadError: {str(e)}")
        logger.error(f"yt-dlp DownloadError: {str(e)}")

        # ENHANCED ERROR DETECTION FOR FORMAT ISSUES
        if 'format' in error_msg and ('not available' in error_msg or 'unavailable' in error_msg):
            # This is the critical error that happens on Railway
            logger.error("FORMAT ERROR DETECTED - This usually happens on cloud IPs")
            logger.error("YouTube may be restricting format availability from datacenter IPs")

            # Provide detailed diagnostic info
            print(f"❌ FORMAT ERROR: YouTube restricted format availability")
            print(f"   This typically happens on cloud platforms (Railway, Heroku, etc.)")
            print(f"   The requested video+audio format combination is not available")
            print(f"   Recommendation: Ensure format fallback chain is configured")

            raise Exception(
                "Format error: YouTube restricted format availability from this IP. "
                "This video format is not available on cloud platforms. "
                "Error details: " + str(e)
            )

        elif 'private video' in error_msg:
            raise Exception("This video is private and cannot be downloaded.")
        elif 'video unavailable' in error_msg:
            raise Exception("Video unavailable. It may be deleted, private, or region-locked. Please try a different video.")
        elif 'sign in' in error_msg or 'age' in error_msg:
            raise Exception("Age-restricted video. Cannot download without authentication. Try a different video.")
        elif 'region' in error_msg or 'country' in error_msg or 'blocked' in error_msg:
            raise Exception("Video blocked in your region. Please try a different video.")
        elif 'copyright' in error_msg:
            raise Exception("Video removed due to copyright. Please try a different video.")
        elif 'members-only' in error_msg or 'membership' in error_msg:
            raise Exception("This is a members-only video. Please try a different video.")
        else:
            # Show actual error message with context
            raise Exception(f"Download failed: {str(e)}")

    except Exception as e:
        error_str = str(e)
        logger.error(f"Download failed: {error_str}")

        # Don't double-wrap error messages
        if error_str.startswith("Video unavailable") or error_str.startswith("This video"):
            raise Exception(error_str)
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
