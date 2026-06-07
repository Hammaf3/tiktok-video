#!/usr/bin/env python3
"""
Quick Test Script - Verify Fixes Applied
Tests all critical endpoints and error handling
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"  # Change if using different port

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health():
    """Test health endpoint"""
    print_section("TEST 1: Health Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint working")
            print(f"   Status: {data.get('status')}")
            print(f"   Components: {data.get('components', {})}")
            return True
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint failed: {str(e)}")
        return False

def test_invalid_job_status():
    """Test status endpoint with invalid job ID (should return 200, not 404)"""
    print_section("TEST 2: Invalid Job ID (No 404 Test)")

    try:
        invalid_id = "invalid-job-id-12345"
        print(f"Checking status for invalid job: {invalid_id}")

        response = requests.get(f"{BASE_URL}/status/{invalid_id}")
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Correctly returns 200 (not 404)")
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
        elif response.status_code == 404:
            print(f"❌ FAILED: Still returns 404 (should return 200)")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  YouTube to TikTok Converter - Verification Tests")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Test 1: Health
    results.append(("Health Endpoint", test_health()))

    # Test 2: Invalid Job ID
    results.append(("No 404 for Invalid Job", test_invalid_job_status()))

    # Summary
    print_section("TEST SUMMARY")

    passed = sum(1 for _, result in results if result is True)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Application is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {str(e)}")
