#!/bin/bash
# Quick Deployment Script for Hugging Face Spaces

echo "=========================================="
echo "Hugging Face Spaces Deployment"
echo "=========================================="

# Step 1: Copy README for Hugging Face
echo ""
echo "Step 1: Preparing README..."
cp README_HUGGINGFACE.md README.md
echo "✓ README.md updated with Hugging Face frontmatter"

# Step 2: Git add files
echo ""
echo "Step 2: Adding files to git..."
git add app.py Dockerfile requirements.txt README.md HUGGINGFACE_DEPLOYMENT.md
echo "✓ Files staged for commit"

# Step 3: Commit
echo ""
echo "Step 3: Committing changes..."
git commit -m "Fix PORT handling for Hugging Face Spaces deployment

- Add FastAPI app.py with proper PORT environment variable handling
- Update Dockerfile to use uvicorn instead of gunicorn
- Add FastAPI and uvicorn to requirements.txt
- Handle empty PORT string with fallback to 7860
- Bind to 0.0.0.0 for external access

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"

echo "✓ Changes committed"

# Step 4: Instructions for Hugging Face push
echo ""
echo "=========================================="
echo "Next: Push to Hugging Face Spaces"
echo "=========================================="
echo ""
echo "If you haven't added Hugging Face remote yet:"
echo "  git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME"
echo ""
echo "To push to Hugging Face:"
echo "  git push hf master:main"
echo ""
echo "Or if your branch is 'main':"
echo "  git push hf main"
echo ""
echo "=========================================="
echo "After deployment, check:"
echo "  https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME"
echo "=========================================="
