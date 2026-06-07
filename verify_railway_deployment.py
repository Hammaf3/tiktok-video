#!/usr/bin/env python3
"""
Quick verification script to test if /terms and /privacy are live on Railway
"""
import requests
import sys
from time import sleep

BASE_URL = "https://tiktok-video-production.up.railway.app"

def test_url(url, expected_content):
    """Test if a URL returns expected content"""
    try:
        print(f"Testing: {url}")
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            # Check if we got the expected page (not homepage)
            if expected_content in response.text:
                print(f"✅ SUCCESS - {url}")
                print(f"   Status: {response.status_code}")
                print(f"   Content: Found '{expected_content}'")
                return True
            else:
                print(f"❌ FAIL - Got 200 but wrong content")
                print(f"   Expected to find: '{expected_content}'")
                # Check if it's the homepage
                if "YouTube Analyzer + TikTok Converter" in response.text:
                    print(f"   ⚠️  Still showing homepage - Railway may still be deploying")
                return False
        else:
            print(f"❌ FAIL - Status: {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print(f"⏱️  TIMEOUT - Server took too long to respond")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Could not reach server")
        return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🧪 RAILWAY DEPLOYMENT VERIFICATION")
    print("=" * 70)
    print()
    print(f"Base URL: {BASE_URL}")
    print()
    print("Testing legal pages on Railway...")
    print()

    # Test cases
    tests = [
        {
            'url': f'{BASE_URL}/',
            'expected': 'YouTube Analyzer + TikTok Converter',
            'name': 'Homepage'
        },
        {
            'url': f'{BASE_URL}/terms',
            'expected': 'Terms of Service',
            'name': 'Terms of Service'
        },
        {
            'url': f'{BASE_URL}/privacy',
            'expected': 'Privacy Policy',
            'name': 'Privacy Policy'
        }
    ]

    results = []

    for test in tests:
        print(f"📋 Testing: {test['name']}")
        print(f"   URL: {test['url']}")
        success = test_url(test['url'], test['expected'])
        results.append({'name': test['name'], 'success': success})
        print()
        sleep(1)  # Be nice to the server

    print("=" * 70)
    print("📊 RESULTS SUMMARY")
    print("=" * 70)
    print()

    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['name']}")

    print()
    print("=" * 70)

    # Overall result
    all_passed = all(r['success'] for r in results)

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your legal pages are live and working correctly:")
        print(f"  • {BASE_URL}/terms")
        print(f"  • {BASE_URL}/privacy")
        print()
        print("✅ Deployment successful!")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED")
        print()

        # Check if terms and privacy failed
        terms_failed = not next((r for r in results if r['name'] == 'Terms of Service'), {'success': True})['success']
        privacy_failed = not next((r for r in results if r['name'] == 'Privacy Policy'), {'success': True})['success']

        if terms_failed or privacy_failed:
            print("Possible reasons:")
            print("  1. Railway is still deploying (wait 2-5 minutes)")
            print("  2. Template files not found on Railway")
            print("  3. Routes not properly configured")
            print()
            print("Try again in 1-2 minutes, or check Railway deployment logs.")

        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
