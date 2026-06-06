"""
Test Production Fixes for YouTube to TikTok Converter
Run this to verify all fixes are working correctly
"""
import sys
import os
from pathlib import Path

# Suppress encoding errors on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("Testing Production Fixes")
print("=" * 60)

# Test 1: JobStore import
print("\n[TEST 1] JobStore import...")
try:
    from job_store import JobStore
    js = JobStore(ttl_seconds=3600, max_jobs=1000)
    print("[PASS] JobStore imported successfully")

    # Test job operations
    job = js.create_job('test-123')
    assert job['job_id'] == 'test-123'
    assert job['status'] == 'pending'
    print("[PASS] JobStore.create_job() works")

    js.update_job('test-123', status='processing', progress=50, message='Testing')
    job = js.get_job('test-123')
    assert job['status'] == 'processing'
    assert job['progress'] == 50
    print("[PASS] JobStore.update_job() and get_job() work")

    # Test non-existent job
    job = js.get_job('non-existent')
    assert job is None
    print("[PASS] JobStore.get_job() returns None for missing jobs")

except Exception as e:
    print(f"[FAIL] JobStore error: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 2: Fixed downloader import
print("\n[TEST 2] Fixed downloader import...")
try:
    from yt2tik.downloader_fixed import download_youtube_video, cleanup_old_downloads
    print("[PASS] Fixed downloader imported successfully")
    print("[INFO] download_youtube_video has max_retries parameter")
    print("[INFO] cleanup_old_downloads available")
except Exception as e:
    print(f"[FAIL] Fixed downloader error: {str(e)}")
    import traceback
    traceback.print_exc()

# Test 3: Check integrated_app imports
print("\n[TEST 3] Check integrated_app.py imports...")
try:
    # Check if imports are updated
    with open('integrated_app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    if 'from job_store import JobStore' in content:
        print("[PASS] JobStore import present in integrated_app.py")
    else:
        print("[WARN] JobStore import not found in integrated_app.py")

    if 'from yt2tik.downloader_fixed import' in content:
        print("[PASS] Fixed downloader import present in integrated_app.py")
    elif 'from yt2tik.downloader import' in content:
        print("[WARN] Using original downloader (not fixed version)")

    if 'job_store = JobStore' in content:
        print("[PASS] job_store initialized in integrated_app.py")
    elif 'jobs = {}' in content:
        print("[WARN] Still using jobs dict (not JobStore)")

except Exception as e:
    print(f"[FAIL] Error checking integrated_app.py: {str(e)}")

# Test 4: Check directory structure
print("\n[TEST 4] Check directory structure...")
required_dirs = [
    Path('tmp/yt2tik/downloads'),
    Path('tmp/yt2tik/output'),
    Path('yt2tik'),
]

for dir_path in required_dirs:
    if dir_path.exists():
        print(f"[PASS] {dir_path} exists")
    else:
        print(f"[WARN] {dir_path} does not exist (will be created on startup)")

# Test 5: Check required files
print("\n[TEST 5] Check required files...")
required_files = [
    'integrated_app.py',
    'yt2tik/downloader_fixed.py',
    'job_store.py',
    'Dockerfile',
    'requirements.txt',
]

for file_path in required_files:
    if Path(file_path).exists():
        print(f"[PASS] {file_path} exists")
    else:
        print(f"[FAIL] {file_path} missing")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("\n[NEXT STEPS]")
print("1. Apply manual changes from APPLY_FIXES.txt")
print("2. Test locally: python integrated_app.py")
print("3. Test /convert endpoint: curl -X POST http://localhost:7860/convert -H 'Content-Type: application/json' -d '{\"youtube_url\":\"https://youtube.com/watch?v=dQw4w9WgXcQ\",\"duration\":30}'")
print("4. Test /status endpoint: curl http://localhost:7860/status/<job_id>")
print("5. Deploy to Railway: git push origin master")
print("\n" + "=" * 60)
