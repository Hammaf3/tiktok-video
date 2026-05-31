"""
Simple Web App - No TikTok OAuth Required
Converts videos and provides download link for manual upload
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
from pathlib import Path
from dotenv import load_dotenv
import threading
import uuid

# Import your existing modules
from yt2tik.downloader import download_youtube_video
from yt2tik.converter import convert_to_tiktok_format
from yt2tik.caption_gen import generate_caption

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-this-secret-key')

# Store job status
jobs = {}


@app.route('/')
def index():
    """Main page - simple version without OAuth"""
    return render_template('simple.html')


@app.route('/convert_only', methods=['POST'])
def convert_only():
    """Convert video without uploading to TikTok"""
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
            target=process_video_only,
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


@app.route('/download/<filename>')
def download_file(filename):
    """Download converted video"""
    try:
        file_path = Path('tmp/yt2tik/output') / filename
        if not file_path.exists():
            return "File not found", 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


def process_video_only(job_id, youtube_url, start_time, duration, caption, auto_detect):
    """Background task to process video (no upload)"""
    try:
        # Step 1: Download
        jobs[job_id] = {'status': 'processing', 'progress': 25, 'message': 'Downloading YouTube video...'}
        video_data = download_youtube_video(youtube_url)

        # Step 2: Convert
        jobs[job_id] = {'status': 'processing', 'progress': 50, 'message': 'Converting to TikTok format...'}
        output_filename = f"tiktok_{Path(video_data['video_path']).stem}.mp4"
        converted_path = convert_to_tiktok_format(
            input_path=video_data['video_path'],
            output_filename=output_filename,
            start_time=start_time,
            duration=duration,
            auto_detect=auto_detect and not start_time
        )

        # Step 3: Generate caption
        jobs[job_id] = {'status': 'processing', 'progress': 75, 'message': 'Generating caption...'}
        if not caption:
            caption = generate_caption(
                title=video_data['title'],
                description=video_data['description']
            )

        # Success
        jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Conversion complete!',
            'video_title': video_data['title'],
            'duration': duration,
            'caption': caption,
            'filename': output_filename
        }

    except Exception as e:
        jobs[job_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Error: {str(e)}'
        }


if __name__ == '__main__':
    # Create necessary directories
    Path('tmp/yt2tik/downloads').mkdir(parents=True, exist_ok=True)
    Path('tmp/yt2tik/output').mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("🎬 Simple YouTube to TikTok Converter")
    print("="*60)
    print("")
    print("✅ No TikTok OAuth required")
    print("✅ Converts videos to TikTok format")
    print("✅ Provides download link")
    print("✅ Manual upload to TikTok")
    print("")
    print("Open in browser: http://localhost:5000")
    print("")
    print("="*60)

    # Run app
    app.run(debug=True, host='0.0.0.0', port=5000)
