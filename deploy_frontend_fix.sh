#!/bin/bash
# Quick Deployment Script for Hugging Face Spaces
# Deploys Flask app with frontend UI

set -e

echo "=========================================="
echo "Hugging Face Spaces - Frontend Fix Deploy"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "integrated_app.py" ]; then
    echo "ERROR: integrated_app.py not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

echo "Step 1: Running pre-deployment tests..."
python test_hf_deployment.py
if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed. Please fix issues before deploying."
    exit 1
fi

echo ""
echo "Step 2: Staging files for commit..."
git add integrated_app.py Dockerfile entrypoint.sh README.md test_hf_deployment.py FRONTEND_FIX_SUMMARY.md

echo ""
echo "Step 3: Creating commit..."
git commit -m "Fix frontend for Hugging Face Spaces

- Update Dockerfile to run Flask app with frontend UI
- Fix PORT handling for empty string in integrated_app.py
- Add entrypoint.sh for proper PORT environment variable handling
- Update README.md with app_port: 7860
- Frontend web interface will now show instead of JSON

Changes:
- integrated_app.py: Safe PORT handling with fallback to 7860
- Dockerfile: Run Flask app via entrypoint.sh
- entrypoint.sh: Bash script for PORT variable handling
- README.md: Added app_port: 7860 in frontmatter

Result: Web UI with YouTube search and convert interface

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"

echo ""
echo "=========================================="
echo "Step 4: Push to Hugging Face"
echo "=========================================="
echo ""
echo "To push to Hugging Face Spaces, run:"
echo ""
echo "  # If you haven't added the remote:"
echo "  git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME"
echo ""
echo "  # Then push:"
echo "  git push hf master:main"
echo ""
echo "  # Or if your branch is 'main':"
echo "  git push hf main"
echo ""
echo "=========================================="
echo "After Deployment"
echo "=========================================="
echo ""
echo "Your Space URL will show a web interface with:"
echo "  - YouTube search form"
echo "  - Country selector"
echo "  - Convert to TikTok button"
echo "  - Download/Upload options"
echo ""
echo "NOT just JSON like: {\"status\": \"running\"}"
echo ""
echo "=========================================="
echo "Deployment preparation complete!"
echo "=========================================="
