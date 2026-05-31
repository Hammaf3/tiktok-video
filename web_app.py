"""
Flask Web Application for YouTube to TikTok Converter
Simple interface for clients - no API knowledge needed
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
import uuid

# Import your existing modules
from yt2tik.downloader import download_youtube_video
from yt2tik.converter import convert_to_tiktok_format
from yt2tik.caption_gen import generate_caption
from yt2tik.uploader import TikTokUploader

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key')

# Store job status in memory (use Redis for production)
jobs = {}


@app.route('/')
def index():
    """Main page"""
    tiktok_connected = session.get('tiktok_connected', False)
    return render_template('index.html', tiktok_connected=tiktok_connected)


@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video to TikTok"""
    try:
        data = request.json
        youtube_url = data.get('youtube_url')
        start_time = data.get('start_time')
        duration = int(data.get('duration', 30))
        caption = data.get('caption')
        auto_detect = data.get('auto_detect', False)

        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        # Create unique job ID
        job_id = str(uuid.uuid4())
        jobs[job_id] = {'status': 'processing', 'progress': 0, 'message': 'Starting...'}

        # Process in background thread
        thread = threading.Thread(
            target=process_video,
            args=(job_id, youtube_url, start_time, duration, caption, auto_detect)
        )
        thread.start()

        return jsonify({'job_id': job_id, 'message': 'Processing started'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(jobs[job_id])


@app.route('/tiktok/connect')
def tiktok_connect():
    """Redirect to TikTok OAuth with PKCE"""
    import hashlib
    import base64
    import secrets

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

            # Save tokens to .env file (simple approach)
            # For production, use database
            update_env_file('TIKTOK_ACCESS_TOKEN', data['access_token'])
            update_env_file('TIKTOK_REFRESH_TOKEN', data.get('refresh_token', ''))

            session['tiktok_connected'] = True

            # Clear OAuth session data
            session.pop('code_verifier', None)
            session.pop('oauth_state', None)

            return render_template('success.html')
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            return f"Token Exchange Error: {response.status_code} - {error_data}", 400

    except Exception as e:
        return f"Error: {str(e)}", 500


def process_video(job_id, youtube_url, start_time, duration, caption, auto_detect):
    """Background task to process video"""
    try:
        # Step 1: Download
        jobs[job_id] = {'status': 'processing', 'progress': 20, 'message': 'Downloading YouTube video...'}
        video_data = download_youtube_video(youtube_url)

        # Step 2: Convert
        jobs[job_id] = {'status': 'processing', 'progress': 40, 'message': 'Converting to TikTok format...'}
        output_filename = f"tiktok_{Path(video_data['video_path']).stem}.mp4"
        converted_path = convert_to_tiktok_format(
            input_path=video_data['video_path'],
            output_filename=output_filename,
            start_time=start_time,
            duration=duration,
            auto_detect=auto_detect and not start_time
        )

        # Step 3: Generate caption
        jobs[job_id] = {'status': 'processing', 'progress': 60, 'message': 'Generating caption...'}
        if not caption:
            caption = generate_caption(
                title=video_data['title'],
                description=video_data['description']
            )

        # Step 4: Upload to TikTok
        jobs[job_id] = {'status': 'processing', 'progress': 80, 'message': 'Uploading to TikTok...'}
        uploader = TikTokUploader()
        video_url = uploader.upload(converted_path, caption)

        # Success
        jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Upload complete!',
            'tiktok_url': video_url,
            'video_title': video_data['title']
        }

    except Exception as e:
        jobs[job_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }


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


if __name__ == '__main__':
    # Create necessary directories
    Path('tmp/yt2tik/downloads').mkdir(parents=True, exist_ok=True)
    Path('tmp/yt2tik/output').mkdir(parents=True, exist_ok=True)

    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
