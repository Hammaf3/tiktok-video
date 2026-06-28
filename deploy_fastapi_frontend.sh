#!/bin/bash
# Quick Deploy Script - FastAPI Frontend Fix
# Urdu/English mixed comments for clarity

set -e

echo "=========================================="
echo "FastAPI Frontend - Quick Deploy"
echo "=========================================="
echo ""

# Step 1: Test karein
echo "Step 1: Running tests..."
echo ""
python test_fastapi_frontend.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Tests failed. Deployment aborted."
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 2: Git Changes"
echo "=========================================="
echo ""

# Check for uncommitted changes
if ! git diff --quiet app.py Dockerfile; then
    echo "Staging files..."
    git add app.py Dockerfile test_fastapi_frontend.py FASTAPI_FRONTEND_COMPLETE.md

    echo ""
    echo "Creating commit..."
    git commit -m "Add FastAPI embedded frontend UI

Changes:
- app.py: Root route now returns HTML UI (not JSON)
- Modern gradient design with responsive layout
- YouTube to TikTok converter form
- Loading animations and error handling
- /convert POST endpoint with file download
- Mobile + desktop responsive design

Frontend Features:
- Beautiful gradient purple/blue theme
- YouTube URL input with validation
- Convert button with loading state
- Success/error message display
- One-click download after conversion
- Smooth animations and transitions

Technical Stack:
- FastAPI with HTMLResponse
- Embedded HTML/CSS/JavaScript
- Fetch API for async requests
- Pydantic models for validation

Result: Full web application instead of JSON API

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"

    echo ""
    echo "Commit created successfully!"
else
    echo "No changes to commit (already committed)"
fi

echo ""
echo "=========================================="
echo "Step 3: Push to Hugging Face"
echo "=========================================="
echo ""
echo "To deploy to Hugging Face Spaces, run:"
echo ""
echo "  git remote add hf https://huggingface.co/spaces/USERNAME/SPACE_NAME"
echo "  git push hf master:main"
echo ""
echo "Replace USERNAME and SPACE_NAME with your details"
echo ""
echo "=========================================="
echo "What You'll See After Deployment"
echo "=========================================="
echo ""
echo "Opening your Space URL will show:"
echo ""
echo "  🎬 YouTube to TikTok Converter"
echo "  ┌─────────────────────────────┐"
echo "  │ YouTube Video URL           │"
echo "  │ [Input Box]                 │"
echo "  │                             │"
echo "  │ [Convert to TikTok Button]  │"
echo "  └─────────────────────────────┘"
echo ""
echo "NOT JSON like: {\"status\": \"running\"}"
echo ""
echo "=========================================="
echo "Deployment Ready!"
echo "=========================================="
echo ""
echo "Frontend Features:"
echo "  ✓ Modern gradient UI"
echo "  ✓ YouTube URL input"
echo "  ✓ Loading animations"
echo "  ✓ Error handling"
echo "  ✓ Download functionality"
echo "  ✓ Mobile responsive"
echo ""
