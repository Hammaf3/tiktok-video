"""
Automated Integration Script - Applies Production Fixes to integrated_app.py
This script updates integrated_app.py to use JobStore instead of jobs dict
"""
import re
import sys
from pathlib import Path

def apply_fixes():
    """Apply all production fixes to integrated_app.py"""

    file_path = Path('integrated_app.py')

    if not file_path.exists():
        print("[ERROR] integrated_app.py not found")
        return False

    print("=" * 60)
    print("Applying Production Fixes to integrated_app.py")
    print("=" * 60)

    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # Fix 1: Update /convert endpoint - job creation
    print("\n[FIX 1] Updating /convert endpoint - job creation...")
    old_pattern = r"""        # Create job
        job_id = str\(uuid\.uuid4\(\)\)
        jobs\[job_id\] = \{
            'status': 'processing',
            'progress': 0,
            'message': 'Initializing\.\.\.',
            'created_at': datetime\.now\(\)\.isoformat\(\)
        \}"""

    new_code = """        # Create job using JobStore
        job_id = str(uuid.uuid4())
        job_store.create_job(job_id)
        job_store.update_job(job_id, status='queued', progress=0, message='Queued for processing')

        print(f"[JOB] Created: {job_id}")"""

    if old_pattern in content or 'jobs[job_id] = {' in content:
        # Use a simpler replacement
        content = content.replace(
            """        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            'status': 'processing',
            'progress': 0,
            'message': 'Initializing...',
            'created_at': datetime.now().isoformat()
        }""",
            new_code
        )
        if content != original_content:
            changes_made.append("Job creation in /convert")
            print("[DONE] Job creation updated")
        else:
            print("[SKIP] Pattern not found or already updated")

    # Fix 2: Update /convert endpoint - thread target
    print("\n[FIX 2] Updating /convert endpoint - thread target...")
    content = content.replace(
        "target=process_video,",
        "target=process_video_safe,"
    )
    if "target=process_video_safe," in content:
        changes_made.append("Thread target to process_video_safe")
        print("[DONE] Thread target updated")

    # Fix 3: Update /convert endpoint - return statement
    print("\n[FIX 3] Updating /convert endpoint - return statement...")
    content = content.replace(
        """        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Processing started successfully'
        })""",
        """        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Processing started successfully',
            'status_url': f'/status/{job_id}'
        }), 202"""
    )
    if "'status_url':" in content:
        changes_made.append("Return statement with status_url")
        print("[DONE] Return statement updated")

    # Fix 4: Update /status endpoint
    print("\n[FIX 4] Updating /status endpoint...")
    old_status = """    try:
        if not job_id:
            return jsonify({'error': 'Job ID is required'}), 400

        if job_id not in jobs:
            return jsonify({'error': 'Job not found. It may have expired or never existed.'}), 404

        job_data = jobs[job_id]

        # Check if job is stuck (processing for more than 5 minutes)
        if job_data.get('status') == 'processing':
            created_at = job_data.get('created_at')
            if created_at:
                try:
                    from datetime import datetime
                    created_time = datetime.fromisoformat(created_at)
                    elapsed = (datetime.now() - created_time).total_seconds()

                    if elapsed > 300:  # 5 minutes
                        job_data['status'] = 'error'
                        job_data['message'] = 'Processing timeout. Please try again with a shorter video.'
                        job_data['progress'] = 0
                except:
                    pass

        return jsonify(job_data), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500"""

    new_status = """    try:
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
        }), 500"""

    if "if job_id not in jobs:" in content:
        content = content.replace(old_status, new_status)
        changes_made.append("/status endpoint logic")
        print("[DONE] /status endpoint updated")
    else:
        print("[SKIP] /status already updated or pattern not found")

    # Fix 5: Add process_video_safe wrapper
    print("\n[FIX 5] Adding process_video_safe wrapper...")
    if "def process_video_safe" not in content:
        # Find the location before process_video function
        process_video_location = content.find("def process_video(job_id,")
        if process_video_location > 0:
            safe_wrapper = '''

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


'''
            content = content[:process_video_location] + safe_wrapper + content[process_video_location:]
            changes_made.append("process_video_safe wrapper")
            print("[DONE] process_video_safe wrapper added")
    else:
        print("[SKIP] process_video_safe already exists")

    # Fix 6: Update update_job_status helper in process_video
    print("\n[FIX 6] Updating update_job_status helper...")
    content = content.replace(
        """    def update_job_status(status, progress, message):
        \"\"\"Update job status safely\"\"\"
        try:
            jobs[job_id] = {
                'status': status,
                'progress': progress,
                'message': message
            }
        except Exception as e:
            safe_print(f\"Failed to update job status: {str(e)}\")""",
        """    def update_job_status(status, progress, message):
        \"\"\"Update job status safely\"\"\"
        try:
            job_store.update_job(job_id, status=status, progress=progress, message=message)
        except Exception as e:
            safe_print(f\"Failed to update job status: {str(e)}\")"""
    )
    if "job_store.update_job(job_id, status=status" in content:
        changes_made.append("update_job_status helper")
        print("[DONE] update_job_status updated")

    # Fix 7: Update success case in process_video
    print("\n[FIX 7] Updating success case in process_video...")
    old_success = """            jobs[job_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Conversion complete!',
                'video_title': video_title,
                'duration': duration,
                'filename': output_filename,
                'video_url': f'/download/{output_filename}',
                'redirect_url': f'/video_result/{output_filename}'
            }

            # Store video info for result page
            jobs[f'video_{output_filename}'] = {
                'title': video_title,
                'duration': duration
            }"""

    new_success = """            job_store.update_job(
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
                                duration=duration)"""

    if old_success in content:
        content = content.replace(old_success, new_success)
        changes_made.append("Success case in process_video")
        print("[DONE] Success case updated")

    # Fix 8: Update error handler in /convert
    print("\n[FIX 8] Updating error handler in /convert...")
    content = content.replace(
        """    except Exception as e:
        error_msg = str(e)
        print(f"❌ /convert error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'error': 'Server error occurred',
            'details': str(e)
        }), 500""",
        """    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] /convert endpoint: {error_msg}")
        return jsonify({
            'error': 'Server error occurred',
            'details': error_msg
        }), 500"""
    )

    # Write back if changes were made
    if content != original_content:
        # Create backup
        backup_path = file_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"\n[BACKUP] Original saved to {backup_path}")

        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("\n" + "=" * 60)
        print("FIXES APPLIED SUCCESSFULLY")
        print("=" * 60)
        print(f"\nChanges made:")
        for i, change in enumerate(changes_made, 1):
            print(f"  {i}. {change}")

        print(f"\nBackup created: {backup_path}")
        print(f"Updated file: {file_path}")

        return True
    else:
        print("\n" + "=" * 60)
        print("NO CHANGES NEEDED")
        print("=" * 60)
        print("\nAll fixes appear to be already applied.")
        return False


if __name__ == '__main__':
    print("\nProduction Fix Automation Script")
    print("This will update integrated_app.py to use JobStore\n")

    response = input("Continue? (yes/no): ").lower().strip()

    if response in ['yes', 'y']:
        success = apply_fixes()
        if success:
            print("\n✅ Integration complete!")
            print("\nNext steps:")
            print("1. Test locally: python integrated_app.py")
            print("2. Commit: git add integrated_app.py")
            print("3. Commit: git commit -m 'Complete JobStore integration'")
            print("4. Push: git push origin master")
        sys.exit(0 if success else 1)
    else:
        print("\nAborted.")
        sys.exit(1)
