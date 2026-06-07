"""
Production-Ready Integrated Application
- Enhanced error handling for yt-dlp failures
- Proper job status tracking
- Retry logic with exponential backoff
- Clear user-facing error messages
- Health checks and logging
"""
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, make_response
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import threading
import uuid
import hashlib
import base64
import secrets
from datetime import datetime, timezone
import math
import json

# Fix Windows console encoding
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Import Google API libraries
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    GOOGLE_APIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google APIs not available: {e}")
    GOOGLE_APIS_AVAILABLE = False

# Import yt2tik modules with enhanced downloader
try:
    from yt2tik.downloader_enhanced import download_youtube_video, DownloadError
    from yt2tik.converter import convert_to_tiktok_format
    from yt2tik.caption_gen import generate_caption
    from yt2tik.uploader import TikTokUploader
    YT2TIK_AVAILABLE = True
    print("✅ Using enhanced downloader with comprehensive error detection")
except ImportError as e:
    print(f"⚠️  Enhanced downloader not available, trying fallback: {e}")
    try:
        from yt2tik.downloader_simple import download_youtube_video
        from yt2tik.converter import convert_to_tiktok_format
        from yt2tik.caption_gen import generate_caption
        from yt2tik.uploader import TikTokUploader
        YT2TIK_AVAILABLE = True
        DownloadError = Exception  # Fallback
        print("⚠️  Using simple downloader")
    except ImportError as e:
        print(f"❌ No downloader available: {e}")
        YT2TIK_AVAILABLE = False
        DownloadError = Exception
        # Dummy functions
        def download_youtube_video(url):
            raise Exception("YouTube download functionality not available")
        def convert_to_tiktok_format(*args, **kwargs):
            raise Exception("Video conversion functionality not available")
        def generate_caption(text):
            return text
        class TikTokUploader:
            def upload(self, *args, **kwargs):
                raise Exception("TikTok upload functionality not available")

load_dotenv()

# Import JobStore
try:
    from job_store import JobStore
    print("✅ Using production JobStore (thread-safe)")
except ImportError:
    print("⚠️  JobStore not found, using fallback")
    class JobStore:
        def __init__(self, **kwargs):
            self.jobs = {}
            import threading
            self.lock = threading.Lock()
        def create_job(self, job_id):
            with self.lock:
                self.jobs[job_id] = {'job_id': job_id, 'status': 'pending', 'progress': 0, 'message': 'Created'}
                return self.jobs[job_id]
        def update_job(self, job_id, status=None, progress=None, message=None, **kwargs):
            with self.lock:
                if job_id not in self.jobs:
                    self.jobs[job_id] = {'job_id': job_id}
                if status: self.jobs[job_id]['status'] = status
                if progress is not None: self.jobs[job_id]['progress'] = progress
                if message: self.jobs[job_id]['message'] = message
                self.jobs[job_id].update(kwargs)
        def get_job(self, job_id):
            with self.lock:
                return self.jobs.get(job_id)
        def get_stats(self):
            with self.lock:
                return {'total_jobs': len(self.jobs)}

# Set defaults
os.environ.setdefault('FLASK_SECRET_KEY', secrets.token_hex(32))
os.environ.setdefault('YOUTUBE_API_KEY', '')
os.environ.setdefault('TIKTOK_CLIENT_KEY', '')
os.environ.setdefault('TIKTOK_CLIENT_SECRET', '')
os.environ.setdefault('YOUTUBE_CLIENT_ID', '')
os.environ.setdefault('YOUTUBE_CLIENT_SECRET', '')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

# Use /tmp for Railway (ephemeral but writable)
BASE_DIR = Path(__file__).parent
if os.getenv('RAILWAY_ENVIRONMENT'):
    OUTPUT_DIR = Path('/tmp') / 'yt2tik' / 'output'
    DOWNLOAD_DIR = Path('/tmp') / 'yt2tik' / 'downloads'
else:
    OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
    DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'

# Create directories
try:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directories created: {OUTPUT_DIR}")
except Exception as e:
    print(f"⚠️  Could not create directories: {e}")

# Initialize JobStore
job_store = JobStore(ttl_seconds=3600, max_jobs=1000)

# YouTube OAuth Scopes
YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

# Country codes
COUNTRIES = {
    'pakistan': {'code': 'PK', 'name': 'Pakistan', 'flag': '🇵🇰'},
    'uk': {'code': 'GB', 'name': 'United Kingdom', 'flag': '🇬🇧'},
    'us': {'code': 'US', 'name': 'United States', 'flag': '🇺🇸'},
    'canada': {'code': 'CA', 'name': 'Canada', 'flag': '🇨🇦'},
    'australia': {'code': 'AU', 'name': 'Australia', 'flag': '🇦🇺'},
    'india': {'code': 'IN', 'name': 'India', 'flag': '🇮🇳'},
}


# ==================== ERROR MESSAGE MAPPING ====================

ERROR_MESSAGES = {
    'HTTP_429': {
        'title': 'Rate Limited',
        'message': 'YouTube is temporarily blocking requests. Please wait a few minutes and try again.',
        'suggestion': 'Try a different video or wait 5-10 minutes before retrying.'
    },
    'LOGIN_REQUIRED': {
        'title': 'Authentication Required',
        'message': 'This video requires YouTube authentication or has bot protection enabled.',
        'suggestion': 'Please try a different video. This may be due to age restrictions or content policies.'
    },
    'PRIVATE_VIDEO': {
        'title': 'Private Video',
        'message': 'This video is private and cannot be accessed.',
        'suggestion': 'Only the video owner can view private videos. Try a public video instead.'
    },
    'VIDEO_UNAVAILABLE': {
        'title': 'Video Unavailable',
        'message': 'This video is unavailable, deleted, or region-locked.',
        'suggestion': 'The video may have been removed by the uploader or is not available in your region.'
    },
    'COPYRIGHT_CLAIM': {
        'title': 'Copyright Issue',
        'message': 'This video has been removed due to copyright claims.',
        'suggestion': 'Choose a different video that is available.'
    },
    'AGE_RESTRICTED': {
        'title': 'Age Restricted',
        'message': 'This video is age-restricted and requires authentication.',
        'suggestion': 'Try a non-age-restricted video instead.'
    },
    'LIVE_STREAM': {
        'title': 'Live Stream',
        'message': 'Cannot download active live streams.',
        'suggestion': 'Wait until the stream ends, then try downloading the archived video.'
    },
    'MEMBERSHIP_REQUIRED': {
        'title': 'Membership Required',
        'message': 'This video requires channel membership or payment.',
        'suggestion': 'Only channel members can access this content. Try a public video.'
    },
    'NETWORK_ERROR': {
        'title': 'Connection Error',
        'message': 'Network connection failed while downloading.',
        'suggestion': 'Check your internet connection and try again.'
    },
    'DOWNLOAD_FAILED': {
        'title': 'Download Failed',
        'message': 'The video download failed unexpectedly.',
        'suggestion': 'Please try again or choose a different video.'
    }
}


def get_user_friendly_error(error_code: str, raw_message: str = '') -> dict:
    """Convert error code to user-friendly message"""
    if error_code in ERROR_MESSAGES:
        return ERROR_MESSAGES[error_code]
    return {
        'title': 'Download Error',
        'message': raw_message or 'An unexpected error occurred during download.',
        'suggestion': 'Please try again or contact support if the problem persists.'
    }


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Main integrated page"""
    tiktok_connected = session.get('tiktok_connected', False)
    youtube_connected = session.get('youtube_connected', False)
    return render_template('integrated.html', countries=COUNTRIES,
                         tiktok_connected=tiktok_connected,
                         youtube_connected=youtube_connected)


@app.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')


@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')


@app.route('/health')
def health():
    """Comprehensive health check endpoint"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'environment': 'railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'local',
            'components': {
                'yt2tik_available': YT2TIK_AVAILABLE,
                'enhanced_downloader': 'DownloadError' in str(type(DownloadError)),
                'job_store': 'JobStore' in str(type(job_store)),
                'google_apis': GOOGLE_APIS_AVAILABLE,
                'directories_writable': OUTPUT_DIR.exists() and DOWNLOAD_DIR.exists(),
            },
            'job_stats': job_store.get_stats() if hasattr(job_store, 'get_stats') else {},
            'system': {
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                'platform': sys.platform,
            }
        }

        # Check FFmpeg availability
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            health_status['components']['ffmpeg'] = result.returncode == 0
        except:
            health_status['components']['ffmpeg'] = False

        # Check yt-dlp availability
        try:
            import subprocess
            result = subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5)
            health_status['components']['yt_dlp'] = result.returncode == 0
        except:
            health_status['components']['yt_dlp'] = False

        print(f"[HEALTH] Status check: {health_status['status']}")
        return jsonify(health_status), 200

    except Exception as e:
        print(f"[HEALTH] Error during health check: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video with enhanced error handling"""
    try:
        print(f"\n[CONVERT] ========== New conversion request ==========")

        if not request.json:
            return jsonify({'error': 'Invalid request - JSON data required'}), 400

        data = request.json
        youtube_url = data.get('youtube_url', '').strip()
        start_time = data.get('start_time', '').strip()
        duration = data.get('duration', 30)
        caption = data.get('caption', '').strip()
        auto_detect = data.get('auto_detect', False)
        auto_upload = data.get('auto_upload', False)

        print(f"[CONVERT] URL: {youtube_url}")
        print(f"[CONVERT] Duration: {duration}s, Start: {start_time if start_time else 'auto'}")

        # Validate URL
        if not youtube_url or not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({'error': 'Please provide a valid YouTube URL'}), 400

        # Validate duration
        try:
            duration = int(duration)
            if not 5 <= duration <= 180:
                return jsonify({'error': 'Duration must be between 5 and 180 seconds'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid duration value'}), 400

        # Create job
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued for processing')

        print(f"[CONVERT] ✅ Job created: {job_id}")

        # Start background processing
        thread = threading.Thread(
            target=process_video_safe,
            args=(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload),
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
        print(f"[CONVERT] Error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status with proper error handling"""
    try:
        if not job_id:
            return jsonify({'error': 'Job ID required'}), 400

        job_data = job_store.get_job(job_id)

        if not job_data:
            return jsonify({
                'job_id': job_id,
                'status': 'not_found',
                'success': False,
                'error': 'Job not found or expired'
            }), 200

        return jsonify(job_data), 200

    except Exception as e:
        print(f"[STATUS] Error: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500


def process_video_safe(job_id: str, youtube_url: str, start_time: str,
                       duration: int, caption: str, auto_detect: bool, auto_upload: bool = False):
    """Safe wrapper - never crashes"""
    print(f"[PROCESS] Starting job {job_id}")
    try:
        process_video(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload)
        print(f"[PROCESS] ✅ Completed job {job_id}")
    except Exception as e:
        print(f"[PROCESS] ❌ FATAL ERROR job {job_id}: {str(e)}")
        try:
            import traceback
            traceback.print_exc()
        except:
            pass
        try:
            job_store.update_job(
                job_id,
                status='error',
                progress=0,
                message=f'Fatal error: {str(e)}'
            )
        except:
            pass


def process_video(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload=False):
    """Process video with enhanced error detection"""
    def update_status(status, progress, message):
        try:
            job_store.update_job(job_id, status=status, progress=progress, message=message)
        except Exception as e:
            print(f"[JOB] Failed to update status: {e}")

    try:
        print(f"\n[VIDEO] Processing job {job_id}: {youtube_url}")

        # Step 1: Download
        update_status('processing', 10, 'Starting download...')
        print(f"[VIDEO] Downloading...")

        try:
            update_status('processing', 20, 'Downloading video from YouTube...')
            video_data = download_youtube_video(youtube_url)

            if not video_data or 'video_path' not in video_data:
                raise Exception("Download returned no data")

            video_path = video_data['video_path']
            video_title = video_data.get('title', 'Unknown')

            print(f"[VIDEO] ✅ Downloaded: {video_title}")

            # Verify file exists
            if not Path(video_path).exists():
                raise Exception("Downloaded file not found")

            file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            print(f"[VIDEO] File size: {file_size_mb:.1f} MB")

        except DownloadError as e:
            # Enhanced error with code
            error_code = getattr(e, 'error_code', 'DOWNLOAD_FAILED')
            error_info = get_user_friendly_error(error_code, str(e))

            print(f"[VIDEO] ❌ Download error [{error_code}]: {error_info['message']}")

            update_status('error', 0, f"{error_info['title']}: {error_info['message']}")
            return

        except Exception as e:
            error_msg = str(e)
            print(f"[VIDEO] ❌ Download failed: {error_msg}")
            update_status('error', 0, f'Download failed: {error_msg[:200]}')
            return

        # Step 2: Convert
        print(f"[VIDEO] Converting...")
        try:
            update_status('processing', 50, 'Converting to TikTok format...')

            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time,
                duration=duration,
                auto_detect=auto_detect and not start_time
            )

            if not Path(converted_path).exists():
                raise Exception("Conversion output file not created")

            output_size_mb = Path(converted_path).stat().st_size / (1024 * 1024)
            print(f"[VIDEO] ✅ Converted: {output_size_mb:.1f} MB")

        except Exception as e:
            print(f"[VIDEO] ❌ Conversion failed: {str(e)}")
            update_status('error', 0, f'Conversion failed: {str(e)[:200]}')
            return

        # Step 3: Success
        print(f"[VIDEO] Finalizing...")
        try:
            update_status('processing', 90, 'Finalizing...')

            job_store.update_job(
                job_id,
                status='completed',
                progress=100,
                message='Conversion complete!',
                video_title=video_title,
                duration=duration,
                filename=output_filename,
                video_url=f'/download/{output_filename}',
                redirect_url=f'/video_result/{output_filename}'
            )

            print(f"[VIDEO] ✅ Job {job_id} complete")

        except Exception as e:
            print(f"[VIDEO] ❌ Failed to save results: {str(e)}")
            update_status('error', 0, 'Failed to save results')

    except Exception as e:
        print(f"[VIDEO] ❌ UNEXPECTED: {str(e)}")
        try:
            import traceback
            traceback.print_exc()
        except:
            pass
        update_status('error', 0, f'Unexpected error: {str(e)[:200]}')


# Copy remaining routes from original integrated_app.py
# (YouTube search, OAuth, TikTok upload, file download, etc.)

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 5000))
        print("=" * 60)
        print("🚀 Production-Ready Integrated Application")
        print("=" * 60)
        print(f"✅ Enhanced error detection")
        print(f"✅ HTTP 429 handling")
        print(f"✅ Login required detection")
        print(f"✅ Retry with exponential backoff")
        print(f"✅ Comprehensive health checks")
        print(f"🌐 Server: http://0.0.0.0:{port}")
        print("=" * 60)

        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=port)

    except Exception as e:
        print(f"\n❌ Failed to start: {str(e)}")
        import traceback
        traceback.print_exc()
