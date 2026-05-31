#!/bin/bash
# Example 3: Analyze Channel
# Analyzes a YouTube channel to find top-performing videos

echo "Example 3: Analyze YouTube Channel"
echo "==================================="
echo ""

# Replace with your target channel
CHANNEL="@MrBeast"
LIMIT=30

python -m yt_analyzer.main \
  --mode channel \
  --channel "$CHANNEL" \
  --limit $LIMIT \
  --sort viral-score \
  --output "reports/${CHANNEL}_report.md"

echo ""
echo "Report saved to: reports/${CHANNEL}_report.md"
echo "Review the report and pick a video to convert!"
