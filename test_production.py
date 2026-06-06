"""
Test Script for Production YouTube to TikTok Converter
Run this to verify your setup before deploying
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("=" * 60)
    print("Testing Imports...")
    print("=" * 60)

    try:
        import flask
        print("[OK] Flask imported")
    except ImportError as e:
        print(f"[FAIL] Flask import failed: {e}")
        return False

    try:
        import yt_dlp
        print("[OK] yt-dlp imported")
    except ImportError as e:
        print(f"[FAIL] yt-dlp import failed: {e}")
        return False

    try:
        import ffmpeg
        print("[OK] ffmpeg-python imported")
    except ImportError as e:
        print(f"[FAIL] ffmpeg-python import failed: {e}")
        return False

    try:
        from yt2tik.downloader_production import download_youtube_video, VideoRestrictionError
        print("[OK] Production downloader imported")
    except ImportError as e:
        print(f"[WARN] Production downloader import failed: {e}")
        try:
            from yt2tik.downloader_stable import download_youtube_video
            print("[OK] Fallback to stable downloader")
        except ImportError as e2:
            print(f"[FAIL] No downloader available: {e2}")
            return False

    try:
        from yt2tik.converter_stable import convert_to_tiktok_format
        print("[OK] Converter imported")
    except ImportError as e:
        print(f"[FAIL] Converter import failed: {e}")
        return False

    try:
        import app
        print("[OK] App module imported")
    except ImportError as e:
        print(f"[FAIL] App import failed: {e}")
        return False

    print("\n[OK] All imports successful!\n")
    return True


def test_directories():
    """Test that required directories exist"""
    print("=" * 60)
    print("Testing Directories...")
    print("=" * 60)

    required_dirs = [
        Path("tmp/yt2tik/downloads"),
        Path("tmp/yt2tik/output"),
    ]

    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"[OK] {dir_path} exists")
        else:
            print(f"[WARN] {dir_path} doesn't exist, creating...")
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"[OK] Created {dir_path}")
            except Exception as e:
                print(f"[FAIL] Failed to create {dir_path}: {e}")
                return False

    print("\n[OK] All directories ready!\n")
    return True


def test_ffmpeg():
    """Test that FFmpeg is available"""
    print("=" * 60)
    print("Testing FFmpeg...")
    print("=" * 60)

    import subprocess

    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"[OK] FFmpeg available: {version_line}")
            return True
        else:
            print(f"[FAIL] FFmpeg command failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("[FAIL] FFmpeg not found in PATH")
        print("   Install: apt-get install ffmpeg (Linux)")
        print("   Or: brew install ffmpeg (Mac)")
        print("   Or: Download from https://ffmpeg.org/download.html (Windows)")
        return False
    except Exception as e:
        print(f"[FAIL] FFmpeg test failed: {e}")
        return False


def test_app_startup():
    """Test that the Flask app can start"""
    print("=" * 60)
    print("Testing App Startup...")
    print("=" * 60)

    try:
        import app
        flask_app = app.app

        with flask_app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')

            if response.status_code == 200:
                data = response.get_json()
                print(f"[OK] Health check passed")
                print(f"   Status: {data.get('status')}")
                print(f"   Downloader: {data.get('downloader')}")
                print(f"   Converter: {data.get('converter')}")
                return True
            else:
                print(f"[FAIL] Health check failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"[FAIL] App startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_job_store():
    """Test the job tracking system"""
    print("=" * 60)
    print("Testing Job Store...")
    print("=" * 60)

    try:
        import app
        job_store = app.job_store

        # Create a test job
        job_id = "test-job-123"
        job_store.create_job(job_id)

        # Retrieve it
        job = job_store.get_job(job_id)

        if job and job['job_id'] == job_id:
            print(f"[OK] Job store working")
            print(f"   Created job: {job_id}")
            print(f"   Status: {job['status']}")

            # Update it
            job_store.update_job(job_id, status='completed', progress=100)
            job = job_store.get_job(job_id)

            if job['status'] == 'completed' and job['progress'] == 100:
                print(f"[OK] Job updates working")
                return True
            else:
                print(f"[FAIL] Job update failed")
                return False
        else:
            print(f"[FAIL] Job store failed")
            return False

    except Exception as e:
        print(f"[FAIL] Job store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling with invalid input"""
    print("=" * 60)
    print("Testing Error Handling...")
    print("=" * 60)

    try:
        import app
        flask_app = app.app

        with flask_app.test_client() as client:
            # Test with missing data
            response = client.post('/convert',
                                   json={},
                                   headers={'Content-Type': 'application/json'})

            if response.status_code == 400:
                data = response.get_json()
                print(f"[OK] Missing data validation works")
                print(f"   Error: {data.get('error')}")
            else:
                print(f"[WARN] Expected 400, got {response.status_code}")

            # Test with invalid URL
            response = client.post('/convert',
                                   json={'youtube_url': 'not-a-url'},
                                   headers={'Content-Type': 'application/json'})

            if response.status_code == 400:
                data = response.get_json()
                print(f"[OK] Invalid URL validation works")
                print(f"   Error: {data.get('error')}")
            else:
                print(f"[WARN] Expected 400, got {response.status_code}")

            # Test status with non-existent job
            response = client.get('/status/non-existent-job-id')

            if response.status_code == 404:
                data = response.get_json()
                print(f"[OK] 404 handling works")
                print(f"   Error: {data.get('error')}")
            else:
                print(f"[WARN] Expected 404, got {response.status_code}")

            print("\n[OK] Error handling working correctly!\n")
            return True

    except Exception as e:
        print(f"[FAIL] Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 60)
    print("  YouTube to TikTok Converter - Test Suite")
    print("=" * 60)
    print("\n")

    tests = [
        ("Imports", test_imports),
        ("Directories", test_directories),
        ("FFmpeg", test_ffmpeg),
        ("App Startup", test_app_startup),
        ("Job Store", test_job_store),
        ("Error Handling", test_error_handling),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[FAIL] Test '{test_name}' crashed: {e}\n")
            results.append((test_name, False))

    # Summary
    print("\n")
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} - {test_name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n[SUCCESS] All tests passed! Ready to deploy.\n")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Fix issues before deploying.\n")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
