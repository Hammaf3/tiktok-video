"""
Test script to verify yt-dlp js_runtimes fix

This validates that our override correctly enables Node.js
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import yt_dlp
import shutil

print("=" * 70)
print("  YT-DLP JS_RUNTIMES FIX VALIDATION")
print("=" * 70)

# Step 1: Check yt-dlp package default
print("\n1. Checking yt-dlp package defaults...")
from yt_dlp import YoutubeDL
test_ydl = YoutubeDL({})
print(f"   Package version: {yt_dlp.version.__version__}")
print(f"   Default js_runtimes: {test_ydl.params.get('js_runtimes', 'NOT SET')}")

# Step 2: Check Node.js availability
print("\n2. Checking Node.js availability...")
nodejs_path = shutil.which('node') or shutil.which('nodejs')
if nodejs_path:
    import subprocess
    result = subprocess.run([nodejs_path, '--version'], capture_output=True, text=True)
    print(f"   [OK] Node.js found: {nodejs_path}")
    print(f"   Version: {result.stdout.strip()}")
else:
    print(f"   [X] Node.js NOT found")

# Step 3: Test with our override
print("\n3. Testing with Node.js override...")
if nodejs_path:
    ydl_opts = {
        'quiet': True,
        'js_runtimes': {'node': {}, 'nodejs': {}},  # Our override
    }
else:
    ydl_opts = {
        'quiet': True,
        'js_runtimes': {},  # Empty to allow any runtime
    }

test_ydl_override = YoutubeDL(ydl_opts)
print(f"   Our js_runtimes config: {ydl_opts.get('js_runtimes')}")
print(f"   After YoutubeDL init: {test_ydl_override.params.get('js_runtimes')}")

# Step 4: Test actual extraction
print("\n4. Testing video extraction...")
print("   Using test video: https://www.youtube.com/watch?v=jNQXAC9IVRw")
print("   (First YouTube video - 19 seconds)")

ydl_opts_full = {
    'quiet': False,
    'verbose': True,
    'skip_download': True,
    'format': 'best',
    'js_runtimes': {'node': {}, 'nodejs': {}} if nodejs_path else {},
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
        }
    },
}

try:
    with yt_dlp.YoutubeDL(ydl_opts_full) as ydl:
        print(f"\n   Final js_runtimes in YoutubeDL instance: {ydl.params.get('js_runtimes')}")

        info = ydl.extract_info('https://www.youtube.com/watch?v=jNQXAC9IVRw', download=False)

        if not info:
            print("\n   ❌ FAILED: No info returned")
        else:
            formats = info.get('formats', [])
            video_formats = [f for f in formats
                           if f.get('vcodec') != 'none'
                           and 'image' not in f.get('format_note', '').lower()
                           and f.get('ext') not in ['jpg', 'png', 'webp']]

            print(f"\n   ✅ SUCCESS!")
            print(f"   Total formats: {len(formats)}")
            print(f"   Video formats: {len(video_formats)}")
            print(f"   Image formats: {len(formats) - len(video_formats)}")

            if len(video_formats) > 0:
                print(f"\n   ✅ VIDEO FORMATS AVAILABLE - FIX WORKS!")
                print(f"\n   Sample formats:")
                for fmt in video_formats[:5]:
                    print(f"   - {fmt.get('format_id')}: {fmt.get('ext')} "
                          f"{fmt.get('height', 'N/A')}p "
                          f"[vcodec: {fmt.get('vcodec', 'N/A')}]")
            else:
                print(f"\n   ❌ NO VIDEO FORMATS - FIX FAILED")
                print(f"   Only images/thumbnails returned")

except Exception as e:
    print(f"\n   ❌ EXTRACTION FAILED")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("  TEST COMPLETE")
print("=" * 70)
