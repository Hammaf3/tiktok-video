#!/bin/bash
# Quick deployment script for Heroku

echo "🚀 Deploying to Heroku..."
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Install from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Login to Heroku
echo "Step 1: Login to Heroku"
heroku login

# Create app (if not exists)
echo ""
echo "Step 2: Create Heroku app"
read -p "Enter app name (e.g., yt2tik-converter): " APP_NAME
heroku create $APP_NAME

# Add FFmpeg buildpack
echo ""
echo "Step 3: Adding FFmpeg buildpack..."
heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git -a $APP_NAME

# Set environment variables
echo ""
echo "Step 4: Setting environment variables"
read -p "Enter YouTube API Key: " YOUTUBE_KEY
read -p "Enter TikTok Client Key: " TIKTOK_KEY
read -p "Enter TikTok Client Secret: " TIKTOK_SECRET

heroku config:set YOUTUBE_API_KEY=$YOUTUBE_KEY -a $APP_NAME
heroku config:set TIKTOK_CLIENT_KEY=$TIKTOK_KEY -a $APP_NAME
heroku config:set TIKTOK_CLIENT_SECRET=$TIKTOK_SECRET -a $APP_NAME
heroku config:set FLASK_SECRET_KEY=$(openssl rand -hex 32) -a $APP_NAME

# Deploy
echo ""
echo "Step 5: Deploying..."
git add .
git commit -m "Deploy web application"
git push heroku main

# Open app
echo ""
echo "✅ Deployment complete!"
heroku open -a $APP_NAME
