# Hugging Face Spaces Deployment Guide 🚀

## Repository Information

**Hugging Face Space**: https://huggingface.co/spaces/Hammaf3213/youtube

**Git Clone**:
```bash
git clone https://huggingface.co/spaces/Hammaf3213/youtube
```

## Pre-Deployment Checklist ✅

- [x] Dockerfile created for Hugging Face Spaces
- [x] Application configured for port 7860
- [x] requirements.txt updated
- [x] README.md with Space metadata
- [x] .dockerignore created
- [x] FFmpeg installation in Dockerfile
- [x] yt-dlp installation in Dockerfile
- [x] Directory creation for uploads/downloads
- [x] Gunicorn configured as WSGI server

## Files Modified/Created

### New Files
- `Dockerfile` - Docker configuration for HF Spaces
- `.dockerignore` - Exclude unnecessary files from Docker build
- `DEPLOYMENT_HUGGINGFACE.md` - This guide

### Modified Files
- `README.md` - Added HF Space metadata and documentation
- `integrated_app.py` - Port configuration from environment variable
- `requirements.txt` - Updated dependencies
- `.env.example` - Added PORT configuration

## Deployment Steps

### Step 1: Setup Hugging Face Space

1. Go to https://huggingface.co/spaces/Hammaf3213/youtube
2. Ensure Space settings:
   - **SDK**: Docker
   - **Hardware**: CPU Basic (or upgrade if needed)
   - **Visibility**: Public or Private

### Step 2: Configure Environment Variables

In Hugging Face Space settings, add these secrets:

**Required**:
```bash
YOUTUBE_API_KEY=<your_youtube_api_key>
FLASK_SECRET_KEY=<generate_random_secret>
```

**Optional** (for TikTok upload):
```bash
TIKTOK_CLIENT_KEY=<your_tiktok_client_key>
TIKTOK_CLIENT_SECRET=<your_tiktok_client_secret>
```

**Optional** (for YouTube OAuth):
```bash
YOUTUBE_CLIENT_ID=<your_youtube_client_id>
YOUTUBE_CLIENT_SECRET=<your_youtube_client_secret>
```

### Step 3: Push to Hugging Face

```bash
# Clone the HF repository
git clone https://huggingface.co/spaces/Hammaf3213/youtube
cd youtube

# Copy all files from your project to the cloned directory
# (excluding .git, __pycache__, tmp, logs, etc.)

# Add all files
git add .

# Commit changes
git commit -m "Deploy YouTube to TikTok Converter to Hugging Face Spaces"

# Push to Hugging Face
git push
```

### Step 4: Wait for Build

Hugging Face will automatically:
1. Build the Docker image
2. Install system dependencies (FFmpeg)
3. Install Python dependencies
4. Start the application on port 7860

**Build time**: 5-10 minutes (first deployment)

### Step 5: Verify Deployment

Once deployed, your Space will be available at:
```
https://huggingface.co/spaces/Hammaf3213/youtube
```

## Deployment from Your Local Project

If deploying from your current directory:

```bash
# Add Hugging Face remote
git remote add huggingface https://huggingface.co/spaces/Hammaf3213/youtube

# Check current remotes
git remote -v

# Add all changes
git add Dockerfile README.md requirements.txt .dockerignore .env.example integrated_app.py DEPLOYMENT_HUGGINGFACE.md

# Commit
git commit -m "Configure for Hugging Face Docker Spaces deployment"

# Push to Hugging Face
git push huggingface master
```

## Docker Configuration Details

### Dockerfile Highlights

```dockerfile
FROM python:3.11-slim
- FFmpeg installation via apt-get
- yt-dlp upgraded to latest
- Port 7860 exposed
- Gunicorn WSGI server
- 2 workers, 300s timeout
```

### Port Configuration
- **Hugging Face Required Port**: 7860
- **Bind Address**: 0.0.0.0
- Automatically configured via `PORT` environment variable

### File Storage
- Downloads: `/app/tmp/yt2tik/downloads`
- Outputs: `/app/tmp/yt2tik/output`
- **Note**: Storage is ephemeral (resets on restart)

## Troubleshooting

### Build Fails

**Error**: "Failed to install FFmpeg"
- **Solution**: FFmpeg installation is included in Dockerfile

**Error**: "Port 7860 not responding"
- **Solution**: Check integrated_app.py uses PORT environment variable

### Application Errors

**Error**: "YouTube API quota exceeded"
- **Solution**: YouTube API has daily quotas, wait 24 hours

**Error**: "Video download failed"
- **Solution**: Some videos may be region-blocked or age-restricted

**Error**: "Missing environment variables"
- **Solution**: Add required secrets in HF Space settings

### Performance Issues

**Slow video processing**:
- Upgrade to better hardware tier in HF Space settings
- Consider GPU hardware for faster FFmpeg processing

**Memory issues**:
- Videos are stored temporarily, cleaned after processing
- Upgrade hardware tier if needed

## Monitoring

### View Logs
In Hugging Face Space:
1. Click "Logs" tab
2. View real-time application logs
3. Check for errors and warnings

### Check Status
- Application health: Access the URL
- Build status: Check "Building" indicator
- Errors: Review logs tab

## Environment Variables Reference

| Variable | Required | Purpose |
|----------|----------|---------|
| `YOUTUBE_API_KEY` | Yes | Search YouTube videos |
| `FLASK_SECRET_KEY` | Yes | Session security |
| `TIKTOK_CLIENT_KEY` | No | TikTok OAuth |
| `TIKTOK_CLIENT_SECRET` | No | TikTok OAuth |
| `YOUTUBE_CLIENT_ID` | No | YouTube OAuth |
| `YOUTUBE_CLIENT_SECRET` | No | YouTube OAuth |
| `PORT` | Auto-set | Server port (7860) |

## Features Available on HF Spaces

✅ YouTube video search by keyword and country  
✅ Viral score calculation  
✅ Video download and conversion  
✅ TikTok format optimization (9:16)  
✅ Manual caption input  
✅ Video preview and download  

⚠️ TikTok auto-upload (requires OAuth setup)  
⚠️ YouTube channel browsing (requires OAuth setup)

## Security Notes

- Never commit `.env` file
- Use HF Space secrets for sensitive data
- OAuth callbacks need proper redirect URIs
- File uploads are validated and sanitized

## Next Steps After Deployment

1. **Test the application**: Try searching and converting videos
2. **Setup TikTok OAuth** (optional): Configure redirect URIs
3. **Setup YouTube OAuth** (optional): Configure redirect URIs
4. **Monitor usage**: Check YouTube API quota
5. **Share the Space**: Make it public or share with team

## Getting API Keys

### YouTube API Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project
3. Enable "YouTube Data API v3"
4. Create API key
5. Add to HF Space secrets

### TikTok API
1. Go to [TikTok Developers](https://developers.tiktok.com/)
2. Create app
3. Get Client Key and Client Secret
4. Add redirect URI: `https://huggingface.co/spaces/Hammaf3213/youtube/tiktok/callback`
5. Add to HF Space secrets

## Support

For issues:
- Check HF Space logs
- Review error messages in UI
- Check YouTube API quotas
- Verify environment variables

---

**Deployment Status**: ✅ Ready for Hugging Face Spaces

**Last Updated**: 2026-06-05
