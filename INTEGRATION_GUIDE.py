# Production Fixes for integrated_app.py
# Replace sections in your integrated_app.py file

# ============================================================================
# SECTION 1: IMPORTS (add these at the top, after existing imports)
# ============================================================================

from job_store import JobStore

# Replace the downloader import:
# OLD: from yt2tik.downloader import download_youtube_video
# NEW:
try:
    from yt2tik.downloader_fixed import download_youtube_video, cleanup_old_downloads
    print("✅ Using fixed production downloader")
except ImportError:
    from yt2tik.downloader import download_youtube_video
    print("⚠️  Using original downloader (not production-ready)")


# ============================================================================
# SECTION 2: REPLACE JOBS DICT (around line 88)
# ============================================================================

# OLD: jobs = {}
# NEW:
job_store = JobStore(ttl_seconds=3600, max_jobs=1000)


# ============================================================================
# SECTION 3: UPDATE /convert ENDPOINT (replace entire function)
# ============================================================================

@app.route('/convert', methods=['POST'])
def convert():
    """Convert YouTube video to TikTok format with comprehensive validation"""
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
                parts = start_time.split(':')
                if len(parts) > 3 or len(parts) < 1:
                    raise ValueError("Invalid format")
                for part in parts:
                    int(part)
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
            'message': 'Processing started successfully',
            'status_url': f'/status/{job_id}'
        }), 202

    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] /convert endpoint: {error_msg}")
        return jsonify({
            'error': 'Server error occurred',
            'details': error_msg
        }), 500


# ============================================================================
# SECTION 4: UPDATE /status ENDPOINT (replace entire function)
# ============================================================================

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


# ============================================================================
# SECTION 5: ADD SAFE WRAPPER FOR BACKGROUND PROCESSING
# ============================================================================

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


# ============================================================================
# SECTION 6: UPDATE process_video FUNCTION (replace entire function)
# ============================================================================

def process_video(job_id: str, youtube_url: str, start_time: str,
                  duration: int, caption: str, auto_detect: bool, auto_upload: bool = False):
    """
    Background video processing with comprehensive error handling and logging
    """

    def update(status, progress, message, **kwargs):
        """Helper to update job status"""
        job_store.update_job(job_id, status=status, progress=progress, message=message, **kwargs)
        print(f"[{job_id[:8]}] {progress}% - {message}")

    video_path = None

    try:
        print(f"\n[JOB START] {job_id}")
        print(f"[URL] {youtube_url}")
        print(f"[DURATION] {duration}s")

        update('processing', 5, 'Starting download...')

        # ===== STEP 1: Download YouTube video =====
        try:
            update('processing', 10, 'Downloading from YouTube...')
            print(f"[DOWNLOAD] Starting YouTube download...")

            video_data = download_youtube_video(youtube_url, max_retries=2)

            if not video_data or 'video_path' not in video_data:
                raise Exception("Download failed - no video data returned")

            video_path = video_data['video_path']
            video_title = video_data.get('title', 'Unknown')
            video_duration = video_data.get('duration', 0)

            # Verify downloaded file exists
            if not Path(video_path).exists():
                raise Exception("Download failed - video file not found")

            file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
            print(f"[SUCCESS] Downloaded: {video_title} ({file_size_mb:.1f}MB)")

            update('processing', 30, f'Downloaded: {video_title[:50]}...')

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Download failed: {error_msg}")

            # Categorize errors for user-friendly messages
            if any(keyword in error_msg.lower() for keyword in ['sign-in', 'login', 'age-restricted']):
                update('error', 0, '❌ Video requires sign-in (age-restricted or members-only)')
            elif 'private' in error_msg.lower():
                update('error', 0, '❌ Video is private and cannot be accessed')
            elif any(keyword in error_msg.lower() for keyword in ['unavailable', 'deleted']):
                update('error', 0, '❌ Video unavailable (deleted or region-blocked)')
            elif 'rate limit' in error_msg.lower():
                update('error', 0, '❌ Rate limit reached. Try again in a few minutes')
            elif 'timeout' in error_msg.lower():
                update('error', 0, '❌ Download timeout. Try a shorter video')
            else:
                update('error', 0, f'❌ Download failed: {error_msg}')

            return

        # ===== STEP 2: Convert to TikTok format =====
        try:
            update('processing', 40, 'Converting to TikTok format...')
            print(f"[CONVERT] Starting conversion...")

            # Generate safe output filename
            safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))[:50]
            output_filename = f"tiktok_{safe_title}_{job_id[:8]}.mp4"

            update('processing', 50, 'Processing video...')

            converted_path = convert_to_tiktok_format(
                input_path=video_path,
                output_filename=output_filename,
                start_time=start_time if start_time else None,
                duration=duration,
                auto_detect=auto_detect and not start_time
            )

            # Verify converted file exists
            if not Path(converted_path).exists():
                raise Exception("Conversion completed but output file not created")

            output_size_mb = Path(converted_path).stat().st_size / (1024 * 1024)
            print(f"[SUCCESS] Converted: {output_size_mb:.1f}MB")

            update('processing', 90, 'Finalizing...')

        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Conversion failed: {error_msg}")

            if 'ffmpeg' in error_msg.lower():
                update('error', 0, '❌ Video conversion failed (FFmpeg error)')
            elif 'codec' in error_msg.lower():
                update('error', 0, '❌ Video format not supported')
            else:
                update('error', 0, f'❌ Conversion failed: {error_msg}')

            return

        # ===== STEP 3: Success =====
        try:
            print(f"[SUCCESS] Job {job_id} completed")

            job_store.update_job(
                job_id,
                status='completed',
                progress=100,
                message='✅ Conversion complete!',
                video_title=video_title,
                filename=output_filename,
                video_url=f'/download/{output_filename}',
                redirect_url=f'/video_result/{output_filename}',
                file_size_mb=round(output_size_mb, 1),
                duration=duration
            )

        except Exception as e:
            print(f"[ERROR] Failed to save results: {str(e)}")
            update('error', 0, 'Processing completed but failed to save results')
            return

    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = str(e)
        print(f"[FATAL] Unexpected error: {error_msg}")

        try:
            import traceback
            traceback.print_exc()
        except:
            pass

        update('error', 0, f'❌ Unexpected error: {error_msg}')

    finally:
        # Cleanup: delete downloaded video (keep converted)
        try:
            if video_path and Path(video_path).exists():
                Path(video_path).unlink()
                print(f"[CLEANUP] Deleted source: {video_path}")
        except Exception as e:
            print(f"[CLEANUP] Warning: {str(e)}")


# ============================================================================
# SECTION 7: UPDATE __main__ BLOCK (replace at bottom of file)
# ============================================================================

if __name__ == '__main__':
    try:
        # Create required directories
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Cleanup old downloads on startup
        try:
            cleanup_old_downloads(days=1)
        except:
            pass

        # Get port from environment (Railway compatible)
        port = int(os.getenv('PORT', 7860))

        print("=" * 60)
        print("🚀 YouTube to TikTok Converter - Production")
        print("=" * 60)
        print(f"📦 Downloader: Fixed version with retry logic")
        print(f"📊 Job Store: Thread-safe with TTL")
        print(f"🌐 Server: http://0.0.0.0:{port}")
        print("=" * 60)

        # Run app (Gunicorn will use this for production)
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(debug=debug_mode, host='0.0.0.0', port=port)

    except Exception as e:
        print(f"\n❌ Failed to start application: {str(e)}")
        import traceback
        traceback.print_exc()
