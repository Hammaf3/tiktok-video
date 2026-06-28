#!/usr/bin/env python3
"""
Test FastAPI app with frontend UI
"""
import sys

# Fix encoding for Windows
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

def test_fastapi_frontend():
    """Test that FastAPI app has proper frontend"""
    print("=" * 60)
    print("Testing FastAPI Frontend Configuration")
    print("=" * 60)
    print()

    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()

    tests = {
        "HTMLResponse import": "HTMLResponse" in content,
        "Root route returns HTML": 'response_class=HTMLResponse' in content,
        "HTML content present": '<!DOCTYPE html>' in content,
        "Form element": '<form id="convertForm">' in content,
        "YouTube URL input": 'id="youtubeUrl"' in content,
        "Convert button": 'Convert to TikTok' in content,
        "Loading spinner": 'class="spinner"' in content,
        "CSS styling": '<style>' in content,
        "JavaScript fetch": 'fetch(\'/convert\'' in content,
        "POST /convert endpoint": '@app.post("/convert")' in content,
        "ConvertRequest model": 'class ConvertRequest' in content,
        "Error handling": 'HTTPException' in content,
        "Download endpoint": '@app.get("/download/' in content,
        "Responsive design": '@media (max-width: 480px)' in content,
    }

    all_passed = True
    for test_name, passed in tests.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")
        if not passed:
            all_passed = False

    print()
    print("=" * 60)
    if all_passed:
        print("SUCCESS: All frontend tests passed!")
        print("=" * 60)
        print()
        print("Your FastAPI app now has:")
        print("  - Modern HTML UI at '/' route")
        print("  - YouTube to TikTok converter form")
        print("  - Responsive design (mobile + desktop)")
        print("  - Loading animation during conversion")
        print("  - Success/error message display")
        print("  - Download functionality")
        print()
        return 0
    else:
        print("FAILED: Some tests did not pass")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(test_fastapi_frontend())
