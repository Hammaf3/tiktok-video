"""
Configuration constants for yt2tik
"""
import os
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
DOWNLOAD_DIR = BASE_DIR / "tmp" / "yt2tik" / "downloads"
OUTPUT_DIR = BASE_DIR / "tmp" / "yt2tik" / "output"
LOG_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# TikTok API Configuration
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
TIKTOK_UPLOAD_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
TIKTOK_MAX_FILE_SIZE = 72 * 1024 * 1024  # 72MB max
TIKTOK_MAX_CAPTION_LENGTH = 2200
TIKTOK_MAX_DURATION = 60  # seconds

# Video Processing
DEFAULT_DURATION = 30  # seconds
TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920
TIKTOK_ASPECT_RATIO = "9:16"
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
VIDEO_BITRATE = "1500k"  # Optimized for speed and quality balance
AUDIO_BITRATE = "128k"
FFMPEG_PRESET = "ultrafast"  # Maximum speed preset
FFMPEG_CRF = "23"  # Constant Rate Factor for quality (18-28, lower=better)

# YouTube Download
YOUTUBE_PREFERRED_QUALITY = "1080p"
YOUTUBE_FALLBACK_QUALITY = "720p"
YOUTUBE_COOKIES_FILE = BASE_DIR / "youtube_cookies.txt"  # Optional: for age-restricted videos

# Default hashtags
DEFAULT_HASHTAGS = ["#fyp", "#foryoupage", "#viral"]

# Privacy settings
PRIVACY_OPTIONS = {
    "public": "PUBLIC_TO_EVERYONE",
    "friends": "MUTUAL_FOLLOW_FRIENDS",
    "private": "SELF_ONLY"
}

# Polling settings
UPLOAD_STATUS_POLL_INTERVAL = 10  # seconds
UPLOAD_STATUS_MAX_ATTEMPTS = 60  # 10 minutes max
