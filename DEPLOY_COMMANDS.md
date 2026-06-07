# Hugging Face Spaces Deployment - Quick Reference

## Deployment Commands

```bash
# Clone your Hugging Face Space repository
git clone https://huggingface.co/spaces/Hammaf3213/youtube
cd youtube

# Copy all necessary files from your project (excluding temp files)
# Then add all files
git add Dockerfile README.md requirements.txt .dockerignore integrated_app.py yt2tik/ templates/ .env.example DEPLOYMENT_HUGGINGFACE.md

# Commit
git commit -m "Deploy YouTube to TikTok Converter to Hugging Face Spaces"

# Push to Hugging Face
git push
```

## OR Deploy from Current Directory

```bash
# Add Hugging Face remote
git remote add huggingface https://huggingface.co/spaces/Hammaf3213/youtube

# Add files
git add .

# Commit
git commit -m "Configure for Hugging Face Docker Spaces deployment"

# Push
git push huggingface master
```

## Environment Variables to Set in HF Space

Go to: https://huggingface.co/spaces/Hammaf3213/youtube/settings

Add these secrets:

**Required:**
- `YOUTUBE_API_KEY` - Your YouTube API key
- `FLASK_SECRET_KEY` - Random secret key for sessions

**Optional (for TikTok upload):**
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`

**Optional (for YouTube OAuth):**
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`

## Verification

After deployment:
1. Wait 5-10 minutes for build
2. Visit: https://huggingface.co/spaces/Hammaf3213/youtube
3. Test video search functionality
4. Check logs if issues occur

## Files Deployed

✅ Dockerfile - Docker configuration
✅ requirements.txt - Python dependencies
✅ integrated_app.py - Main Flask application
✅ yt2tik/ - Core modules
✅ templates/ - HTML templates
✅ README.md - Documentation with HF metadata
✅ .env.example - Environment variables template
✅ .dockerignore - Files to exclude from Docker build

## What Happens on Deployment

1. Hugging Face builds Docker image
2. Installs FFmpeg (for video processing)
3. Installs yt-dlp (for YouTube downloads)
4. Installs Python dependencies
5. Starts Gunicorn server on port 7860
6. Application becomes available at your Space URL

## Troubleshooting

**Build fails**: Check Dockerfile syntax
**Port error**: Ensure PORT=7860 in environment
**Import errors**: Check all dependencies in requirements.txt
**Video processing fails**: FFmpeg installation in Dockerfile is correct

See DEPLOYMENT_HUGGINGFACE.md for detailed documentation.
