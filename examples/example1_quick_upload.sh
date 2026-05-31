#!/bin/bash
# Example 1: Quick TikTok Upload
# Downloads a YouTube video, auto-detects best 30s segment, and uploads to TikTok

echo "Example 1: Quick TikTok Upload"
echo "================================"
echo ""
echo "This will:"
echo "1. Download a YouTube video"
echo "2. Auto-detect the best 30-second segment"
echo "3. Convert to TikTok format (9:16)"
echo "4. Upload to TikTok"
echo ""

# Replace with your YouTube URL
YOUTUBE_URL="https://youtube.com/watch?v=dQw4w9WgXcQ"

python -m yt2tik.main \
  --url "$YOUTUBE_URL" \
  --auto-detect \
  --duration 30 \
  --auto-upload

echo ""
echo "Done! Check your TikTok account."
