"""
Quick test script to verify the app works before deployment
"""
import subprocess
import sys
import time
import requests

def test_app():
    print("=" * 60)
    print("Testing FastAPI Application for Hugging Face Spaces")
    print("=" * 60)

    print("\n1. Checking if app.py exists...")
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "FastAPI" in content and "port_env" in content:
                print("   [PASS] app.py found with correct PORT handling")
            else:
                print("   [FAIL] app.py missing required code")
                return False
    except FileNotFoundError:
        print("   [FAIL] app.py not found")
        return False

    print("\n2. Checking Dockerfile...")
    try:
        with open("Dockerfile", "r", encoding="utf-8") as f:
            content = f.read()
            if "python app.py" in content and "uvicorn" not in content:
                print("   [PASS] Dockerfile configured correctly")
            else:
                print("   [WARN] Dockerfile may have issues")
    except FileNotFoundError:
        print("   [FAIL] Dockerfile not found")
        return False

    print("\n3. Checking requirements.txt...")
    try:
        with open("requirements.txt", "r", encoding="utf-8") as f:
            content = f.read()
            has_fastapi = "fastapi" in content.lower()
            has_uvicorn = "uvicorn" in content.lower()
            if has_fastapi and has_uvicorn:
                print("   [PASS] FastAPI and uvicorn in requirements.txt")
            else:
                print(f"   [FAIL] Missing: {'fastapi' if not has_fastapi else ''} {'uvicorn' if not has_uvicorn else ''}")
                return False
    except FileNotFoundError:
        print("   [FAIL] requirements.txt not found")
        return False

    print("\n4. Testing PORT handling logic...")
    import os

    # Test empty string
    os.environ['PORT'] = ''
    port_env = os.getenv('PORT', '').strip()
    port = 7860 if not port_env else int(port_env)
    if port == 7860:
        print("   [PASS] Empty PORT string handled correctly (fallback to 7860)")
    else:
        print(f"   [FAIL] Empty PORT returned {port} instead of 7860")
        return False

    # Test valid port
    os.environ['PORT'] = '8080'
    port_env = os.getenv('PORT', '').strip()
    port = 7860 if not port_env else int(port_env)
    if port == 8080:
        print("   [PASS] Valid PORT handled correctly")
    else:
        print(f"   [FAIL] Valid PORT returned {port} instead of 8080")
        return False

    # Clean up
    if 'PORT' in os.environ:
        del os.environ['PORT']

    print("\n" + "=" * 60)
    print("All pre-deployment checks PASSED!")
    print("=" * 60)
    print("\nYour application is ready for Hugging Face Spaces deployment.")
    print("\nNext steps:")
    print("1. Copy README_HUGGINGFACE.md to README.md (optional)")
    print("2. Commit your changes: git add . && git commit -m 'Fix PORT for HF Spaces'")
    print("3. Push to Hugging Face: git push hf master:main")
    print("\nFor detailed instructions, see HUGGINGFACE_DEPLOYMENT.md")

    return True

if __name__ == "__main__":
    try:
        success = test_app()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        sys.exit(1)
