#!/bin/bash
# Final deployment script - executes the deployment

echo "=================================================="
echo "🚀 DEPLOYING TO HUGGING FACE SPACES"
echo "=================================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Add Hugging Face remote
echo "Adding Hugging Face remote..."
git remote remove huggingface 2>/dev/null
git remote add huggingface https://huggingface.co/spaces/Hammaf3213/youtube

# Add all deployment files
echo ""
echo "Adding deployment files..."
git add Dockerfile
git add README.md
git add requirements.txt
git add .dockerignore
git add .env.example
git add integrated_app.py
git add yt2tik/
git add templates/
git add static/
git add DEPLOYMENT_HUGGINGFACE.md
git add DEPLOY_COMMANDS.md
git add DEPLOYMENT_STATUS.md

echo ""
echo "✅ Files added successfully!"
echo ""
echo "=================================================="
echo "Files ready for deployment:"
echo "=================================================="
git status --short

echo ""
echo "=================================================="
echo "🚀 COMMITTING AND PUSHING TO HUGGING FACE"
echo "=================================================="
echo ""

# Commit
git commit -m "Deploy YouTube to TikTok Converter to Hugging Face Spaces

- Added Dockerfile with FFmpeg and yt-dlp
- Configured for port 7860 (Hugging Face requirement)
- Updated README with Space metadata
- Production-ready with Gunicorn WSGI server
- All dependencies included in requirements.txt"

echo ""
echo "✅ Committed successfully!"
echo ""

# Push to Hugging Face
echo "Pushing to Hugging Face Spaces..."
echo ""

git push huggingface master --force

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Go to: https://huggingface.co/spaces/Hammaf3213/youtube/settings"
echo ""
echo "2. Add these environment variables (Settings → Repository secrets):"
echo "   - YOUTUBE_API_KEY (required)"
echo "   - FLASK_SECRET_KEY (required - use a random string)"
echo "   - TIKTOK_CLIENT_KEY (optional)"
echo "   - TIKTOK_CLIENT_SECRET (optional)"
echo ""
echo "3. Wait 5-10 minutes for Docker build to complete"
echo ""
echo "4. Visit your Space: https://huggingface.co/spaces/Hammaf3213/youtube"
echo ""
echo "5. Check logs if there are any issues"
echo ""
echo "=================================================="
