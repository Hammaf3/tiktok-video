#!/bin/bash
# Example 6: Test Run (Dry Run)
# Tests the entire pipeline without actually uploading

echo "Example 6: Test Run (No Upload)"
echo "================================"
echo ""
echo "This will process everything but skip the TikTok upload."
echo "Perfect for testing your setup!"
echo ""

YOUTUBE_URL="https://youtube.com/watch?v=dQw4w9WgXcQ"

python -m yt2tik.main \
  --url "$YOUTUBE_URL" \
  --auto-detect \
  --duration 30 \
  --dry-run

echo ""
echo "Test complete! Check tmp/yt2tik/output/ for the converted video."
echo "If everything looks good, remove --dry-run and add --auto-upload"
