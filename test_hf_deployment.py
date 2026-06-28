#!/usr/bin/env python3
"""
Test script for Hugging Face Spaces deployment
Verifies that the Flask app with frontend is properly configured
"""
import os
import sys
from pathlib import Path

# Fix Windows console encoding
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

def test_files_exist():
    """Test that all required files exist"""
    print("=" * 60)
    print("Testing File Structure")
    print("=" * 60)

    required_files = [
        "integrated_app.py",
        "Dockerfile",
        "entrypoint.sh",
        "requirements.txt",
        "templates/integrated.html",
        "README.md"
    ]

    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - MISSING!")
            all_exist = False

    return all_exist

def test_dockerfile():
    """Test Dockerfile configuration"""
    print("\n" + "=" * 60)
    print("Testing Dockerfile Configuration")
    print("=" * 60)

    with open("Dockerfile", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Uses integrated_app.py": "integrated_app" in content,
        "Has entrypoint.sh": "entrypoint.sh" in content,
        "Exposes port 7860": "7860" in content,
        "Sets FLASK_APP": "FLASK_APP" in content,
        "Makes entrypoint executable": "chmod +x" in content,
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check} - FAILED!")
            all_passed = False

    return all_passed

def test_entrypoint():
    """Test entrypoint script"""
    print("\n" + "=" * 60)
    print("Testing Entrypoint Script")
    print("=" * 60)

    with open("entrypoint.sh", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Has shebang": content.startswith("#!/bin/bash"),
        "Handles empty PORT": "-z \"$PORT\"" in content,
        "Sets fallback PORT": "export PORT=7860" in content,
        "Runs gunicorn": "gunicorn integrated_app:app" in content,
        "Binds to 0.0.0.0": "0.0.0.0" in content,
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check} - FAILED!")
            all_passed = False

    return all_passed

def test_flask_app():
    """Test Flask app configuration"""
    print("\n" + "=" * 60)
    print("Testing Flask App Configuration")
    print("=" * 60)

    with open("integrated_app.py", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Flask app initialized": "app = Flask(__name__)" in content,
        "Has root route": "@app.route('/')" in content,
        "Serves HTML template": "render_template('integrated.html'" in content,
        "Has PORT handling": "port_env = os.getenv('PORT'" in content,
        "Has empty PORT fallback": "if not port_env:" in content,
        "Binds to 0.0.0.0": "host='0.0.0.0'" in content,
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check} - FAILED!")
            all_passed = False

    return all_passed

def test_requirements():
    """Test requirements.txt"""
    print("\n" + "=" * 60)
    print("Testing Requirements")
    print("=" * 60)

    with open("requirements.txt", "r", encoding="utf-8") as f:
        content = f.read().lower()

    checks = {
        "Flask": "flask" in content,
        "Gunicorn": "gunicorn" in content,
        "yt-dlp": "yt-dlp" in content,
        "ffmpeg-python": "ffmpeg-python" in content,
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check} - MISSING!")
            all_passed = False

    return all_passed

def test_readme():
    """Test README.md has Hugging Face frontmatter"""
    print("\n" + "=" * 60)
    print("Testing README Configuration")
    print("=" * 60)

    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "Has frontmatter": content.startswith("---"),
        "Has sdk: docker": "sdk: docker" in content,
        "Has app_port: 7860": "app_port: 7860" in content,
        "Has title": "title:" in content,
    }

    all_passed = True
    for check, passed in checks.items():
        if passed:
            print(f"✓ {check}")
        else:
            print(f"✗ {check} - FAILED!")
            all_passed = False

    return all_passed

def test_port_handling_logic():
    """Test PORT environment variable handling logic"""
    print("\n" + "=" * 60)
    print("Testing PORT Handling Logic")
    print("=" * 60)

    # Test 1: Empty PORT
    os.environ['PORT'] = ''
    port_env = os.getenv('PORT', '').strip()
    port = 7860 if not port_env else int(port_env)
    test1 = (port == 7860)
    print(f"✓ Empty PORT → 7860" if test1 else f"✗ Empty PORT failed")

    # Test 2: Valid PORT
    os.environ['PORT'] = '8080'
    port_env = os.getenv('PORT', '').strip()
    port = 7860 if not port_env else int(port_env)
    test2 = (port == 8080)
    print(f"✓ Valid PORT → 8080" if test2 else f"✗ Valid PORT failed")

    # Test 3: PORT not set
    if 'PORT' in os.environ:
        del os.environ['PORT']
    port_env = os.getenv('PORT', '').strip()
    port = 7860 if not port_env else int(port_env)
    test3 = (port == 7860)
    print(f"✓ No PORT → 7860" if test3 else f"✗ No PORT failed")

    return test1 and test2 and test3

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 Hugging Face Spaces Deployment Test")
    print("Testing Flask App with Frontend UI")
    print("=" * 60)
    print()

    tests = [
        ("File Structure", test_files_exist),
        ("Dockerfile", test_dockerfile),
        ("Entrypoint Script", test_entrypoint),
        ("Flask App", test_flask_app),
        ("Requirements", test_requirements),
        ("README", test_readme),
        ("PORT Handling", test_port_handling_logic),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = all(results.values())
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests PASSED!")
        print("=" * 60)
        print("\n🚀 Your app is ready for Hugging Face Spaces deployment!")
        print("\nNext steps:")
        print("1. Commit your changes:")
        print("   git add .")
        print('   git commit -m "Fix frontend for Hugging Face Spaces"')
        print("\n2. Push to Hugging Face:")
        print("   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE")
        print("   git push hf master:main")
        print("\n3. Your Space will show the web UI at:")
        print("   https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE")
        return 0
    else:
        print("❌ Some tests FAILED!")
        print("=" * 60)
        print("\nPlease fix the failed tests before deploying.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
