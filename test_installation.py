"""
Test script to verify both systems are properly installed
"""
import sys
import importlib
from pathlib import Path


def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...\n")

    modules_to_test = [
        # System 1
        ('yt2tik', 'System 1 - Main package'),
        ('yt2tik.config', 'System 1 - Configuration'),
        ('yt2tik.logger', 'System 1 - Logger'),
        ('yt2tik.downloader', 'System 1 - Downloader'),
        ('yt2tik.converter', 'System 1 - Converter'),
        ('yt2tik.caption_gen', 'System 1 - Caption Generator'),
        ('yt2tik.uploader', 'System 1 - Uploader'),

        # System 2
        ('yt_analyzer', 'System 2 - Main package'),
        ('yt_analyzer.config', 'System 2 - Configuration'),
        ('yt_analyzer.fetcher', 'System 2 - YouTube Fetcher'),
        ('yt_analyzer.scorer', 'System 2 - Viral Scorer'),
        ('yt_analyzer.reporter', 'System 2 - Report Generator'),
        ('yt_analyzer.niche_presets', 'System 2 - Niche Presets'),
        ('yt_analyzer.uploader_bridge', 'System 2 - Uploader Bridge'),
    ]

    failed = []

    for module_name, description in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"[OK] {description}")
        except Exception as e:
            print(f"[X] {description}: {str(e)}")
            failed.append((module_name, str(e)))

    print()

    if failed:
        print(f"[X] {len(failed)} module(s) failed to import:")
        for module, error in failed:
            print(f"   - {module}: {error}")
        return False
    else:
        print("[OK] All modules imported successfully!")
        return True


def test_dependencies():
    """Test that required dependencies are installed"""
    print("\nTesting dependencies...\n")

    dependencies = [
        ('yt_dlp', 'yt-dlp'),
        ('ffmpeg', 'ffmpeg-python'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
        ('rich', 'rich'),
        ('tqdm', 'tqdm'),
        ('googleapiclient', 'google-api-python-client'),
        ('pandas', 'pandas'),
    ]

    failed = []

    for module_name, package_name in dependencies:
        try:
            importlib.import_module(module_name)
            print(f"[OK] {package_name}")
        except Exception as e:
            print(f"[X] {package_name}: Not installed")
            failed.append(package_name)

    print()

    if failed:
        print(f"[X] {len(failed)} dependency(ies) missing:")
        for package in failed:
            print(f"   - {package}")
        print("\nRun: pip install -r requirements.txt")
        return False
    else:
        print("[OK] All dependencies installed!")
        return True


def test_directories():
    """Test that required directories exist"""
    print("\nTesting directory structure...\n")

    base_dir = Path(__file__).parent

    directories = [
        'yt2tik',
        'yt_analyzer',
        'logs',
        'tmp/yt2tik/downloads',
        'tmp/yt2tik/output',
        'examples',
    ]

    failed = []

    for dir_path in directories:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"[OK] {dir_path}/")
        else:
            print(f"[X] {dir_path}/ - Missing")
            failed.append(dir_path)

    print()

    if failed:
        print(f"[X] {len(failed)} directory(ies) missing")
        return False
    else:
        print("[OK] All directories exist!")
        return True


def test_config_files():
    """Test that configuration files exist"""
    print("\nTesting configuration files...\n")

    base_dir = Path(__file__).parent

    files = [
        ('.env', 'Environment variables', True),
        ('requirements.txt', 'Dependencies list', False),
        ('README.md', 'Documentation', False),
        ('QUICKSTART.md', 'Quick start guide', False),
        ('PROJECT_SUMMARY.md', 'Project summary', False),
    ]

    warnings = []

    for file_path, description, is_critical in files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"[OK] {description}: {file_path}")
        else:
            if is_critical:
                print(f"[!]  {description}: {file_path} - Missing (IMPORTANT)")
                warnings.append(file_path)
            else:
                print(f"[X] {description}: {file_path} - Missing")

    print()

    if warnings:
        print(f"[!]  {len(warnings)} critical file(s) missing:")
        for file in warnings:
            print(f"   - {file}")
        if '.env' in warnings:
            print("\n💡 Create .env from .env.example and add your API credentials")
        return False
    else:
        print("[OK] All configuration files present!")
        return True


def test_env_variables():
    """Test that environment variables are set"""
    print("\nTesting environment variables...\n")

    import os
    from dotenv import load_dotenv

    load_dotenv()

    variables = [
        ('TIKTOK_CLIENT_KEY', 'TikTok Client Key', True),
        ('TIKTOK_CLIENT_SECRET', 'TikTok Client Secret', True),
        ('TIKTOK_ACCESS_TOKEN', 'TikTok Access Token', True),
        ('YOUTUBE_API_KEY', 'YouTube API Key', False),
    ]

    missing = []
    empty = []

    for var_name, description, is_critical in variables:
        value = os.getenv(var_name)
        if value is None:
            print(f"[X] {description}: Not set")
            missing.append(var_name)
        elif not value or value == f'your_{var_name.lower()}_here':
            print(f"[!]  {description}: Empty or placeholder")
            empty.append(var_name)
        else:
            print(f"[OK] {description}: Set")

    print()

    if missing or empty:
        print("[!]  Some environment variables need attention:")
        if missing:
            print(f"   Missing: {', '.join(missing)}")
        if empty:
            print(f"   Empty/Placeholder: {', '.join(empty)}")
        print("\n💡 Edit .env file and add your API credentials")
        return False
    else:
        print("[OK] All environment variables configured!")
        return True


def main():
    """Run all tests"""
    print("="*60)
    print("yt2tik + yt_analyzer - Installation Test")
    print("="*60)

    results = []

    # Run tests
    results.append(('Module Imports', test_imports()))
    results.append(('Dependencies', test_dependencies()))
    results.append(('Directory Structure', test_directories()))
    results.append(('Configuration Files', test_config_files()))
    results.append(('Environment Variables', test_env_variables()))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60 + "\n")

    for test_name, passed in results:
        status = "[OK] PASS" if passed else "[X] FAIL"
        print(f"{status} - {test_name}")

    print()

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("All tests passed! Your installation is ready.")
        print("\nNext steps:")
        print("   1. Edit .env and add your API credentials")
        print("   2. Try: python -m yt2tik.main --help")
        print("   3. Try: python -m yt_analyzer.main --help")
        print("   4. Check examples/ directory for usage examples")
        return 0
    else:
        print("Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Create .env from .env.example")
        print("   - Add your API credentials to .env")
        return 1


if __name__ == '__main__':
    sys.exit(main())
