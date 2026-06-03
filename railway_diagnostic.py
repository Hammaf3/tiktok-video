"""
RAILWAY DIAGNOSTIC SCRIPT - Run this on Railway to identify yt-dlp issues

This script performs a complete diagnostic of the yt-dlp environment
and identifies the exact source of any js_runtimes injection.

Usage on Railway:
1. Deploy this file
2. Access Railway shell
3. Run: python railway_diagnostic.py
4. Send output to engineer
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_nodejs():
    """Check Node.js availability and version"""
    print_section("1. NODE.JS RUNTIME CHECK")

    # Check which node/nodejs
    node_paths = []
    for cmd in ['node', 'nodejs']:
        path = shutil.which(cmd)
        if path:
            node_paths.append((cmd, path))
            print(f"✅ {cmd}: {path}")
            try:
                result = subprocess.run([path, '--version'],
                                       capture_output=True, text=True, timeout=5)
                print(f"   Version: {result.stdout.strip()}")
            except Exception as e:
                print(f"   Version check failed: {e}")
        else:
            print(f"❌ {cmd}: NOT FOUND")

    # Check other JS runtimes
    for runtime in ['deno', 'bun', 'quickjs']:
        path = shutil.which(runtime)
        if path:
            print(f"⚠️  {runtime}: {path} (unexpected)")
        else:
            print(f"✅ {runtime}: Not installed (correct)")

    # Check PATH
    print(f"\n📍 PATH environment variable:")
    path_var = os.environ.get('PATH', '')
    for p in path_var.split(':')[:10]:  # First 10 entries
        print(f"   {p}")

    return len(node_paths) > 0


def check_ytdlp_configs():
    """Search for ALL yt-dlp config files"""
    print_section("2. YT-DLP CONFIG FILE SEARCH")

    config_locations = [
        # Standard locations
        '/etc/yt-dlp.conf',
        '/etc/yt-dlp/config',
        '~/.config/yt-dlp/config',
        '~/.config/yt-dlp/config.txt',
        '~/.yt-dlp.conf',
        '~/.yt-dlp/config',

        # XDG locations
        os.path.expanduser('~/.config/yt-dlp/config'),
        os.path.join(os.environ.get('XDG_CONFIG_HOME', '~/.config'), 'yt-dlp/config'),

        # App directory
        '/app/.config/yt-dlp/config',
        '/app/.yt-dlp.conf',
    ]

    found_configs = []

    for location in config_locations:
        expanded = os.path.expanduser(location)
        if os.path.exists(expanded):
            print(f"⚠️  FOUND: {location}")
            try:
                with open(expanded, 'r') as f:
                    content = f.read()
                    print(f"   Content ({len(content)} bytes):")
                    print(f"   {'-'*60}")
                    print(f"   {content[:500]}")
                    if len(content) > 500:
                        print(f"   ... (truncated)")
                    print(f"   {'-'*60}")
                    found_configs.append((location, content))
            except Exception as e:
                print(f"   Error reading: {e}")
        else:
            print(f"✅ Not found: {location}")

    # Search filesystem
    print(f"\n🔍 Searching filesystem for yt-dlp config files...")
    try:
        result = subprocess.run(
            ['find', '/root', '-name', '*yt-dlp*', '-type', 'f'],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            print(f"   Found files:")
            for line in result.stdout.strip().split('\n')[:20]:
                print(f"   - {line}")
        else:
            print(f"   ✅ No yt-dlp config files found")
    except Exception as e:
        print(f"   Search failed: {e}")

    return found_configs


def check_env_variables():
    """Check environment variables affecting yt-dlp"""
    print_section("3. ENVIRONMENT VARIABLES")

    # Check yt-dlp related vars
    print("YT-DLP related variables:")
    found_any = False
    for key in os.environ:
        if 'ytdl' in key.lower() or 'yt_dlp' in key.lower() or 'youtube' in key.lower():
            print(f"   {key} = {os.environ[key][:100]}")
            found_any = True

    if not found_any:
        print("   ✅ No yt-dlp environment variables")

    # Check runtime-related vars
    print("\nRuntime-related variables:")
    for var in ['NODE_PATH', 'DENO_DIR', 'NODE_OPTIONS']:
        value = os.environ.get(var)
        if value:
            print(f"   {var} = {value}")
        else:
            print(f"   {var}: Not set")


def check_ytdlp_package():
    """Check yt-dlp package integrity"""
    print_section("4. YT-DLP PACKAGE CHECK")

    try:
        import yt_dlp
        print(f"✅ yt-dlp imported successfully")
        print(f"   Version: {yt_dlp.version.__version__}")
        print(f"   Location: {yt_dlp.__file__}")

        # Check default YoutubeDL params
        print(f"\n🔍 Checking yt-dlp package defaults...")
        from yt_dlp import YoutubeDL

        test_ydl = YoutubeDL({})

        if 'js_runtimes' in test_ydl.params:
            print(f"❌ CRITICAL: Package defaults contain js_runtimes!")
            print(f"   Value: {test_ydl.params['js_runtimes']}")
            print(f"   This indicates CORRUPTED PACKAGE INSTALLATION")
            return False
        else:
            print(f"✅ Package defaults clean (no js_runtimes)")

        # Print some key defaults
        print(f"\n📋 Key default parameters:")
        for key in ['format', 'outtmpl', 'cookiefile', 'verbose']:
            value = test_ydl.params.get(key, '<not set>')
            print(f"   {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Error checking yt-dlp package: {e}")
        return False


def test_ytdlp_extraction():
    """Test actual yt-dlp video extraction"""
    print_section("5. YT-DLP EXTRACTION TEST")

    try:
        import yt_dlp

        # Test video (short, public, stable)
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video

        print(f"Testing extraction from: {test_url}")
        print(f"This is a 19-second public video for testing...")

        # Minimal config - let yt-dlp use defaults
        ydl_opts = {
            'quiet': False,
            'verbose': True,
            'no_warnings': False,
            'extract_flat': False,
            'skip_download': True,  # Only extract info, don't download
            'format': 'best',

            # Android client (bypasses JS challenges)
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
        }

        print(f"\n📋 Configuration being tested:")
        print(f"   extractor_args: {ydl_opts.get('extractor_args', {})}")

        # Create YoutubeDL instance and check params
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\n🔍 YoutubeDL instance params check:")
            if 'js_runtimes' in ydl.params:
                print(f"   ❌ js_runtimes INJECTED: {ydl.params['js_runtimes']}")
                print(f"   This is the ROOT CAUSE of the failure!")
            else:
                print(f"   ✅ js_runtimes NOT present (correct)")

            print(f"\n⏳ Extracting video info...")
            info = ydl.extract_info(test_url, download=False)

            if not info:
                print(f"❌ FAILED: No info returned")
                return False

            # Check formats
            formats = info.get('formats', [])
            print(f"\n✅ Extraction successful!")
            print(f"   Total formats: {len(formats)}")

            # Count video vs image formats
            video_formats = [f for f in formats
                           if f.get('vcodec') != 'none'
                           and 'image' not in f.get('format_note', '').lower()
                           and f.get('ext') not in ['jpg', 'png', 'webp']]

            image_formats = [f for f in formats
                           if f.get('ext') in ['jpg', 'png', 'webp']
                           or 'image' in f.get('format_note', '').lower()]

            print(f"   Video formats: {len(video_formats)}")
            print(f"   Image formats: {len(image_formats)}")

            if len(video_formats) == 0:
                print(f"\n❌ CRITICAL: NO VIDEO FORMATS AVAILABLE")
                print(f"   Only images/thumbnails returned")
                print(f"   This indicates signature solving failure")

                # Show what we got
                print(f"\n   Available formats:")
                for fmt in formats[:5]:
                    print(f"   - {fmt.get('format_id')}: {fmt.get('ext')} "
                          f"{fmt.get('format_note', 'N/A')} "
                          f"[vcodec: {fmt.get('vcodec', 'N/A')}]")

                return False

            # Show sample video formats
            print(f"\n   Sample video formats:")
            for fmt in video_formats[:5]:
                print(f"   - {fmt.get('format_id')}: {fmt.get('ext')} "
                      f"{fmt.get('height', 'N/A')}p "
                      f"[vcodec: {fmt.get('vcodec', 'N/A')}, "
                      f"acodec: {fmt.get('acodec', 'N/A')}]")

            print(f"\n✅ SUCCESS: Video formats available - yt-dlp is working!")
            return True

    except Exception as e:
        print(f"\n❌ EXTRACTION FAILED")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")

        import traceback
        print(f"\n   Traceback:")
        traceback.print_exc()

        return False


def generate_fix_script(issues):
    """Generate shell script to fix identified issues"""
    print_section("6. GENERATED FIX SCRIPT")

    fix_commands = []

    if issues.get('config_files'):
        fix_commands.append("# Remove yt-dlp config files")
        for location, _ in issues['config_files']:
            expanded = os.path.expanduser(location)
            fix_commands.append(f"rm -f {expanded}")

    if not issues.get('nodejs_found'):
        fix_commands.append("\n# Node.js not found - cannot fix")
        fix_commands.append("# You must install Node.js via nixpacks.toml")

    if issues.get('package_corrupted'):
        fix_commands.append("\n# Reinstall yt-dlp")
        fix_commands.append("pip uninstall -y yt-dlp")
        fix_commands.append("pip install --no-cache-dir yt-dlp")

    if fix_commands:
        print("\n#!/bin/bash")
        print("# Auto-generated fix script")
        print("")
        for cmd in fix_commands:
            print(cmd)
    else:
        print("✅ No issues detected - no fixes needed")


def main():
    """Run complete diagnostic"""
    print("=" * 70)
    print("  RAILWAY YT-DLP DIAGNOSTIC TOOL")
    print("  Complete environment analysis")
    print("=" * 70)
    print(f"\nPython: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"CWD: {os.getcwd()}")

    issues = {}

    # Run all checks
    nodejs_found = check_nodejs()
    issues['nodejs_found'] = nodejs_found

    config_files = check_ytdlp_configs()
    if config_files:
        issues['config_files'] = config_files

    check_env_variables()

    package_ok = check_ytdlp_package()
    if not package_ok:
        issues['package_corrupted'] = True

    extraction_ok = test_ytdlp_extraction()

    # Summary
    print_section("DIAGNOSTIC SUMMARY")

    print("\n📊 Results:")
    print(f"   Node.js found: {'✅ YES' if nodejs_found else '❌ NO'}")
    print(f"   Config files found: {'⚠️  YES' if config_files else '✅ NO'}")
    print(f"   Package integrity: {'✅ OK' if package_ok else '❌ CORRUPTED'}")
    print(f"   Extraction test: {'✅ PASS' if extraction_ok else '❌ FAIL'}")

    # Determine root cause
    print("\n🔍 ROOT CAUSE ANALYSIS:")

    if not nodejs_found and not extraction_ok:
        print("   ❌ Node.js not found AND extraction failed")
        print("   Likely cause: Missing Node.js runtime")
        print("   Fix: Ensure nixpacks.toml includes Node.js")

    elif config_files:
        print("   ⚠️  External config files found")
        print("   Likely cause: Config file injecting js_runtimes")
        print("   Fix: Remove config files")
        issues['has_config_files'] = True

    elif not package_ok:
        print("   ❌ yt-dlp package defaults corrupted")
        print("   Likely cause: Bad installation")
        print("   Fix: Reinstall yt-dlp with --no-cache-dir")

    elif not extraction_ok:
        print("   ❌ Extraction failed despite clean environment")
        print("   Likely cause: Unknown - needs deeper investigation")
        print("   Recommendation: Check yt-dlp verbose logs")

    else:
        print("   ✅ ALL SYSTEMS OPERATIONAL")
        print("   yt-dlp is working correctly!")

    # Generate fix script
    if issues:
        generate_fix_script(issues)

    print("\n" + "=" * 70)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 70)

    return 0 if extraction_ok else 1


if __name__ == '__main__':
    sys.exit(main())
