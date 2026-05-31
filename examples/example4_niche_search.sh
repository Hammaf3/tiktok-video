#!/bin/bash
# Example 4: Find Viral Content by Niche
# Searches for viral content in a specific niche

echo "Example 4: Find Viral Content by Niche"
echo "======================================="
echo ""
echo "Available niches:"
echo "  - cooking"
echo "  - fitness"
echo "  - tech"
echo "  - comedy"
echo "  - motivation"
echo "  - satisfying"
echo "  - gaming"
echo "  - beauty"
echo "  - travel"
echo "  - diy"
echo ""

# Choose your niche
NICHE="satisfying"
LIMIT=25

python -m yt_analyzer.main \
  --mode search \
  --niche "$NICHE" \
  --limit $LIMIT \
  --filter-duration 30-90 \
  --sort viral-score \
  --output "reports/${NICHE}_viral_report.md"

echo ""
echo "Report saved to: reports/${NICHE}_viral_report.md"
