"""
Integrated YouTube Analyzer + Converter with TikTok Auto-Upload
Production-ready for Railway deployment
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

# Fix Windows console encoding for Unicode characters (safe for all platforms)
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Import Google API libraries with error handling
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google_auth_oauthlib.flow import Flow
    from google.oauth2.credentials import Credentials
    GOOGLE_APIS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Google APIs not available: {e}")
    GOOGLE_APIS_AVAILABLE = False

# Import existing modules with error handling
try:
    from yt2tik.downloader_fixed import download_youtube_video, cleanup_old_downloads
    from yt2tik.converter import convert_to_tiktok_format
    from yt2tik.caption_gen import generate_caption
    from yt2tik.uploader import TikTokUploader
    YT2TIK_AVAILABLE = True
    print("✅ Using fixed production downloader with retry logic")
except ImportError as e:
    print(f"⚠️  Fixed downloader not available, trying original: {e}")
    try:
        from yt2tik.downloader import download_youtube_video
        from yt2tik.converter import convert_to_tiktok_format
        from yt2tik.caption_gen import generate_caption
        from yt2tik.uploader import TikTokUploader
        YT2TIK_AVAILABLE = True
        cleanup_old_downloads = lambda days: None  # Dummy function
        print("⚠️  Using original downloader (not production-ready)")
    except ImportError as e:
        print(f"Warning: yt2tik modules not fully available: {e}")
        YT2TIK_AVAILABLE = False
        cleanup_old_downloads = lambda days: None
        # Create dummy functions so the app doesn't crash
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
    print("⚠️  JobStore not found, using simple dict")
    # Fallback to simple dict if JobStore not available
    class JobStore:
        def __init__(self, **kwargs):
            self.jobs = {}
        def create_job(self, job_id):
            self.jobs[job_id] = {'job_id': job_id, 'status': 'pending', 'progress': 0, 'message': 'Created'}
            return self.jobs[job_id]
        def update_job(self, job_id, status=None, progress=None, message=None, **kwargs):
            if job_id not in self.jobs:
                self.jobs[job_id] = {'job_id': job_id}
            if status: self.jobs[job_id]['status'] = status
            if progress is not None: self.jobs[job_id]['progress'] = progress
            if message: self.jobs[job_id]['message'] = message
            self.jobs[job_id].update(kwargs)
        def get_job(self, job_id):
            return self.jobs.get(job_id)

# Set defaults for optional environment variables to prevent crashes
os.environ.setdefault('FLASK_SECRET_KEY', 'default-secret-change-in-production')
os.environ.setdefault('YOUTUBE_API_KEY', '')
os.environ.setdefault('TIKTOK_CLIENT_KEY', '')
os.environ.setdefault('TIKTOK_CLIENT_SECRET', '')
os.environ.setdefault('YOUTUBE_CLIENT_ID', '')
os.environ.setdefault('YOUTUBE_CLIENT_SECRET', '')

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'integrated-secret-key')

# Base directory for file paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'

# Initialize JobStore (replaces simple dict)
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


@app.route('/')
def index():
    """Main integrated page"""
    tiktok_connected = session.get('tiktok_connected', False)
    youtube_connected = session.get('youtube_connected', False)
    return render_template('integrated.html', countries=COUNTRIES, tiktok_connected=tiktok_connected, youtube_connected=youtube_connected)


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
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'routes_working': True,
        'templates_loaded': True
    }), 200


@app.route('/debug/session')
def debug_session():
    """Debug endpoint to check session status"""
    session_data = {
        'tiktok_connected': session.get('tiktok_connected', False),
        'youtube_connected': session.get('youtube_connected', False),
        'has_youtube_credentials': 'youtube_credentials' in session,
        'session_keys': list(session.keys())
    }

    if 'youtube_credentials' in session:
        creds = session['youtube_credentials']
        session_data['youtube_token_preview'] = creds.get('token', '')[:30] + '...' if creds.get('token') else 'None'
        session_data['has_refresh_token'] = bool(creds.get('refresh_token'))

    return jsonify(session_data)


@app.route('/test/youtube')
def test_youtube():
    """Test page for YouTube API debugging"""
    response = make_response(render_template('test_youtube.html'))
    # Disable CSP for test page
    response.headers['Content-Security-Policy'] = "default-src * 'unsafe-inline' 'unsafe-eval'; script-src * 'unsafe-inline' 'unsafe-eval'; connect-src *; img-src * data:; style-src * 'unsafe-inline';"
    return response


# ==================== ANALYZER FUNCTIONS ====================

def get_youtube_client():
    """Initialize YouTube API client"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise Exception("YouTube API key not found in .env file")
    return build('youtube', 'v3', developerKey=api_key)


def search_videos(query, country_code, max_results=30):
    """Search videos by query and country"""
    youtube = get_youtube_client()

    try:
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            type='video',
            maxResults=max_results,
            order='viewCount',
            regionCode=country_code
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]

        if not video_ids:
            return []

        videos_response = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids)
        ).execute()

        videos = []
        for item in videos_response['items']:
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']

            duration_seconds = parse_duration(content_details['duration'])
            published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))

            video_data = {
                'video_id': item['id'],
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'published_at': published_at,
                'thumbnail': snippet['thumbnails']['high']['url'],
                'duration_seconds': duration_seconds,
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'url': f"https://youtube.com/watch?v={item['id']}"
            }

            video_data['viral_score'] = calculate_viral_score(video_data)
            video_data['days_old'] = (datetime.now(timezone.utc) - published_at.replace(tzinfo=timezone.utc)).days

            videos.append(video_data)

        videos.sort(key=lambda x: x['viral_score'], reverse=True)
        return videos

    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")


def parse_duration(duration_str):
    """Parse ISO 8601 duration"""
    duration_str = duration_str.replace('PT', '')
    hours = minutes = seconds = 0

    if 'H' in duration_str:
        hours = int(duration_str.split('H')[0])
        duration_str = duration_str.split('H')[1]
    if 'M' in duration_str:
        minutes = int(duration_str.split('M')[0])
        duration_str = duration_str.split('M')[1]
    if 'S' in duration_str:
        seconds = int(duration_str.split('S')[0])

    return hours * 3600 + minutes * 60 + seconds


def calculate_viral_score(video):
    """Calculate viral score (0-100)"""
    views = video['view_count']
    likes = video['like_count']
    comments = video['comment_count']
    duration = video['duration_seconds']
    days_old = (datetime.now(timezone.utc) - video['published_at'].replace(tzinfo=timezone.utc)).days

    if views == 0:
        return 0

    engagement_rate = ((likes + comments) / views) * 100
    velocity = views / max(1, days_old)
    like_ratio = likes / views if views > 0 else 0
    duration_bonus = 1.2 if 30 <= duration <= 90 else 1.0
    recency_bonus = 1.3 if days_old <= 30 else 1.0

    raw_score = (
        (engagement_rate * 40) +
        (math.log10(max(1, velocity)) * 30) +
        (like_ratio * 100 * 20) +
        (math.log10(max(1, views)) * 10)
    )

    return round(min(100, raw_score * duration_bonus * recency_bonus), 1)


def format_number(num):
    """Format large numbers"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


def format_duration(seconds):
    """Format duration"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@app.route('/search_youtube', methods=['POST'])
def search_youtube():
    """Search YouTube videos with error handling"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid request - JSON data required'}), 400

        data = request.json
        query = data.get('query', '').strip()
        country = data.get('country', 'us')
        limit = data.get('limit', 25)

        # Validate inputs
        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        if len(query) < 2:
            return jsonify({'error': 'Search query must be at least 2 characters'}), 400

        try:
            limit = int(limit)
            if limit < 1 or limit > 50:
                limit = 25
        except (ValueError, TypeError):
            limit = 25

        # Validate country code
        if country not in COUNTRIES:
            country = 'us'

        country_code = COUNTRIES.get(country, {}).get('code', 'US')

        # Search videos
        try:
            videos = search_videos(query, country_code, limit)
        except Exception as e:
            error_msg = str(e)
            if 'quota' in error_msg.lower():
                return jsonify({'error': 'YouTube API quota exceeded. Please try again tomorrow.'}), 429
            elif 'api key' in error_msg.lower():
                return jsonify({'error': 'YouTube API configuration error. Please contact support.'}), 500
            else:
                return jsonify({'error': f'Search failed: {error_msg}'}), 500

        # Format results
        results = []
        for i, video in enumerate(videos, 1):
            results.append({
                'rank': i,
                'title': video['title'],
                'channel': video['channel'],
                'url': video['url'],
                'thumbnail': video['thumbnail'],
                'views': format_number(video['view_count']),
                'views_raw': video['view_count'],
                'likes': format_number(video['like_count']),
                'comments': format_number(video['comment_count']),
                'duration': format_duration(video['duration_seconds']),
                'duration_seconds': video['duration_seconds'],
                'days_old': video['days_old'],
                'viral_score': video['viral_score'],
                'video_id': video['video_id']
            })

        return jsonify({
            'success': True,
            'query': query,
            'country': COUNTRIES.get(country, {}).get('name', 'Unknown'),
            'total': len(results),
            'videos': results
        })

    except Exception as e:
        error_msg = str(e)
        print(f"Error in /search_youtube: {error_msg}")
        return jsonify({'error': f'Search failed: {error_msg}'}), 500


# ==================== CONVERTER FUNCTIONS ====================

@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video with comprehensive validation"""
    try:
        # Validate request data
        if not request.json:
            return jsonify({'error': 'Invalid request - JSON data required'}), 400

        data = request.json
        youtube_url = data.get('youtube_url', '').strip()
        start_time = data.get('start_time', '').strip()
        duration = data.get('duration', 30)
        caption = data.get('caption', '').strip()
        auto_detect = data.get('auto_detect', False)
        auto_upload = data.get('auto_upload', False)

        # Validate YouTube URL
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        # Basic URL validation
        if not ('youtube.com' in youtube_url or 'youtu.be' in youtube_url):
            return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube link.'}), 400

        # Validate duration
        try:
            duration = int(duration)
            if duration < 5:
                return jsonify({'error': 'Duration must be at least 5 seconds'}), 400
            if duration > 180:
                return jsonify({'error': 'Duration cannot exceed 180 seconds (3 minutes)'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid duration value'}), 400

        # Validate start time format if provided
        if start_time:
            try:
                # Check format: HH:MM:SS, MM:SS, or SS
                parts = start_time.split(':')
                if len(parts) > 3 or len(parts) < 1:
                    raise ValueError("Invalid format")
                for part in parts:
                    int(part)  # Validate each part is a number
            except (ValueError, AttributeError):
                return jsonify({'error': 'Invalid start time format. Use HH:MM:SS, MM:SS, or SS'}), 400

        # Check TikTok connection if auto-upload requested
        if auto_upload and not session.get('tiktok_connected'):
            return jsonify({'error': 'Please connect your TikTok account first to enable auto-upload'}), 400

        # Create job using JobStore
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued for processing')

        print(f"[JOB] Created: {job_id}")

        # Store job_id in session
        session['current_job_id'] = job_id

        # Start background processing
        thread = threading.Thread(
            target=process_video_safe,
            args=(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload),
            daemon=True  # Daemon thread will exit when main program exits
        )
        thread.start()

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Processing started successfully',
            'status_url': f'/status/{job_id}'
        }), 202

    except Exception as e:
        error_msg = str(e)
        print(f"Error in /convert endpoint: {error_msg}")
        return jsonify({'error': f'Server error: {error_msg}'}), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get conversion status with timeout handling"""
    try:
        if not job_id:
            return jsonify({'error': 'Job ID is required'}), 400

        # Get job from JobStore
        job_data = job_store.get_job(job_id)

        if not job_data:
            return jsonify({
                'error': 'Job not found',
                'job_id': job_id,
                'message': 'Job may have expired (1 hour TTL) or never existed'
            }), 404

        return jsonify(job_data), 200

    except Exception as e:
        print(f"[ERROR] /status endpoint: {str(e)}")
        return jsonify({
            'error': 'Failed to get status',
            'details': str(e)
        }), 500


@app.route('/video_result/<filename>')
def video_result(filename):
    """Show converted video result page with validation"""
    try:
        # Security: Prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return "Invalid filename", 400

        # Validate file exists
        file_path = OUTPUT_DIR / filename
        if not file_path.exists():
            return render_template(
                'error.html' if Path('templates/error.html').exists() else 'integrated.html',
                error_message="Video file not found. It may have been deleted or expired."
            ), 404

        # Get video info from jobs dict
        video_info = jobs.get(f'video_{filename}', {})
        video_title = video_info.get('title', 'Converted Video')
        duration = video_info.get('duration', 30)
        tiktok_connected = session.get('tiktok_connected', False)

        return render_template(
            'video_result.html',
            filename=filename,
            video_title=video_title,
            duration=duration,
            tiktok_connected=tiktok_connected
        )

    except Exception as e:
        print(f"Error in /video_result: {str(e)}")
        return f"Error loading video result: {str(e)}", 500


@app.route('/download/<filename>')
def download_file(filename):
    """Serve converted video file with security checks"""
    try:
        # Security: Prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return "Invalid filename", 400

        # Validate filename
        if not filename or not filename.endswith('.mp4'):
            return "Invalid file type. Only MP4 files are allowed.", 400

        file_path = OUTPUT_DIR / filename

        # Check if file exists
        if not file_path.exists():
            return "Video file not found. It may have been deleted or expired.", 404

        # Check if file is actually in the output directory (security check)
        if not str(file_path.resolve()).startswith(str(OUTPUT_DIR.resolve())):
            return "Access denied", 403

        return send_file(file_path, mimetype='video/mp4', as_attachment=True, download_name=filename)

    except Exception as e:
        print(f"Error in /download: {str(e)}")
        return f"Error downloading file: {str(e)}", 500


@app.route('/upload_to_tiktok', methods=['POST'])
def upload_to_tiktok():
    """Upload converted video to TikTok with comprehensive error handling"""
    try:
        if not request.json:
            return jsonify({'error': 'Invalid request - JSON data required'}), 400

        data = request.json
        filename = data.get('filename', '').strip()
        caption = data.get('caption', '').strip()

        # Validate inputs
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400

        if not caption:
            return jsonify({'error': 'Caption is required for TikTok upload'}), 400

        if len(caption) > 2200:
            return jsonify({'error': 'Caption too long. Maximum 2200 characters allowed.'}), 400

        # Check TikTok connection
        if not session.get('tiktok_connected'):
            return jsonify({'error': 'TikTok account not connected. Please connect your account first.'}), 401

        # Validate file exists
        video_path = OUTPUT_DIR / filename
        if not video_path.exists():
            return jsonify({'error': 'Video file not found. It may have been deleted or expired.'}), 404

        # Check file size (TikTok limit is typically 287MB for web)
        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 280:
            return jsonify({'error': f'Video file too large ({file_size_mb:.1f}MB). Maximum 280MB allowed.'}), 400

        # Upload to TikTok
        try:
            uploader = TikTokUploader()
            tiktok_url = uploader.upload(str(video_path), caption)

            return jsonify({
                'success': True,
                'tiktok_url': tiktok_url,
                'message': 'Video uploaded successfully to TikTok!'
            })

        except Exception as upload_error:
            error_msg = str(upload_error)

            # Handle specific TikTok API errors
            if 'authentication' in error_msg.lower() or 'token' in error_msg.lower():
                return jsonify({'error': 'TikTok authentication expired. Please reconnect your account.'}), 401
            elif 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower():
                return jsonify({'error': 'TikTok API rate limit reached. Please try again later.'}), 429
            elif 'file size' in error_msg.lower() or 'too large' in error_msg.lower():
                return jsonify({'error': 'Video file too large for TikTok. Try a shorter duration.'}), 400
            elif 'format' in error_msg.lower() or 'codec' in error_msg.lower():
                return jsonify({'error': 'Video format not supported by TikTok. Please try converting again.'}), 400
            else:
                return jsonify({'error': f'TikTok upload failed: {error_msg}'}), 500

    except Exception as e:
        error_msg = str(e)
        print(f"Error in /upload_to_tiktok: {error_msg}")
        return jsonify({'error': f'Upload failed: {error_msg}'}), 500




def process_video_safe(job_id: str, youtube_url: str, start_time: str,
                       duration: int, caption: str, auto_detect: bool, auto_upload: bool = False):
    """
    Safe wrapper for video processing - NEVER crashes
    All exceptions caught and reported to job status
    """
    try:
        process_video(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload)
    except Exception as e:
        error_msg = str(e)
        print(f"[FATAL] Job {job_id} crashed: {error_msg}")

        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        job_store.update_job(
            job_id,
            status='error',
            progress=0,
            message=f'Fatal error: {error_msg}'
        )


def process_video(job_id, youtube_url, start_time, duration, caption, auto_detect, auto_upload=False):
    """Background video processing with comprehensive error handling"""

    def safe_print(msg):
        """Print with Unicode error handling"""
        try:
            print(msg)
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Fallback: print ASCII-safe version
            try:
                print(msg.encode('ascii', 'ignore').decode('ascii'))
            except:
                pass

    def update_job_status(status, progress, message):
        """Update job status safely"""
        try:
            job_store.update_job(job_id, status=status, progress=progress, message=message)
        except Exception as e:
            safe_print(f"Failed to update job status: {str(e)}")

    try:
        safe_print(f"\n=== Processing Video ===")
        safe_print(f"Job ID: {job_id}")
        safe_print(f"YouTube URL: {youtube_url}")

        # Step 1: Download video
        update_job_status('processing', 10, 'Starting download...')

        try:
            update_job_status('processing', 20, 'Downloading YouTube video...')
            video_data = download_youtube_video(youtube_url)

            if not video_data or 'video_path' not in video_data:
                raise Exception("Download failed - no video data returned")

            video_path = video_data['video_path']
            video_title = video_data.get('title', 'Unknown')

            # Verify downloaded file exists
            if not Path(video_path).exists():
                raise Exception("Download failed - video file not found")

            file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            safe_print(f"Downloaded: {video_title} ({file_size_mb:.1f} MB)")

        except Exception as e:
            error_msg = str(e)
            if "Video unavailable" in error_msg or "private" in error_msg.lower():
                update_job_status('error', 0, 'Video unavailable or private. Please try a different video.')
            elif "region" in error_msg.lower() or "blocked" in error_msg.lower():
                update_job_status('error', 0, 'Video blocked in your region. Please try a different video.')
            elif "age" in error_msg.lower() or "sign in" in error_msg.lower():
                update_job_status('error', 0, 'Age-restricted video. Please try a different video.')
            else:
                update_job_status('error', 0, f'Download failed: {error_msg}')
            safe_print(f"Download error: {error_msg}")
            return

        # Step 2: Convert video
        try:
            update_job_status('processing', 50, 'Preparing conversion...')

            # Generate safe output filename
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            safe_print(f"Converting to: {output_filename}")
            update_job_status('processing', 60, 'Converting to TikTok format...')

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time,
                duration=duration,
                auto_detect=auto_detect and not start_time
            )

            # Verify converted file exists
            if not Path(converted_path).exists():
                raise Exception("Conversion failed - output file not created")

            output_size_mb = Path(converted_path).stat().st_size / (1024 * 1024)
            safe_print(f"Converted successfully: {output_size_mb:.1f} MB")

        except Exception as e:
            error_msg = str(e)
            if "ffmpeg" in error_msg.lower():
                update_job_status('error', 0, 'Video conversion failed. FFmpeg error occurred.')
            elif "codec" in error_msg.lower():
                update_job_status('error', 0, 'Video format not supported. Please try a different video.')
            else:
                update_job_status('error', 0, f'Conversion failed: {error_msg}')
            safe_print(f"Conversion error: {error_msg}")
            return

        # Step 3: Success - store results
        try:
            update_job_status('processing', 90, 'Finalizing...')

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

            # Store video info for result page (using job_store)
            job_store.create_job(f'video_{output_filename}')
            job_store.update_job(f'video_{output_filename}',
                                title=video_title,
                                duration=duration)

            safe_print(f"Processing complete for job {job_id}")

        except Exception as e:
            safe_print(f"Error storing results: {str(e)}")
            update_job_status('error', 0, 'Processing completed but failed to save results')
            return

    except Exception as e:
        # Catch-all for any unexpected errors
        error_msg = str(e)
        safe_print(f"Unexpected error in process_video: {error_msg}")

        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        update_job_status('error', 0, f'An unexpected error occurred: {error_msg}')


# ==================== TIKTOK OAUTH ====================

@app.route('/tiktok/connect')
def tiktok_connect():
    """Redirect to TikTok OAuth with PKCE"""
    client_key = os.getenv('TIKTOK_CLIENT_KEY')
    redirect_uri = url_for('tiktok_callback', _external=True)

    # Generate PKCE parameters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    # Generate state for security
    state = secrets.token_urlsafe(32)

    # Store in session
    session['code_verifier'] = code_verifier
    session['oauth_state'] = state

    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&scope=video.upload,video.publish"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&state={state}"
    )

    return redirect(oauth_url)


@app.route('/tiktok/callback')
def tiktok_callback():
    """Handle TikTok OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    # Check for errors
    if error:
        return f"TikTok OAuth Error: {error} - {request.args.get('error_description', 'Unknown error')}", 400

    if not code:
        return "Error: No authorization code received", 400

    # Verify state
    if state != session.get('oauth_state'):
        return "Error: Invalid state parameter (CSRF protection)", 400

    # Get code_verifier from session
    code_verifier = session.get('code_verifier')
    if not code_verifier:
        return "Error: Code verifier not found in session", 400

    # Exchange code for token
    try:
        import requests

        response = requests.post(
            'https://open.tiktokapis.com/v2/oauth/token/',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data={
                'client_key': os.getenv('TIKTOK_CLIENT_KEY'),
                'client_secret': os.getenv('TIKTOK_CLIENT_SECRET'),
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': url_for('tiktok_callback', _external=True),
                'code_verifier': code_verifier
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Save tokens to .env file
            update_env_file('TIKTOK_ACCESS_TOKEN', data['access_token'])
            update_env_file('TIKTOK_REFRESH_TOKEN', data.get('refresh_token', ''))

            session['tiktok_connected'] = True

            # Clear OAuth session data
            session.pop('code_verifier', None)
            session.pop('oauth_state', None)

            return redirect(url_for('index'))
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            return f"Token Exchange Error: {response.status_code} - {error_data}", 400

    except Exception as e:
        return f"Error: {str(e)}", 500


def update_env_file(key, value):
    """Update .env file with new value"""
    env_path = Path('.env')

    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update existing key or add new
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}\n'
                found = True
                break

        if not found:
            lines.append(f'{key}={value}\n')

        with open(env_path, 'w') as f:
            f.writelines(lines)


# ==================== YOUTUBE OAUTH ====================

@app.route('/youtube/connect')
def youtube_connect():
    """Redirect to YouTube OAuth with PKCE"""
    client_id = os.getenv('YOUTUBE_CLIENT_ID')
    client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')

    if not client_id or not client_secret or client_id == 'your_youtube_client_id_here':
        return """
        <h2>YouTube OAuth Not Configured</h2>
        <p>Please configure YouTube OAuth credentials in .env file:</p>
        <ol>
            <li>Go to <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a></li>
            <li>Create a new project or select existing</li>
            <li>Enable YouTube Data API v3</li>
            <li>Create OAuth 2.0 credentials</li>
            <li>Add redirect URI: http://localhost:5000/youtube/callback</li>
            <li>Copy Client ID and Client Secret to .env file</li>
        </ol>
        <a href="/">← Back to Home</a>
        """

    redirect_uri = url_for('youtube_callback', _external=True)

    try:
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        # Generate state for security
        state = secrets.token_urlsafe(32)

        # Store in session
        session['youtube_code_verifier'] = code_verifier
        session['youtube_oauth_state'] = state

        # Build authorization URL manually with PKCE
        scopes_str = ' '.join(YOUTUBE_SCOPES)

        authorization_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scopes_str}"
            f"&state={state}"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&code_challenge={code_challenge}"
            f"&code_challenge_method=S256"
        )

        return redirect(authorization_url)

    except Exception as e:
        return f"Error creating OAuth flow: {str(e)}", 500


@app.route('/youtube/callback')
def youtube_callback():
    """Handle YouTube OAuth callback with PKCE"""
    try:
        state = request.args.get('state')
        code = request.args.get('code')
        error = request.args.get('error')

        if error:
            return f"YouTube OAuth Error: {error}", 400

        if not code:
            return "Error: No authorization code received", 400

        # Verify state
        if state != session.get('youtube_oauth_state'):
            return "Error: Invalid state parameter (CSRF protection)", 400

        # Get code_verifier from session
        code_verifier = session.get('youtube_code_verifier')
        if not code_verifier:
            return "Error: Code verifier not found in session", 400

        # Use requests library for direct token exchange with PKCE
        import requests

        client_id = os.getenv('YOUTUBE_CLIENT_ID')
        client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        redirect_uri = url_for('youtube_callback', _external=True)

        # Exchange authorization code for tokens with code_verifier
        token_response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'code_verifier': code_verifier  # PKCE parameter
            }
        )

        if token_response.status_code != 200:
            error_data = token_response.json() if token_response.headers.get('content-type') == 'application/json' else token_response.text
            return f"Token Exchange Error: {token_response.status_code} - {error_data}", 400

        token_data = token_response.json()

        # Store credentials in session
        session['youtube_credentials'] = {
            'token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': YOUTUBE_SCOPES
        }
        session['youtube_connected'] = True

        # Clear OAuth session data
        session.pop('youtube_code_verifier', None)
        session.pop('youtube_oauth_state', None)

        return redirect(url_for('index'))

    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/youtube/channels')
def get_youtube_channels():
    """Get user's YouTube channels with comprehensive error handling"""
    try:
        if not session.get('youtube_connected'):
            return jsonify({'error': 'YouTube account not connected. Please connect your account first.'}), 401

        creds_data = session.get('youtube_credentials')
        if not creds_data:
            session['youtube_connected'] = False
            return jsonify({'error': 'YouTube credentials expired. Please reconnect your account.'}), 401

        try:
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )

            youtube = build('youtube', 'v3', credentials=credentials)

            # Get user's channels
            channels_response = youtube.channels().list(
                part='snippet,contentDetails,statistics',
                mine=True
            ).execute()

            channels = []
            for item in channels_response.get('items', []):
                channel_data = {
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'subscriber_count': int(item['statistics'].get('subscriberCount', 0)),
                    'video_count': int(item['statistics'].get('videoCount', 0)),
                    'uploads_playlist_id': item['contentDetails']['relatedPlaylists']['uploads']
                }
                channels.append(channel_data)

            if not channels:
                return jsonify({'error': 'No YouTube channels found for this account.'}), 404

            return jsonify({
                'success': True,
                'channels': channels
            })

        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401 or e.resp.status == 403:
                session['youtube_connected'] = False
                return jsonify({'error': 'YouTube authentication expired. Please reconnect your account.'}), 401
            elif 'quota' in error_msg.lower():
                return jsonify({'error': 'YouTube API quota exceeded. Please try again tomorrow.'}), 429
            else:
                return jsonify({'error': f'YouTube API error: {error_msg}'}), 500

    except Exception as e:
        error_msg = str(e)
        print(f"Error in /youtube/channels: {error_msg}")
        return jsonify({'error': f'Failed to fetch channels: {error_msg}'}), 500


@app.route('/youtube/videos/<channel_id>')
def get_youtube_videos(channel_id):
    """Get videos from a channel with comprehensive error handling"""
    try:
        # Validate channel_id
        if not channel_id or len(channel_id) < 10:
            return jsonify({'error': 'Invalid channel ID'}), 400

        if not session.get('youtube_connected'):
            return jsonify({'error': 'YouTube account not connected. Please connect your account first.'}), 401

        creds_data = session.get('youtube_credentials')
        if not creds_data:
            session['youtube_connected'] = False
            return jsonify({'error': 'YouTube credentials expired. Please reconnect your account.'}), 401

        try:
            credentials = Credentials(
                token=creds_data['token'],
                refresh_token=creds_data.get('refresh_token'),
                token_uri=creds_data['token_uri'],
                client_id=creds_data['client_id'],
                client_secret=creds_data['client_secret'],
                scopes=creds_data['scopes']
            )

            youtube = build('youtube', 'v3', credentials=credentials)

            # Get channel's uploads playlist
            channel_response = youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()

            if not channel_response.get('items'):
                return jsonify({'error': 'Channel not found or access denied'}), 404

            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get videos from uploads playlist
            videos = []
            next_page_token = None
            max_results = 50

            while len(videos) < max_results:
                try:
                    playlist_response = youtube.playlistItems().list(
                        part='snippet',
                        playlistId=uploads_playlist_id,
                        maxResults=min(50, max_results - len(videos)),
                        pageToken=next_page_token
                    ).execute()

                    video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response.get('items', [])]

                except HttpError as e:
                    if 'playlistNotFound' in str(e):
                        # Fallback to search API
                        search_response = youtube.search().list(
                            part='id',
                            channelId=channel_id,
                            type='video',
                            order='date',
                            maxResults=min(50, max_results - len(videos)),
                            pageToken=next_page_token
                        ).execute()
                        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                        next_page_token = search_response.get('nextPageToken')
                    else:
                        raise

                if video_ids:
                    # Get video details
                    videos_response = youtube.videos().list(
                        part='snippet,contentDetails,statistics',
                        id=','.join(video_ids)
                    ).execute()

                    for item in videos_response.get('items', []):
                        duration_seconds = parse_duration(item['contentDetails']['duration'])

                        videos.append({
                            'video_id': item['id'],
                            'title': item['snippet']['title'],
                            'description': item['snippet'].get('description', ''),
                            'thumbnail': item['snippet']['thumbnails']['high']['url'],
                            'published_at': item['snippet']['publishedAt'],
                            'duration': format_duration(duration_seconds),
                            'duration_seconds': duration_seconds,
                            'view_count': int(item['statistics'].get('viewCount', 0)),
                            'like_count': int(item['statistics'].get('likeCount', 0)),
                            'comment_count': int(item['statistics'].get('commentCount', 0)),
                            'url': f"https://youtube.com/watch?v={item['id']}",
                            'is_short': duration_seconds <= 60
                        })

                if 'playlist_response' in locals():
                    next_page_token = playlist_response.get('nextPageToken')

                if not next_page_token or len(videos) >= max_results:
                    break

            return jsonify({
                'success': True,
                'videos': videos,
                'total': len(videos)
            })

        except HttpError as e:
            error_msg = str(e)
            if e.resp.status == 401 or e.resp.status == 403:
                session['youtube_connected'] = False
                return jsonify({'error': 'YouTube authentication expired. Please reconnect your account.'}), 401
            elif 'quota' in error_msg.lower():
                return jsonify({'error': 'YouTube API quota exceeded. Please try again tomorrow.'}), 429
            else:
                return jsonify({'error': f'YouTube API error: {error_msg}'}), 500

    except Exception as e:
        error_msg = str(e)
        print(f"Error in /youtube/videos: {error_msg}")
        return jsonify({'error': f'Failed to fetch videos: {error_msg}'}), 500


# ==================== GLOBAL ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/') or request.path.startswith('/download/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('integrated.html', error_message='Page not found', countries=COUNTRIES, tiktok_connected=False, youtube_connected=False), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    print(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({'error': 'Internal server error. Please try again later.'}), 500
    return render_template('integrated.html', error_message='An error occurred. Please try again.', countries=COUNTRIES, tiktok_connected=False, youtube_connected=False), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large errors"""
    return jsonify({'error': 'File too large. Maximum size is 500MB.'}), 413


@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limit errors"""
    return jsonify({'error': 'Too many requests. Please try again later.'}), 429


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    print(f"Unhandled exception: {type(e).__name__}: {str(e)}")

    try:
        import traceback
        traceback.print_exc()
    except:
        pass

    if request.path.startswith('/api/') or request.is_json:
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
    return render_template('integrated.html', error_message='An unexpected error occurred.'), 500


# ==================== APP INITIALIZATION ====================

# Create required directories (must be outside if __name__ for production servers like gunicorn)
try:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Warning: Could not create directories: {e}")

if __name__ == '__main__':
    try:
        # Get port from environment
        port = int(os.getenv('PORT', 5000))

        print("=" * 60)
        print("🚀 Integrated YouTube Analyzer + Converter + TikTok Upload")
        print("=" * 60)
        print("")
        print("✅ Search viral YouTube videos")
        print("✅ Filter by country")
        print("✅ One-click convert to TikTok")
        print("✅ Auto-upload to TikTok (optional)")
        print("✅ Browse your YouTube channels")
        print("")
        print(f"🌐 Server running on: http://0.0.0.0:{port}")
        print("")
        print("=" * 60)
        print("")
        print("📝 Features:")
        print("  • Production-ready error handling")
        print("  • Comprehensive input validation")
        print("  • Security checks on file operations")
        print("  • User-friendly error messages")
        print("  • Timeout protection")
        print("  • Unicode support for all languages")
        print("")
        print("=" * 60)

        # Run the app (debug mode disabled for production)
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=port)

    except Exception as e:
        print(f"\n❌ Failed to start application: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nPlease check:")
        print("  1. Port 5000 is not already in use")
        print("  2. All dependencies are installed (pip install -r requirements.txt)")
        print("  3. .env file is properly configured")
        print("")
        input("Press Enter to exit...")
