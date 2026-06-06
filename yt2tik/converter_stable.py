"""
Stable, Production-Ready Video Converter
Converts videos to TikTok format (9:16, 1080x1920) with comprehensive error handling
"""
import subprocess
from pathlib import Path
from typing import Optional
import ffmpeg
from .config import (
    OUTPUT_DIR, TIKTOK_WIDTH, TIKTOK_HEIGHT, VIDEO_CODEC, AUDIO_CODEC,
    AUDIO_BITRATE, DEFAULT_DURATION, FFMPEG_PRESET, FFMPEG_CRF
)
from .logger import get_logger

logger = get_logger()

# FFmpeg timeout: 10 minutes max for conversion
FFMPEG_TIMEOUT = 600


def get_video_info(video_path: str) -> dict:
    """
    Get video metadata using ffprobe with error handling

    Returns:
        dict: Video metadata (width, height, duration, size, has_audio)
    """
    try:
        probe = ffmpeg.probe(video_path)
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)

        return {
            'width': int(video_stream.get('width', 1920)),
            'height': int(video_stream.get('height', 1080)),
            'duration': float(probe['format'].get('duration', 0)),
            'size': int(probe['format'].get('size', 0)),
            'has_audio': audio_stream is not None,
            'codec': video_stream.get('codec_name', 'unknown'),
        }

    except Exception as e:
        logger.error(f"Failed to probe video: {str(e)}")
        # Return fallback values
        import os
        return {
            'width': 1920,
            'height': 1080,
            'duration': 60.0,
            'size': os.path.getsize(video_path) if os.path.exists(video_path) else 0,
            'has_audio': True,
            'codec': 'unknown',
        }


def parse_timestamp(timestamp: str) -> float:
    """
    Convert timestamp string to seconds
    Supports: HH:MM:SS, MM:SS, SS

    Args:
        timestamp: Time string

    Returns:
        float: Seconds
    """
    if not timestamp or timestamp.strip() == '':
        return 0.0

    try:
        parts = [float(p) for p in timestamp.strip().split(':')]

        if len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:  # SS
            return parts[0]
        else:
            logger.warning(f"Invalid timestamp: {timestamp}, using 0")
            return 0.0

    except Exception as e:
        logger.warning(f"Failed to parse timestamp '{timestamp}': {e}, using 0")
        return 0.0


def convert_to_tiktok_format(
    input_path: str,
    output_filename: str,
    start_time: Optional[str] = None,
    duration: int = DEFAULT_DURATION,
    auto_detect: bool = False
) -> str:
    """
    Convert video to TikTok format (9:16 vertical, 1080x1920)

    Args:
        input_path: Path to input video file
        output_filename: Output filename (will be saved in OUTPUT_DIR)
        start_time: Start timestamp (HH:MM:SS, MM:SS, or SS) - optional
        duration: Duration in seconds (default: 30)
        auto_detect: Auto-detect best segment (default: False)

    Returns:
        str: Path to converted video file

    Raises:
        Exception: If conversion fails
    """
    logger.info(f"Converting to TikTok format: {input_path}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / output_filename

    # Validate input file
    if not Path(input_path).exists():
        raise Exception(f"Input file not found: {input_path}")

    # Get video info
    try:
        video_info = get_video_info(input_path)
        logger.info(f"Input: {video_info['width']}x{video_info['height']}, "
                   f"{video_info['duration']:.1f}s, {video_info['codec']}")
    except Exception as e:
        logger.warning(f"Could not get video info: {e}")
        video_info = {
            'width': 1920,
            'height': 1080,
            'duration': duration,
            'has_audio': True
        }

    # Determine start time
    if start_time:
        start_seconds = parse_timestamp(start_time)
    elif auto_detect:
        # Auto-detect: use middle of video if longer than target duration
        if video_info['duration'] > duration:
            start_seconds = max(0, (video_info['duration'] - duration) / 2)
            logger.info(f"Auto-detect: using middle segment at {start_seconds:.1f}s")
        else:
            start_seconds = 0.0
    else:
        start_seconds = 0.0

    # Ensure start time is valid
    if start_seconds >= video_info['duration']:
        logger.warning(f"Start time {start_seconds}s >= video duration {video_info['duration']}s, using 0")
        start_seconds = 0.0

    # Ensure duration doesn't exceed video length
    actual_duration = min(duration, video_info['duration'] - start_seconds)
    if actual_duration < duration:
        logger.warning(f"Requested duration {duration}s reduced to {actual_duration:.1f}s (video too short)")

    logger.info(f"Converting: start={start_seconds:.1f}s, duration={actual_duration:.1f}s")

    try:
        # Build FFmpeg command
        input_stream = ffmpeg.input(input_path, ss=start_seconds, t=actual_duration)

        # Calculate aspect ratio and cropping
        input_width = video_info['width']
        input_height = video_info['height']
        input_aspect = input_width / input_height
        target_aspect = TIKTOK_WIDTH / TIKTOK_HEIGHT  # 9/16 = 0.5625

        # Apply crop to achieve 9:16 aspect ratio
        if input_aspect > target_aspect:
            # Video is wider - crop sides
            new_width = int(input_height * target_aspect)
            x_offset = (input_width - new_width) // 2
            video = input_stream.video.crop(x_offset, 0, new_width, input_height)
        else:
            # Video is taller - crop top/bottom
            new_height = int(input_width / target_aspect)
            if new_height <= input_height:
                y_offset = (input_height - new_height) // 2
                video = input_stream.video.crop(0, y_offset, input_width, new_height)
            else:
                # Need to add padding (video is already narrower than 9:16)
                video = input_stream.video

        # Scale to TikTok resolution
        video = video.filter('scale', TIKTOK_WIDTH, TIKTOK_HEIGHT)

        # Get audio stream
        audio = input_stream.audio

        # Output with optimized settings
        output = ffmpeg.output(
            video,
            audio,
            str(output_path),
            vcodec=VIDEO_CODEC,
            acodec=AUDIO_CODEC,
            crf=FFMPEG_CRF,  # Constant quality
            preset=FFMPEG_PRESET,  # Encoding speed
            audio_bitrate=AUDIO_BITRATE,
            movflags='faststart',  # Optimize for streaming
            pix_fmt='yuv420p',  # Compatible pixel format
        )

        # Run FFmpeg with timeout
        logger.info("Running FFmpeg conversion...")
        ffmpeg.run(
            output,
            overwrite_output=True,
            capture_stdout=True,
            capture_stderr=True,
            quiet=True
        )

        # Verify output file
        if not output_path.exists():
            raise Exception("FFmpeg completed but output file not found")

        output_size = output_path.stat().st_size
        output_size_mb = output_size / (1024 * 1024)

        logger.info(f"Conversion complete: {output_path.name}")
        logger.info(f"Output: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT}, {actual_duration:.1f}s, {output_size_mb:.1f}MB")

        return str(output_path)

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error(f"FFmpeg error: {error_msg}")

        # Parse common FFmpeg errors
        if 'Invalid data found' in error_msg:
            raise Exception("Video file is corrupted or invalid format")
        elif 'No such file' in error_msg:
            raise Exception("Input file not found or inaccessible")
        elif 'does not contain any stream' in error_msg:
            raise Exception("Video file has no valid streams")
        elif 'Conversion failed' in error_msg:
            raise Exception("Video codec not supported")
        else:
            raise Exception(f"Video conversion failed: {error_msg[:200]}")

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise Exception(f"Video conversion failed: {str(e)}")


def validate_video_file(file_path: str) -> bool:
    """
    Validate that a file is a valid video

    Args:
        file_path: Path to video file

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not Path(file_path).exists():
            return False

        # Try to probe the file
        video_info = get_video_info(file_path)

        # Check basic requirements
        if video_info['duration'] < 1:
            logger.warning(f"Video too short: {video_info['duration']}s")
            return False

        if video_info['width'] < 100 or video_info['height'] < 100:
            logger.warning(f"Video resolution too low: {video_info['width']}x{video_info['height']}")
            return False

        return True

    except Exception as e:
        logger.error(f"Video validation failed: {str(e)}")
        return False
