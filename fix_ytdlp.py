"""
Fix corrupted yt-dlp installation

This script reinstalls yt-dlp cleanly to remove js_runtimes corruption
"""

import subprocess
import sys

print("=" * 70)
print("  YT-DLP CORRUPTION FIX")
print("=" * 70)

print("\n1. Checking current yt-dlp installation...")
try:
    import yt_dlp
    from yt_dlp import YoutubeDL

    print(f"   Version: {yt_dlp.version.__version__}")
    print(f"   Location: {yt_dlp.__file__}")

    # Check for corruption
    test_ydl = YoutubeDL({})
    if 'js_runtimes' in test_ydl.params:
        print(f"\n   [X] CORRUPTED: js_runtimes = {test_ydl.params['js_runtimes']}")
        print(f"   This package needs to be reinstalled")
        needs_fix = True
    else:
        print(f"\n   [OK] Package is clean (no js_runtimes in defaults)")
        needs_fix = False

except ImportError:
    print(f"   [X] yt-dlp not installed")
    needs_fix = True

if not needs_fix:
    print("\n" + "=" * 70)
    print("  NO FIX NEEDED - yt-dlp is clean")
    print("=" * 70)
    sys.exit(0)

print("\n2. Uninstalling yt-dlp...")
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'uninstall', '-y', 'yt-dlp'],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"   Warning: {result.stderr}")

print("\n3. Clearing pip cache...")
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'cache', 'purge'],
    capture_output=True,
    text=True
)
print(f"   {result.stdout.strip()}")

print("\n4. Reinstalling yt-dlp (clean)...")
result = subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'yt-dlp>=2024.12.23'],
    capture_output=True,
    text=True
)
print(result.stdout)
if result.returncode != 0:
    print(f"   [X] Installation failed: {result.stderr}")
    sys.exit(1)

print("\n5. Verifying fix...")
try:
    # Reimport to get fresh package
    import importlib
    if 'yt_dlp' in sys.modules:
        importlib.reload(sys.modules['yt_dlp'])

    import yt_dlp
    from yt_dlp import YoutubeDL

    print(f"   Version: {yt_dlp.version.__version__}")
    print(f"   Location: {yt_dlp.__file__}")

    test_ydl = YoutubeDL({})
    if 'js_runtimes' in test_ydl.params:
        print(f"\n   [X] STILL CORRUPTED: js_runtimes = {test_ydl.params['js_runtimes']}")
        print(f"   The corruption persists - may be in site config")
        sys.exit(1)
    else:
        print(f"\n   [OK] SUCCESS! Package is now clean")
        print(f"   No js_runtimes in defaults")

except Exception as e:
    print(f"\n   [X] Verification failed: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("  FIX COMPLETE - yt-dlp reinstalled cleanly")
print("=" * 70)
