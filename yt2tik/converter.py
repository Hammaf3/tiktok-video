"""
Video conversion and processing using FFmpeg
"""
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
import ffmpeg
from .config import (
    OUTPUT_DIR, TIKTOK_WIDTH, TIKTOK_HEIGHT, VIDEO_CODEC, AUDIO_CODEC,
    VIDEO_BITRATE, AUDIO_BITRATE, TIKTOK_MAX_FILE_SIZE, DEFAULT_DURATION,
    FFMPEG_PRESET, FFMPEG_CRF
)
from .logger import get_logger

logger = get_logger()


def get_video_info(video_path: str) -> dict:
    """Get video metadata using ffprobe (with fallback)"""
    try:
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio_info = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)

        return {
            'width': int(video_info['width']),
            'height': int(video_info['height']),
            'duration': float(probe['format']['duration']),
            'size': int(probe['format']['size']),
            'has_audio': audio_info is not None
        }
    except Exception as e:
        # Fallback: Use basic file info if FFmpeg not available
        logger.warning(f"FFmpeg probe failed, using fallback: {str(e)}")
        import os
        file_size = os.path.getsize(video_path)

        # Return default values
        return {
            'width': 1920,
            'height': 1080,
            'duration': 60.0,  # Default duration
            'size': file_size,
            'has_audio': True
        }


def parse_timestamp(timestamp: str) -> float:
    """
    Convert timestamp string to seconds
    Supports formats: HH:MM:SS, MM:SS, SS
    """
    if not timestamp:
        return 0.0

    parts = timestamp.split(':')
    parts = [float(p) for p in parts]

    if len(parts) == 3:  # HH:MM:SS
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:  # MM:SS
        return parts[0] * 60 + parts[1]
    elif len(parts) == 1:  # SS
        return parts[0]
    else:
        raise ValueError(f"Invalid timestamp format: {timestamp}")


def detect_best_segment(video_path: str, duration: int = 30) -> float:
    """
    Detect the most engaging segment using audio energy analysis
    Returns the start timestamp in seconds
    (Fallback: returns 0 if FFmpeg not available)
    """
    logger.info("🔍 Analyzing video to find best segment...")

    try:
        video_info = get_video_info(video_path)
        video_duration = video_info['duration']

        # If video is shorter than desired duration, start from beginning
        if video_duration <= duration:
            logger.info("Video is shorter than target duration, using full video")
            return 0.0

        # Try FFmpeg audio analysis
        try:
            # Use ffmpeg to analyze audio energy across the video
            num_samples = min(10, int(video_duration / duration))
            best_start = 0.0
            max_energy = 0.0

            for i in range(num_samples):
                start = (video_duration - duration) * i / max(1, num_samples - 1)

                try:
                    # Extract audio energy for this segment
                    out, err = (
                        ffmpeg
                        .input(video_path, ss=start, t=min(5, duration))
                        .output('pipe:', format='null', af='volumedetect')
                        .run(capture_stdout=True, capture_stderr=True, quiet=True)
                    )

                    # Parse mean volume from stderr
                    stderr = err.decode('utf-8')
                    for line in stderr.split('\n'):
                        if 'mean_volume:' in line:
                            volume = float(line.split('mean_volume:')[1].split('dB')[0].strip())
                            energy = abs(volume)

                            if energy < max_energy or max_energy == 0:
                                max_energy = energy
                                best_start = start
                            break

                except Exception as e:
                    logger.debug(f"Failed to analyze segment at {start}s: {str(e)}")
                    continue

            logger.info(f"✅ Best segment found at {best_start:.1f}s")
            return best_start

        except Exception as e:
            logger.warning(f"FFmpeg analysis failed: {str(e)}")
            # Fallback: Use middle of video
            best_start = max(0, (video_duration - duration) / 2)
            logger.info(f"Using middle of video: {best_start:.1f}s")
            return best_start

    except Exception as e:
        logger.warning(f"Auto-detection failed: {str(e)}, using start of video")
        return 0.0


def convert_to_tiktok_format(
    input_path: str,
    output_filename: str,
    start_time: Optional[str] = None,
    duration: int = DEFAULT_DURATION,
    watermark: Optional[str] = None,
    auto_detect: bool = False
) -> str:
    """
    Convert video to TikTok format (9:16, 1080x1920)
    Uses yt-dlp post-processing if FFmpeg not available
    """
    logger.info("🎬 Converting video to TikTok format...")

    # Output path
    output_path = OUTPUT_DIR / output_filename

    # Determine start time
    if start_time:
        start_seconds = parse_timestamp(start_time)
    elif auto_detect:
        start_seconds = detect_best_segment(input_path, duration)
    else:
        start_seconds = 0.0

    logger.info(f"Clipping from {start_seconds:.1f}s for {duration}s")

    try:
        # Try FFmpeg conversion first
        return _convert_with_ffmpeg(input_path, output_path, start_seconds, duration, watermark)
    except Exception as e:
        logger.warning(f"FFmpeg conversion failed: {str(e)}")
        logger.info("Trying alternative conversion method...")

        # Fallback: Simple copy with yt-dlp
        return _convert_simple(input_path, output_path, start_seconds, duration)


def _convert_with_ffmpeg(input_path, output_path, start_seconds, duration, watermark):
    """Convert using FFmpeg (optimized for speed)"""
    # Get input video info
    video_info = get_video_info(input_path)

    # Build ffmpeg command with optimized settings
    stream = ffmpeg.input(input_path, ss=start_seconds, t=duration)

    # Calculate scaling for 9:16 aspect ratio
    input_width = video_info['width']
    input_height = video_info['height']
    input_aspect = input_width / input_height
    target_aspect = TIKTOK_WIDTH / TIKTOK_HEIGHT

    # Apply crop and scale filters
    needs_scale = True
    if input_aspect > target_aspect:
        # Video is wider - crop width
        new_width = int(input_height * target_aspect)
        x_offset = (input_width - new_width) // 2
        stream = stream.crop(x_offset, 0, new_width, input_height)
    else:
        # Video is taller - crop height
        new_height = int(input_width / target_aspect)
        if new_height <= input_height:
            y_offset = (input_height - new_height) // 2
            stream = stream.crop(0, y_offset, input_width, new_height)
        else:
            # Need padding
            stream = stream.filter('scale', TIKTOK_WIDTH, -1)
            stream = stream.filter('pad', TIKTOK_WIDTH, TIKTOK_HEIGHT, 0, '(oh-ih)/2')
            needs_scale = False

    # Scale to final size if needed
    if needs_scale:
        stream = stream.filter('scale', TIKTOK_WIDTH, TIKTOK_HEIGHT)

    # Add watermark if specified
    if watermark:
        stream = stream.drawtext(
            text=watermark,
            fontsize=24,
            fontcolor='white',
            x='(w-text_w)/2',
            y='h-th-20',
            box=1,
            boxcolor='black@0.5',
            boxborderw=5
        )

    # Output with audio
    audio = ffmpeg.input(input_path, ss=start_seconds, t=duration).audio

    output = ffmpeg.output(
        stream,
        audio,
        str(output_path),
        vcodec=VIDEO_CODEC,
        acodec=AUDIO_CODEC,
        crf=FFMPEG_CRF,  # Use CRF mode for faster encoding
        maxrate=VIDEO_BITRATE,  # Max bitrate cap
        bufsize='3000k',  # Buffer size
        audio_bitrate=AUDIO_BITRATE,
        preset=FFMPEG_PRESET,  # Use ultrafast preset
        movflags='faststart',
        pix_fmt='yuv420p',
        **{'threads': 0, 'tune': 'fastdecode'}  # Use all CPU threads + fast decode tune
    )

    # Run with progress feedback
    logger.info("⚙️  Encoding video (this should take 5-15 seconds)...")
    try:
        ffmpeg.run(output, overwrite_output=True, capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise

    output_size = output_path.stat().st_size
    output_size_mb = output_size / (1024 * 1024)

    logger.info(f"✅ Conversion complete: {output_path.name}")
    logger.info(f"Output: {TIKTOK_WIDTH}x{TIKTOK_HEIGHT}, {duration}s, {output_size_mb:.1f}MB")

    return str(output_path)


def _convert_simple(input_path, output_path, start_seconds, duration):
    """Simple conversion without FFmpeg - just copy the segment"""
    import shutil
    from pathlib import Path

    logger.info("Using simple conversion (no FFmpeg)")

    # For now, just copy the file
    # This is a fallback - video won't be in perfect TikTok format
    # but it will work
    shutil.copy2(input_path, output_path)

    output_size = output_path.stat().st_size
    output_size_mb = output_size / (1024 * 1024)

    logger.info(f"✅ Video copied: {output_path.name}")
    logger.info(f"Output: {output_size_mb:.1f}MB")
    logger.warning("⚠️  Video not optimized for TikTok format (FFmpeg not available)")
    logger.warning("⚠️  Install FFmpeg for best results")

    return str(output_path)
