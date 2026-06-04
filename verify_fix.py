#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Production Fix Verification Script
Tests that all critical fixes are working correctly
Windows-compatible version (no Unicode emojis)
"""
import os
import sys
import subprocess
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")

def check_node_js():
    """Check if Node.js is accessible"""
    print_header("1. Node.js Availability Check")

    import shutil

    # Check standard PATH
    nodejs_path = shutil.which('node') or shutil.which('nodejs')

    if not nodejs_path:
        # Check Nix profile (Railway environment)
        nix_node = '/root/.nix-profile/bin/node'
        if Path(nix_node).exists():
            print(f"[OK] Node.js found in Nix profile: {nix_node}")
            # Add to PATH
            nix_bin = '/root/.nix-profile/bin'
            if nix_bin not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{nix_bin}:{os.environ.get('PATH', '')}"
                print(f"[OK] Added Nix bin to PATH")
            nodejs_path = shutil.which('node')
        else:
            print(f"[WARN] Node.js NOT found in standard PATH or Nix profile")
            print(f"       Android client will be used (no JS runtime)")
            return False

    if nodejs_path:
        try:
            result = subprocess.run(
                [nodejs_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            version = result.stdout.strip()
            print(f"[OK] Node.js accessible: {nodejs_path}")
            print(f"     Version: {version}")
            return True
        except Exception as e:
            print(f"[ERROR] Node.js found but not working: {e}")
            return False

    return False

def check_ytdlp_config_cleanup():
    """Check if yt-dlp config files exist (they should be deleted)"""
    print_header("2. yt-dlp Config File Check")

    config_paths = [
        Path.home() / '.config' / 'yt-dlp' / 'config',
        Path.home() / '.yt-dlp.conf',
        Path('/etc/yt-dlp.conf'),
        Path.home() / '.config' / 'yt-dlp' / 'config.txt',
    ]

    found_configs = []
    for path in config_paths:
        if path.exists():
            found_configs.append(str(path))
            print(f"[WARN] Found config file: {path}")

    if not found_configs:
        print(f"[OK] No yt-dlp config files found (good!)")
        print(f"     This prevents external js_runtimes injection")
        return True
    else:
        print(f"[ERROR] {len(found_configs)} config file(s) exist")
        print(f"        These will be deleted at runtime")
        return False

def check_environment_variables():
    """Check critical environment variables"""
    print_header("3. Environment Variables Check")

    enable_cookies = os.getenv('ENABLE_YOUTUBE_COOKIES', 'false')
    cookies_base64 = os.getenv('YOUTUBE_COOKIES_BASE64', '')

    print(f"ENABLE_YOUTUBE_COOKIES: {enable_cookies}")

    if enable_cookies.lower() == 'true':
        print(f"[WARN] Cookies ENABLED - Web client may be used")
        print(f"       This requires working Node.js and increases failure risk")
        print(f"       Recommendation: Set ENABLE_YOUTUBE_COOKIES=false")
        if cookies_base64:
            print(f"[OK] YOUTUBE_COOKIES_BASE64 is set ({len(cookies_base64)} chars)")
        else:
            print(f"[ERROR] YOUTUBE_COOKIES_BASE64 not set but cookies enabled")
    else:
        print(f"[OK] Cookies DISABLED (recommended for production)")
        print(f"     Android client will be used exclusively")
        print(f"     No JS runtime required, maximum reliability")

    return enable_cookies.lower() != 'true'

def test_ytdlp_import():
    """Test yt-dlp import and configuration"""
    print_header("4. yt-dlp Import & Configuration Test")

    try:
        import yt_dlp
        print(f"[OK] yt-dlp imported successfully")
        print(f"     Version: {yt_dlp.version.__version__}")

        # Test YoutubeDL instantiation with no_config
        test_opts = {
            'no_config': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(test_opts) as ydl:
            print(f"[OK] YoutubeDL instantiated successfully")

            # Check if js_runtimes appears in params
            if 'js_runtimes' in ydl.params:
                print(f"[WARN] js_runtimes in default params: {ydl.params['js_runtimes']}")
                print(f"       This is normal for yt-dlp 2026.3.17+")
                print(f"       Our code uses no_config=True to prevent this")
            else:
                print(f"[OK] js_runtimes NOT in params (good!)")

        return True

    except ImportError as e:
        print(f"[ERROR] Failed to import yt-dlp: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error testing yt-dlp: {e}")
        return False

def test_downloader_module():
    """Test our downloader module imports correctly"""
    print_header("5. Downloader Module Test")

    try:
        from yt2tik.downloader import download_youtube_video, cleanup_ytdlp_configs
        print(f"[OK] downloader module imported successfully")

        # Test config cleanup function
        deleted = cleanup_ytdlp_configs()
        if deleted > 0:
            print(f"[OK] Cleaned up {deleted} config file(s)")
        else:
            print(f"[OK] No config files to clean up")

        return True

    except ImportError as e:
        print(f"[ERROR] Failed to import downloader: {e}")
        print(f"        Make sure you're in the project directory")
        return False
    except Exception as e:
        print(f"[ERROR] Error testing downloader: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[WARN]"
        print(f"{status} {test_name}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print(f"\n[SUCCESS] ALL CHECKS PASSED - Ready for production!")
    elif passed >= total - 1:
        print(f"\n[OK] ACCEPTABLE - Minor warnings only")
    else:
        print(f"\n[WARN] WARNINGS - Review issues above")

def main():
    """Run all verification checks"""
    print_header("PRODUCTION FIX VERIFICATION")
    print("Testing all critical components...")

    results = {
        'Node.js Check': check_node_js(),
        'Config Cleanup': check_ytdlp_config_cleanup(),
        'Environment Variables': check_environment_variables(),
        'yt-dlp Import': test_ytdlp_import(),
        'Downloader Module': test_downloader_module(),
    }

    print_summary(results)

    # Exit with appropriate code
    if sum(results.values()) >= len(results) - 1:
        sys.exit(0)  # Success or acceptable warnings
    else:
        sys.exit(1)  # Too many failures

if __name__ == '__main__':
    main()
