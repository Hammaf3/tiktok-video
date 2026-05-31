#!/bin/bash
# Example 2: Custom Clip with Caption
# Creates a specific clip with custom caption and hashtags

echo "Example 2: Custom Clip with Caption"
echo "===================================="
echo ""

# Replace with your values
YOUTUBE_URL="https://youtube.com/watch?v=dQw4w9WgXcQ"
START_TIME="00:01:30"
DURATION=45
CAPTION="🔥 This is incredible! You won't believe what happens next!"
HASHTAGS="#fyp #viral #trending #amazing #mustsee"

python -m yt2tik.main \
  --url "$YOUTUBE_URL" \
  --start "$START_TIME" \
  --duration $DURATION \
  --caption "$CAPTION" \
  --hashtags "$HASHTAGS" \
  --auto-upload

echo ""
echo "Done!"
