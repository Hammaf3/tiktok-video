"""
PRODUCTION YouTube to TikTok Converter
Railway/Hugging Face Ready - Zero-Crash Architecture
"""
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
import os
import sys
import threading
import uuid
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

# Fix Windows console encoding
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Import modules
try:
    from yt2tik.downloader_production import download_youtube_video, DownloadError
    from yt2tik.converter import convert_to_tiktok_format
    from yt2tik.caption_gen import generate_caption
    YT2TIK_AVAILABLE = True
    print("✅ Production downloader loaded (multi-client fallback)")
except ImportError as e:
    print(f"❌ yt2tik modules not available: {e}")
    YT2TIK_AVAILABLE = False

# Import JobStore
try:
    from job_store import JobStore
    print("✅ JobStore loaded (thread-safe)")
except ImportError:
    print("⚠️  JobStore not found")
    # Fallback implementation
    class JobStore:
        def __init__(self, **kwargs):
            self.jobs = {}
            self.lock = threading.Lock()
        def create_job(self, job_id):
            with self.lock:
                self.jobs[job_id] = {'job_id': job_id, 'status': 'pending', 'progress': 0}
                return self.jobs[job_id]
        def update_job(self, job_id, **kwargs):
            with self.lock:
                if job_id not in self.jobs:
                    self.jobs[job_id] = {'job_id': job_id}
                self.jobs[job_id].update(kwargs)
        def get_job(self, job_id):
            with self.lock:
                return self.jobs.get(job_id)

load_dotenv()

# Set safe defaults
os.environ.setdefault('FLASK_SECRET_KEY', 'production-secret-change-me')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize JobStore
job_store = JobStore(ttl_seconds=3600, max_jobs=1000)


@app.route('/')
def index():
    """Main page"""
    return render_template('integrated.html')


@app.route('/health')
def health():
    """Health check for Railway/Hugging Face"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'yt2tik_available': YT2TIK_AVAILABLE
    }), 200


@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video with comprehensive validation"""
    try:
        if not request.json:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_REQUEST',
                'solution': 'Send JSON data'
            }), 400

        data = request.json
        youtube_url = data.get('youtube_url', '').strip()
        start_time = data.get('start_time', '').strip()
        duration = data.get('duration', 30)
        caption = data.get('caption', '').strip()
        auto_detect = data.get('auto_detect', False)

        # Validate URL
        if not youtube_url:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_URL',
                'solution': 'Provide a valid YouTube URL'
            }), 400

        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_URL',
                'solution': 'URL must be from YouTube'
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

        # Validate start time format
        if start_time:
            try:
                parts = start_time.split(':')
                if len(parts) > 3:
                    raise ValueError()
                for part in parts:
                    int(part)
            except:
                return jsonify({
                    'status': 'error',
                    'reason': 'INVALID_TIME',
                    'solution': 'Use format HH:MM:SS, MM:SS, or SS'
                }), 400

        # Create job
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued')

        print(f"[JOB] Created: {job_id}")

        # Start background processing
        thread = threading.Thread(
            target=process_video_safe,
            args=(job_id, youtube_url, start_time, duration, caption, auto_detect),
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
            'solution': 'Try again or contact support',
            'details': str(e)
        }), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status - NEVER returns 404 for valid job format"""
    try:
        if not job_id:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_JOB_ID',
                'solution': 'Provide a valid job ID'
            }), 400

        # Get job from store
        job_data = job_store.get_job(job_id)

        if not job_data:
            # Return a proper response instead of 404
            return jsonify({
                'status': 'error',
                'job_id': job_id,
                'reason': 'JOB_NOT_FOUND',
                'solution': 'Job may have expired (1 hour TTL) or never existed',
                'message': 'Job not found'
            }), 200  # Return 200, not 404, so frontend doesn't break

        return jsonify(job_data), 200

    except Exception as e:
        print(f"[ERROR] /status: {str(e)}")
        return jsonify({
            'status': 'error',
            'reason': 'STATUS_ERROR',
            'solution': 'Try refreshing the page',
            'details': str(e)
        }), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download converted video"""
    try:
        # Security check
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'status': 'error',
                'reason': 'INVALID_FILENAME',
                'solution': 'Use a valid filename'
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
                'solution': 'File may have expired or been deleted'
            }), 404

        # Security: ensure file is in output directory
        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            return jsonify({
                'status': 'error',
                'reason': 'ACCESS_DENIED',
                'solution': 'Invalid file path'
            }), 403

        return send_file(file_path, mimetype='video/mp4', as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"[ERROR] /download: {str(e)}")
        return jsonify({
            'status': 'error',
            'reason': 'DOWNLOAD_ERROR',
            'solution': 'Try again later'
        }), 500


def process_video_safe(job_id: str, youtube_url: str, start_time: str,
                       duration: int, caption: str, auto_detect: bool):
    """
    Safe wrapper - NEVER crashes, always updates job status
    """
    try:
        process_video(job_id, youtube_url, start_time, duration, caption, auto_detect)
    except Exception as e:
        print(f"[FATAL] Job {job_id} crashed: {str(e)}")
        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        # Always update job status on crash
        try:
            job_store.update_job(
                job_id,
                status='error',
                progress=0,
                message=f'Fatal error: {str(e)}',
                reason='FATAL_ERROR',
                solution='Try a different video or contact support'
            )
        except:
            pass


def process_video(job_id: str, youtube_url: str, start_time: str,
                  duration: int, caption: str, auto_detect: bool):
    """Background video processing with structured error handling"""

    def update_status(status, progress, message, **extra):
        """Update job status safely"""
        try:
            job_store.update_job(job_id, status=status, progress=progress, message=message, **extra)
        except Exception as e:
            print(f"[ERROR] Failed to update job: {str(e)}")

    try:
        print(f"\n=== Processing Job {job_id} ===")
        print(f"URL: {youtube_url}")

        # Step 1: Download video
        update_status('processing', 10, 'Starting download...')

        try:
            update_status('processing', 20, 'Downloading YouTube video...')
            video_data = download_youtube_video(youtube_url)

            if not video_data or 'video_path' not in video_data:
                raise Exception("Download returned no data")

            video_path = video_data['video_path']
            video_title = video_data.get('title', 'Unknown')

            if not Path(video_path).exists():
                raise Exception("Downloaded file not found")

            file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            print(f"[OK] Downloaded: {video_title} ({file_size_mb:.1f} MB)")

        except DownloadError as e:
            # Structured error from downloader
            update_status('error', 0, str(e), reason=e.reason, solution=e.solution)
            print(f"[ERROR] Download failed: {e.reason}")
            return

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Download failed: {error_msg}")

            # Generic download error
            update_status(
                'error', 0,
                f'Download failed: {error_msg}',
                reason='DOWNLOAD_FAILED',
                solution='Check video URL or try a different video'
            )
            return

        # Step 2: Convert video
        try:
            update_status('processing', 50, 'Preparing conversion...')

            # Generate safe filename
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            print(f"[CONVERT] Converting to: {output_filename}")
            update_status('processing', 60, 'Converting to TikTok format...')

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time,
                duration=duration,
                auto_detect=auto_detect and not start_time
            )

            if not Path(converted_path).exists():
                raise Exception("Conversion output not created")

            output_size_mb = Path(converted_path).stat().st_size / (1024 * 1024)
            print(f"[OK] Converted: {output_size_mb:.1f} MB")

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Conversion failed: {error_msg}")

            if 'ffmpeg' in error_msg.lower():
                update_status(
                    'error', 0,
                    'Video conversion failed',
                    reason='FFMPEG_ERROR',
                    solution='FFmpeg may not be installed or video format unsupported'
                )
            else:
                update_status(
                    'error', 0,
                    f'Conversion failed: {error_msg}',
                    reason='CONVERSION_FAILED',
                    solution='Try a different video or shorter duration'
                )
            return

        # Step 3: Success
        try:
            update_status('processing', 90, 'Finalizing...')

            update_status(
                'completed', 100,
                'Conversion complete!',
                video_title=video_title,
                duration=duration,
                filename=output_filename,
                video_url=f'/download/{output_filename}'
            )

            print(f"[SUCCESS] Job {job_id} completed")

        except Exception as e:
            print(f"[ERROR] Failed to save results: {str(e)}")
            update_status(
                'error', 0,
                'Processing completed but failed to save results',
                reason='SAVE_FAILED',
                solution='Try again'
            )
            return

    except Exception as e:
        error_msg = str(e)
        print(f"[FATAL] Unexpected error: {error_msg}")

        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        update_status(
            'error', 0,
            f'Unexpected error: {error_msg}',
            reason='UNKNOWN_ERROR',
            solution='Contact support if this persists'
        )


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404"""
    if request.path.startswith('/api/'):
        return jsonify({
            'status': 'error',
            'reason': 'NOT_FOUND',
            'solution': 'Check the URL'
        }), 404
    return render_template('integrated.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500"""
    print(f"[500] {str(error)}")
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({
            'status': 'error',
            'reason': 'SERVER_ERROR',
            'solution': 'Try again later'
        }), 500
    return render_template('integrated.html'), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all exception handler"""
    print(f"[EXCEPTION] {type(e).__name__}: {str(e)}")
    try:
        import traceback
        traceback.print_exc()
    except:
        pass

    if request.path.startswith('/api/') or request.is_json:
        return jsonify({
            'status': 'error',
            'reason': 'UNHANDLED_ERROR',
            'solution': 'Contact support'
        }), 500
    return render_template('integrated.html'), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 7860))

    print("=" * 70)
    print("🚀 PRODUCTION YouTube to TikTok Converter")
    print("=" * 70)
    print("")
    print("✅ Multi-client fallback (android → ios → web)")
    print("✅ Structured error handling")
    print("✅ Thread-safe job tracking")
    print("✅ Zero-crash architecture")
    print("✅ Cookie support (optional)")
    print("")
    print(f"🌐 Server: http://0.0.0.0:{port}")
    print("=" * 70)

    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
