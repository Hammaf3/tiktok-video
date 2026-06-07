"""
Production Flask App - YouTube to TikTok Converter
Cloud-ready for Railway / Hugging Face Spaces
Zero-crash architecture with structured error handling
"""
from flask import Flask, request, jsonify, send_file
import os
import sys
import json
import uuid
import threading
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Import production modules
try:
    from yt2tik.downloader_production_v2 import download_youtube_video, cleanup_old_downloads
    from job_store import JobStore
    print("[INIT] ✓ Production downloader loaded (fallback chain)")
    print("[INIT] ✓ JobStore loaded (thread-safe)")
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    sys.exit(1)

# Import converter
try:
    from yt2tik.converter_stable import convert_to_tiktok_format
    print("[INIT] ✓ Converter loaded")
except ImportError:
    from yt2tik.converter import convert_to_tiktok_format
    print("[INIT] ⚠ Using fallback converter")

load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize job store (thread-safe, 10-minute TTL)
job_store = JobStore(ttl_seconds=600, max_jobs=1000)

print("[INIT] ✓ Directories created")
print("[INIT] ✓ Job store initialized (TTL: 10 minutes)")


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        'service': 'YouTube to TikTok Converter',
        'version': '2.0.0',
        'status': 'online',
        'endpoints': {
            '/health': 'GET - Health check',
            '/convert': 'POST - Start conversion',
            '/status/<job_id>': 'GET - Check job status',
            '/download/<filename>': 'GET - Download video'
        },
        'usage': {
            'convert': {
                'method': 'POST',
                'body': {
                    'youtube_url': 'https://youtube.com/watch?v=VIDEO_ID',
                    'start_time': '0:30 (optional)',
                    'duration': 30
                }
            }
        }
    })


@app.route('/health')
def health():
    """Health check for Railway/Hugging Face"""
    stats = job_store.get_stats()
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'jobs': stats,
        'disk': {
            'downloads': len(list(DOWNLOAD_DIR.glob('*'))),
            'outputs': len(list(OUTPUT_DIR.glob('*')))
        }
    })


@app.route('/convert', methods=['POST'])
def convert():
    """
    Start video conversion

    Request JSON:
    {
        "youtube_url": "https://youtube.com/watch?v=VIDEO_ID",
        "start_time": "0:30" (optional),
        "duration": 30 (optional, 5-180 seconds)
    }

    Returns:
    {
        "success": true,
        "job_id": "uuid",
        "status_url": "/status/<job_id>"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_REQUEST',
                'solution': 'Content-Type must be application/json'
            }), 400

        data = request.json
        youtube_url = data.get('youtube_url', '').strip()
        start_time = data.get('start_time', '').strip()
        duration = data.get('duration', 30)

        # Validate URL
        if not youtube_url:
            return jsonify({
                'status': 'error',
                'reason': 'MISSING_URL',
                'solution': 'youtube_url is required'
            }), 400

        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_URL',
                'solution': 'Must be a valid YouTube URL'
            }), 400

        # Validate duration
        try:
            duration = int(duration)
            if duration < 5 or duration > 180:
                return jsonify({
                    'status': 'error',
                    'reason': 'INVALID_DURATION',
                    'solution': 'Duration must be 5-180 seconds'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_DURATION',
                'solution': 'Duration must be a number'
            }), 400

        # Create job
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued')

        print(f"[JOB] Created: {job_id}")

        # Start processing in background
        thread = threading.Thread(
            target=process_video_safe,
            args=(job_id, youtube_url, start_time, duration),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'status_url': f'/status/{job_id}'
        }), 202

    except Exception as e:
        print(f"[ERROR] /convert: {str(e)}")
        return jsonify({
            'status': 'error',
            'reason': 'SERVER_ERROR',
            'solution': str(e)
        }), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """
    Get job status

    Returns:
    {
        "job_id": "uuid",
        "status": "processing|completed|error",
        "progress": 0-100,
        "message": "...",
        "video_url": "/download/file.mp4" (if completed)
    }
    """
    try:
        if not job_id:
            return jsonify({
                'status': 'error',
                'reason': 'MISSING_JOB_ID',
                'solution': 'job_id is required'
            }), 400

        job = job_store.get_job(job_id)

        if not job:
            return jsonify({
                'status': 'error',
                'reason': 'JOB_NOT_FOUND',
                'solution': 'Job expired (10 min TTL) or never existed',
                'job_id': job_id
            }), 404

        return jsonify(job), 200

    except Exception as e:
        print(f"[ERROR] /status: {str(e)}")
        return jsonify({
            'status': 'error',
            'reason': 'SERVER_ERROR',
            'solution': str(e)
        }), 500


@app.route('/download/<filename>')
def download(filename):
    """Download converted video"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_FILENAME',
                'solution': 'Invalid filename'
            }), 400

        if not filename.endswith('.mp4'):
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_FILE_TYPE',
                'solution': 'Only MP4 files allowed'
            }), 400

        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            return jsonify({
                'status': 'error',
                'reason': 'FILE_NOT_FOUND',
                'solution': 'File not found or expired'
            }), 404

        # Security: verify file is in OUTPUT_DIR
        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            return jsonify({
                'status': 'error',
                'reason': 'ACCESS_DENIED',
                'solution': 'Access denied'
            }), 403

        return send_file(file_path, mimetype='video/mp4', as_attachment=True)

    except Exception as e:
        print(f"[ERROR] /download: {str(e)}")
        return jsonify({
            'status': 'error',
            'reason': 'SERVER_ERROR',
            'solution': str(e)
        }), 500


# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

def process_video_safe(job_id: str, youtube_url: str, start_time: str, duration: int):
    """Safe wrapper - never crashes"""
    try:
        process_video(job_id, youtube_url, start_time, duration)
    except Exception as e:
        print(f"[FATAL] Job {job_id}: {str(e)}")
        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        # Parse structured error if available
        try:
            error_data = json.loads(str(e))
            reason = error_data.get('reason', 'UNKNOWN_ERROR')
            solution = error_data.get('solution', str(e))
        except:
            reason = 'UNKNOWN_ERROR'
            solution = str(e)

        job_store.update_job(
            job_id,
            status='error',
            progress=0,
            message=f'{reason}: {solution}',
            reason=reason,
            solution=solution
        )


def process_video(job_id: str, youtube_url: str, start_time: str, duration: int):
    """Process video with structured error handling"""

    def update(status, progress, message, **kwargs):
        job_store.update_job(job_id, status=status, progress=progress, message=message, **kwargs)
        print(f"[{job_id[:8]}] {progress}% - {message}")

    video_path = None

    try:
        update('processing', 5, 'Starting download...')

        # STEP 1: Download
        try:
            update('processing', 10, 'Downloading from YouTube...')
            print(f"[DOWNLOAD] URL: {youtube_url}")

            video_data = download_youtube_video(youtube_url, use_cookies=None, max_retries=3)

            video_path = video_data['video_path']
            video_title = video_data['title']
            file_size = video_data['file_size_mb']

            update('processing', 40, f'Downloaded: {video_title[:50]}')
            print(f"[SUCCESS] Downloaded: {file_size:.1f}MB")

        except Exception as e:
            error_str = str(e)

            # Parse structured error
            try:
                error_data = json.loads(error_str)
                reason = error_data.get('reason', 'DOWNLOAD_FAILED')
                solution = error_data.get('solution', error_str)

                update('error', 0, f'{reason}: {solution}', reason=reason, solution=solution)
                print(f"[ERROR] Download: {reason}")
                return

            except json.JSONDecodeError:
                # Fallback for non-JSON errors
                update('error', 0, f'Download failed: {error_str}')
                print(f"[ERROR] Download: {error_str}")
                return

        # STEP 2: Convert
        try:
            update('processing', 50, 'Converting to TikTok format...')

            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            print(f"[CONVERT] Output: {output_filename}")

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time if start_time else None,
                duration=duration,
                auto_detect=False
            )

            if not Path(converted_path).exists():
                raise Exception("Conversion completed but file not found")

            output_size = Path(converted_path).stat().st_size / (1024 * 1024)

            update('processing', 95, 'Finalizing...')
            print(f"[SUCCESS] Converted: {output_size:.1f}MB")

        except Exception as e:
            update('error', 0, f'Conversion failed: {str(e)}', reason='CONVERSION_FAILED')
            print(f"[ERROR] Conversion: {str(e)}")
            return

        # STEP 3: Success
        update(
            'completed',
            100,
            'Conversion complete!',
            video_title=video_title,
            filename=output_filename,
            video_url=f'/download/{output_filename}',
            file_size_mb=round(output_size, 1),
            duration=duration
        )
        print(f"[COMPLETE] Job {job_id}")

    except Exception as e:
        update('error', 0, f'Unexpected error: {str(e)}', reason='UNEXPECTED_ERROR')
        print(f"[ERROR] Unexpected: {str(e)}")

    finally:
        # Cleanup source video
        if video_path and Path(video_path).exists():
            try:
                Path(video_path).unlink()
                print(f"[CLEANUP] Deleted: {video_path}")
            except Exception as e:
                print(f"[CLEANUP] Failed: {e}")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'reason': 'NOT_FOUND',
        'solution': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'reason': 'SERVER_ERROR',
        'solution': 'Internal server error'
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    print(f"[ERROR] Unhandled: {str(e)}")
    return jsonify({
        'status': 'error',
        'reason': 'UNEXPECTED_ERROR',
        'solution': str(e)
    }), 500


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    try:
        # Cleanup old files
        cleanup_old_downloads(days=1)
        print("[INIT] ✓ Cleaned up old downloads")
    except Exception as e:
        print(f"[INIT] ⚠ Cleanup failed: {e}")

    # Port for Railway (8080) or Hugging Face (7860)
    port = int(os.getenv('PORT', os.getenv('SERVER_PORT', 7860)))

    print("\n" + "=" * 60)
    print("YouTube to TikTok Converter - Production v2.0")
    print("=" * 60)
    print(f"Server: http://0.0.0.0:{port}")
    print("Features:")
    print("  ✓ Fallback chain (android → web → ios)")
    print("  ✓ Cookie support (auto-detect)")
    print("  ✓ Thread-safe job store (10 min TTL)")
    print("  ✓ Structured JSON errors")
    print("  ✓ Zero-crash architecture")
    print("=" * 60 + "\n")

    # Run app
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
