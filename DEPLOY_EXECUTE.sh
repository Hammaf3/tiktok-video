#!/bin/bash
# Hugging Face Deployment - Execute All Commands

set -e  # Exit on error

echo "================================================================================"
echo "DEPLOYING TO HUGGING FACE SPACES"
echo "================================================================================"
echo ""

# Step 1: Add Hugging Face remote
echo "Step 1: Adding Hugging Face remote..."
if git remote | grep -q "^huggingface$"; then
    echo "  Remote 'huggingface' already exists. Removing..."
    git remote remove huggingface
fi
git remote add huggingface https://huggingface.co/spaces/Hammaf3213/youtube
echo "  ✓ Remote added"
echo ""

# Step 2: Stage all files
echo "Step 2: Staging all files..."
git add .
echo "  ✓ Files staged"
echo ""

# Step 3: Show what will be committed
echo "Step 3: Files to be committed:"
git status --short
echo ""

# Step 4: Commit
echo "Step 4: Committing changes..."
git commit -m "Deploy to Hugging Face Spaces - Complete application with Docker"
echo "  ✓ Changes committed"
echo ""

# Step 5: Push to Hugging Face
echo "Step 5: Pushing to Hugging Face..."
echo "  This may take 30-60 seconds..."
echo ""
git push huggingface master
echo ""

echo "================================================================================"
echo "✓ DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Visit: https://huggingface.co/spaces/Hammaf3213/youtube"
echo ""
echo "2. Add environment variables in Settings:"
echo "   - YOUTUBE_API_KEY"
echo "   - FLASK_SECRET_KEY"
echo ""
echo "3. Wait ~10 minutes for Docker build"
echo ""
echo "4. Test your application!"
echo ""
echo "================================================================================"
