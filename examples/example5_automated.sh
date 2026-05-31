#!/bin/bash
# Example 5: Fully Automated Workflow
# Analyzes a niche and automatically uploads the #1 video

echo "Example 5: Fully Automated Workflow"
echo "===================================="
echo ""
echo "This will:"
echo "1. Search for viral content in a niche"
echo "2. Rank videos by viral score"
echo "3. Automatically convert and upload the #1 video to TikTok"
echo ""

# Choose your niche or query
QUERY="viral cooking hacks 2024"
LIMIT=20

python -m yt_analyzer.main \
  --mode search \
  --query "$QUERY" \
  --limit $LIMIT \
  --filter-duration 30-60 \
  --filter-views 50000 \
  --auto-upload-top \
  --output "reports/automated_workflow_report.md"

echo ""
echo "Done! The top video has been uploaded to TikTok."
echo "Check the report for details: reports/automated_workflow_report.md"
