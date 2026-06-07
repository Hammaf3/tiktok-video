#!/usr/bin/env python3
"""
Railway Deployment Monitor
Continuously checks if /terms and /privacy are live on Railway
"""
import requests
import time
import sys
from datetime import datetime

BASE_URL = "https://tiktok-video-production.up.railway.app"

def check_url(url):
    """Check if URL returns 200 and expected content"""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code, len(response.text)
    except:
        return None, 0

def main():
    print("=" * 70)
    print("RAILWAY DEPLOYMENT MONITOR")
    print("=" * 70)
    print()
    print(f"Monitoring: {BASE_URL}")
    print("Checking every 30 seconds until deployment is complete...")
    print()
    print("Press Ctrl+C to stop")
    print()

    attempt = 0
    max_attempts = 20  # 20 attempts * 30 seconds = 10 minutes

    while attempt < max_attempts:
        attempt += 1
        current_time = datetime.now().strftime("%H:%M:%S")

        print(f"[{current_time}] Attempt {attempt}/{max_attempts}")

        # Check homepage
        home_status, home_size = check_url(f"{BASE_URL}/")

        # Check terms
        terms_status, terms_size = check_url(f"{BASE_URL}/terms")

        # Check privacy
        privacy_status, privacy_size = check_url(f"{BASE_URL}/privacy")

        # Display results
        print(f"  Homepage: {home_status or 'ERROR'}")
        print(f"  /terms:   {terms_status or 'ERROR'}")
        print(f"  /privacy: {privacy_status or 'ERROR'}")

        # Check if all successful
        if home_status == 200 and terms_status == 200 and privacy_status == 200:
            print()
            print("=" * 70)
            print("SUCCESS! DEPLOYMENT COMPLETE!")
            print("=" * 70)
            print()
            print("All URLs are now live:")
            print(f"  Homepage:     {BASE_URL}/")
            print(f"  Terms:        {BASE_URL}/terms")
            print(f"  Privacy:      {BASE_URL}/privacy")
            print()

            # Verify content
            if terms_size > 10000 and privacy_size > 10000:
                print("Content verification:")
                print(f"  Terms page:   {terms_size:,} bytes (expected ~18KB)")
                print(f"  Privacy page: {privacy_size:,} bytes (expected ~22KB)")
                print()
                print("Pages have correct content!")

            print()
            print("Deployment successful! You can now access:")
            print(f"  {BASE_URL}/terms")
            print(f"  {BASE_URL}/privacy")
            print()
            return 0

        # Still deploying
        if home_status == 502 or terms_status == 502 or privacy_status == 502:
            print("  Status: Still deploying or app crashed...")
        elif home_status == 200 and (terms_status != 200 or privacy_status != 200):
            print("  Status: App running but legal pages not working!")
            print("  This means routes or templates have an issue.")
            print()
            print("  Check Railway logs for errors.")
            return 1

        print()

        if attempt < max_attempts:
            print(f"Waiting 30 seconds before next check...")
            print()
            time.sleep(30)

    # Timeout
    print("=" * 70)
    print("TIMEOUT")
    print("=" * 70)
    print()
    print("Deployment did not complete within 10 minutes.")
    print()
    print("Next steps:")
    print("  1. Check Railway dashboard for deployment status")
    print("  2. Look at build/runtime logs for errors")
    print("  3. Try manual redeploy if needed")
    print()
    return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print()
        print("Monitoring stopped by user.")
        print()
        sys.exit(0)
