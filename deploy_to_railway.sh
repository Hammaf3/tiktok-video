#!/bin/bash

# Deployment Script for Railway
# This script prepares and deploys the enhanced application

echo "=========================================="
echo "🚀 Railway Deployment Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "integrated_app.py" ]; then
    echo "❌ Error: integrated_app.py not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "📋 Step 1: Checking files..."
echo ""

# Check if enhanced downloader exists
if [ -f "yt2tik/downloader_enhanced.py" ]; then
    echo "✅ Enhanced downloader found"
else
    echo "❌ Enhanced downloader not found"
    exit 1
fi

# Check if production Dockerfile exists
if [ -f "Dockerfile.production_final" ]; then
    echo "✅ Production Dockerfile found"
else
    echo "❌ Production Dockerfile not found"
    exit 1
fi

echo ""
echo "📋 Step 2: Preparing files..."
echo ""

# Copy production Dockerfile to Dockerfile (Railway auto-detects this)
cp Dockerfile.production_final Dockerfile
echo "✅ Copied Dockerfile.production_final → Dockerfile"

# Copy production requirements
if [ -f "requirements.production.txt" ]; then
    cp requirements.production.txt requirements.txt
    echo "✅ Copied requirements.production.txt → requirements.txt"
fi

echo ""
echo "📋 Step 3: Git status check..."
echo ""

# Check git status
git status --short

echo ""
echo "📋 Step 4: Adding files to git..."
echo ""

# Add all modified files
git add integrated_app.py
git add yt2tik/downloader_enhanced.py
git add yt2tik/config.py
git add Dockerfile
git add requirements.txt
git add IMPLEMENTATION_COMPLETE.md

echo "✅ Files staged for commit"

echo ""
echo "📋 Step 5: Creating commit..."
echo ""

# Create commit
git commit -m "Production deployment: Enhanced error handling and Railway optimizations

- Add comprehensive error detection (HTTP 429, login required, private videos, etc.)
- Implement retry logic with exponential backoff
- Add user-friendly error messages
- Optimize Dockerfile for Railway
- Use /tmp directory for Railway ephemeral storage
- Enhanced health checks with component status
- Update dependencies for production stability"

echo "✅ Commit created"

echo ""
echo "📋 Step 6: Pushing to GitHub..."
echo ""

# Push to origin
git push origin master

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Railway will now automatically deploy your application."
echo ""
echo "📊 Next Steps:"
echo "1. Wait 5-10 minutes for Railway to build and deploy"
echo "2. Check Railway dashboard for deployment status"
echo "3. Test health endpoint: https://your-app.up.railway.app/health"
echo "4. Monitor logs for any errors"
echo ""
echo "Expected health response:"
echo '{'
echo '  "status": "healthy",'
echo '  "components": {'
echo '    "enhanced_downloader": true,'
echo '    "ffmpeg": true,'
echo '    "yt_dlp": true'
echo '  }'
echo '}'
echo ""
echo "=========================================="
