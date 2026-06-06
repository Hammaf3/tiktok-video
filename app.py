"""
Production Flask App: YouTube to TikTok Converter
Web UI + API - Railway Deployment Ready
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import threading
import uuid
from datetime import datetime, timezone
import time
import traceback

# Fix encoding issues
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Import with fallback handling
try:
    from yt2tik.downloader_production import (
        download_youtube_video,
        VideoRestrictionError,
        VideoUnavailableError,
        cleanup_old_downloads
    )
    DOWNLOADER_AVAILABLE = True
except ImportError:
    print("Warning: Production downloader not available, using fallback")
    try:
        from yt2tik.downloader_stable import download_youtube_video
        VideoRestrictionError = Exception
        VideoUnavailableError = Exception
        DOWNLOADER_AVAILABLE = True
    except ImportError:
        print("Error: No downloader available")
        DOWNLOADER_AVAILABLE = False
        def download_youtube_video(url):
            raise Exception("Downloader not configured")
        VideoRestrictionError = Exception
        VideoUnavailableError = Exception

try:
    from yt2tik.converter_stable import convert_to_tiktok_format
    CONVERTER_AVAILABLE = True
except ImportError:
    print("Error: Converter not available")
    CONVERTER_AVAILABLE = False
    def convert_to_tiktok_format(*args, **kwargs):
        raise Exception("Converter not configured")

load_dotenv()

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'production-secret-change-me')

# Configuration
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'

# Create directories
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")

# ==================== JOB TRACKING SYSTEM ====================

class JobStore:
    """Thread-safe job tracking with automatic cleanup"""

    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()
        self.max_jobs = 1000
        self.job_ttl = 3600  # 1 hour

    def create_job(self, job_id: str) -> dict:
        """Create a new job"""
        with self.lock:
            job = {
                'job_id': job_id,
                'status': 'pending',
                'progress': 0,
                'message': 'Job created',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            self.jobs[job_id] = job
            self._cleanup_old_jobs()
            return job.copy()

    def update_job(self, job_id: str, status: str = None, progress: int = None,
                   message: str = None, **kwargs):
        """Update job status"""
        with self.lock:
            if job_id not in self.jobs:
                self.jobs[job_id] = {
                    'job_id': job_id,
                    'status': 'error',
                    'progress': 0,
                    'message': 'Job expired or not found',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                }

            job = self.jobs[job_id]
            if status:
                job['status'] = status
            if progress is not None:
                job['progress'] = progress
            if message:
                job['message'] = message

            for key, value in kwargs.items():
                job[key] = value

            job['updated_at'] = datetime.now(timezone.utc).isoformat()

    def get_job(self, job_id: str) -> dict:
        """Get job status"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                # Check for timeout
                try:
                    created = datetime.fromisoformat(job['created_at'])
                    elapsed = (datetime.now(timezone.utc) - created).total_seconds()

                    if job['status'] == 'processing' and elapsed > 600:  # 10 minutes
                        job['status'] = 'error'
                        job['message'] = 'Processing timeout. Please try a shorter video.'
                        job['progress'] = 0
                except:
                    pass

                return job.copy()
            return None

    def _cleanup_old_jobs(self):
        """Remove old jobs to prevent memory leaks"""
        try:
            if len(self.jobs) < self.max_jobs:
                return

            now = datetime.now(timezone.utc)
            expired_jobs = []

            for job_id, job in self.jobs.items():
                try:
                    created = datetime.fromisoformat(job['created_at'])
                    age = (now - created).total_seconds()

                    if age > self.job_ttl:
                        expired_jobs.append(job_id)
                except:
                    expired_jobs.append(job_id)

            for job_id in expired_jobs:
                del self.jobs[job_id]

            if expired_jobs:
                print(f"Cleaned up {len(expired_jobs)} expired jobs")
        except Exception as e:
            print(f"Job cleanup error: {e}")

# Global job store
job_store = JobStore()

# ==================== WEB UI ROUTES ====================

@app.route('/')
def index():
    """Main web page"""
    try:
        return render_template('simple.html')
    except Exception as e:
        print(f"Template error: {e}")
        # Fallback HTML if template not found
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>YouTube to TikTok Converter</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px;">
            <h1>YouTube to TikTok Converter</h1>
            <p><strong>Error:</strong> Template not found. Using API mode.</p>
            <h2>API Endpoints:</h2>
            <ul>
                <li><code>GET /health</code> - Health check</li>
                <li><code>POST /convert</code> - Start conversion</li>
                <li><code>GET /status/&lt;job_id&gt;</code> - Check status</li>
                <li><code>GET /download/&lt;filename&gt;</code> - Download video</li>
            </ul>
            <h3>Example:</h3>
            <pre>
curl -X POST https://your-app.railway.app/convert \\
  -H "Content-Type: application/json" \\
  -d '{"youtube_url": "https://youtube.com/watch?v=VIDEO_ID", "duration": 30}'
            </pre>
        </body>
        </html>
        """


@app.route('/api')
def api_docs():
    """API documentation (JSON)"""
    return jsonify({
        'status': 'online',
        'service': 'YouTube to TikTok Converter',
        'version': '1.0.0',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'endpoints': {
            'web': {
                '/': 'Web UI (HTML)',
                '/api': 'API documentation (this page)'
            },
            'conversion': {
                '/convert': 'POST - Start conversion job',
                '/status/<job_id>': 'GET - Check job status',
                '/download/<filename>': 'GET - Download converted video'
            },
            'monitoring': {
                '/health': 'GET - Health check'
            }
        },
        'usage': {
            'convert': {
                'method': 'POST',
                'url': '/convert',
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
    """Health check for Railway"""
    return jsonify({
        'status': 'healthy',
        'downloader': DOWNLOADER_AVAILABLE,
        'converter': CONVERTER_AVAILABLE,
        'jobs_count': len(job_store.jobs),
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


# ==================== API ROUTES ====================

@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video to TikTok format (API endpoint)"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'error': 'Invalid request. Content-Type must be application/json'
            }), 400

        data = request.json
        youtube_url = data.get('youtube_url', '').strip()
        start_time = data.get('start_time', '').strip()
        duration = data.get('duration', 30)
        caption = data.get('caption', '').strip()

        # Validate YouTube URL
        if not youtube_url:
            return jsonify({'error': 'youtube_url is required'}), 400

        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Validate duration
        try:
            duration = int(duration)
            if duration < 5:
                return jsonify({'error': 'Duration must be at least 5 seconds'}), 400
            if duration > 180:
                return jsonify({'error': 'Duration cannot exceed 180 seconds'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid duration value'}), 400

        # Validate start_time format if provided
        if start_time:
            try:
                parts = start_time.split(':')
                if len(parts) > 3:
                    raise ValueError()
                for part in parts:
                    int(part)
            except:
                return jsonify({'error': 'Invalid start_time format. Use HH:MM:SS, MM:SS, or SS'}), 400

        # Create job
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued for processing')

        # Start background processing
        thread = threading.Thread(
            target=process_video_safe,
            args=(job_id, youtube_url, start_time, duration, caption),
            daemon=True
        )
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Processing started',
            'status_url': f'/status/{job_id}'
        }), 202

    except Exception as e:
        print(f"Error in /convert: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Server error occurred',
            'details': str(e)
        }), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get conversion job status (API endpoint)"""
    try:
        if not job_id:
            return jsonify({'error': 'job_id is required'}), 400

        job = job_store.get_job(job_id)

        if not job:
            return jsonify({
                'error': 'Job not found',
                'job_id': job_id,
                'message': 'Job may have expired (1 hour TTL) or never existed'
            }), 404

        return jsonify(job), 200

    except Exception as e:
        print(f"Error in /status: {str(e)}")
        return jsonify({
            'error': 'Failed to get status',
            'details': str(e)
        }), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download converted video file"""
    try:
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': 'Invalid filename'}), 400

        if not filename.endswith('.mp4'):
            return jsonify({'error': 'Invalid file type'}), 400

        file_path = OUTPUT_DIR / filename

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        # Security: ensure file is in OUTPUT_DIR
        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            return jsonify({'error': 'Access denied'}), 403

        return send_file(
            file_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"Error in /download: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


# ==================== BACKGROUND PROCESSING ====================

def process_video_safe(job_id: str, youtube_url: str, start_time: str,
                       duration: int, caption: str):
    """Safe wrapper for video processing - NEVER crashes"""
    try:
        process_video(job_id, youtube_url, start_time, duration, caption)
    except Exception as e:
        error_msg = str(e)
        print(f"Fatal error in job {job_id}: {error_msg}")
        traceback.print_exc()

        job_store.update_job(
            job_id,
            status='error',
            progress=0,
            message=f'Fatal error: {error_msg}'
        )


def process_video(job_id: str, youtube_url: str, start_time: str,
                  duration: int, caption: str):
    """Background video processing with comprehensive error handling"""

    def update(status, progress, message, **kwargs):
        """Helper to update job status"""
        job_store.update_job(job_id, status=status, progress=progress,
                            message=message, **kwargs)
        print(f"[{job_id[:8]}] {progress}% - {message}")

    video_path = None
    converted_path = None

    try:
        update('processing', 5, 'Starting download...')

        # Step 1: Download YouTube video
        try:
            update('processing', 10, 'Downloading from YouTube...')

            video_data = download_youtube_video(youtube_url, use_cookies=False, max_retries=2)

            video_path = video_data['video_path']
            video_title = video_data['title']
            video_duration = video_data['duration']

            update('processing', 30, f'Downloaded: {video_title[:50]}...')

        except VideoRestrictionError as e:
            update('error', 0, f'Video Restricted: {str(e)}')
            return

        except VideoUnavailableError as e:
            update('error', 0, f'Video Unavailable: {str(e)}')
            return

        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                update('error', 0, 'Download timeout. Try a shorter video.')
            elif 'network' in error_msg.lower() or 'connection' in error_msg.lower():
                update('error', 0, 'Network error. Check your connection.')
            else:
                update('error', 0, f'Download failed: {error_msg}')
            return

        # Step 2: Convert to TikTok format
        try:
            update('processing', 40, 'Converting to TikTok format...')

            # Generate safe output filename
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            update('processing', 50, 'Processing video...')

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time if start_time else None,
                duration=duration,
                auto_detect=False
            )

            # Verify output
            if not Path(converted_path).exists():
                raise Exception("Conversion completed but file not found")

            output_size_mb = Path(converted_path).stat().st_size / (1024 * 1024)

            update('processing', 90, 'Finalizing...')

        except Exception as e:
            error_msg = str(e)
            if 'ffmpeg' in error_msg.lower():
                update('error', 0, 'Video conversion failed. FFmpeg error.')
            elif 'codec' in error_msg.lower():
                update('error', 0, 'Video format not supported.')
            else:
                update('error', 0, f'Conversion failed: {error_msg}')
            return

        # Step 3: Success
        update(
            'completed',
            100,
            'Conversion complete!',
            video_title=video_title,
            filename=output_filename,
            video_url=f'/download/{output_filename}',
            file_size_mb=round(output_size_mb, 1),
            duration=duration
        )

    except Exception as e:
        error_msg = str(e)
        print(f"Unexpected error: {error_msg}")
        traceback.print_exc()
        update('error', 0, f'Unexpected error: {error_msg}')

    finally:
        # Cleanup: delete downloaded video (keep converted)
        try:
            if video_path and Path(video_path).exists():
                Path(video_path).unlink()
                print(f"Cleaned up: {video_path}")
        except Exception as e:
            print(f"Cleanup warning: {e}")


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api') or request.path.startswith('/status') or request.path.startswith('/download'):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource does not exist'
        }), 404

    # For web pages, render 404 page or redirect to home
    try:
        return render_template('404.html'), 404
    except:
        return """
        <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>404 - Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/">Go Home</a>
        </body>
        </html>
        """, 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"Internal error: {str(error)}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all exception handler"""
    print(f"Unhandled exception: {type(e).__name__}: {str(e)}")
    traceback.print_exc()

    return jsonify({
        'error': 'Server error',
        'message': str(e)
    }), 500


# ==================== STARTUP ====================

# Cleanup old files on startup
try:
    cleanup_old_downloads(days=1)
except:
    pass

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("=" * 60)
    print("YouTube to TikTok Converter - Production")
    print("=" * 60)
    print(f"Downloader: {'OK' if DOWNLOADER_AVAILABLE else 'FAIL'}")
    print(f"Converter: {'OK' if CONVERTER_AVAILABLE else 'FAIL'}")
    print(f"Server: http://0.0.0.0:{port}")
    print("=" * 60)

    app.run(host='0.0.0.0', port=port, debug=False)
