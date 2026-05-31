"""
YouTube video downloader using yt-dlp
"""
import re
from pathlib import Path
from typing import Optional, Dict
import yt_dlp
from tqdm import tqdm
from .config import DOWNLOAD_DIR, YOUTUBE_PREFERRED_QUALITY, YOUTUBE_FALLBACK_QUALITY
from .logger import get_logger

logger = get_logger()


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

    progress_bar = DownloadProgressBar()

    # Enhanced yt-dlp options for better compatibility
    ydl_opts = {
        'format': 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'progress_hooks': [progress_bar],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'no_check_certificate': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_color': True,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'age_limit': None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        },
        'extractor_retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
        'keepvideo': False,
        'merge_output_format': 'mp4',
    }

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

        if 'private video' in error_msg:
            raise Exception("This video is private and cannot be downloaded.")
        elif 'video unavailable' in error_msg or 'not available' in error_msg:
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
