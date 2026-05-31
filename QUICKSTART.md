# 🚀 Quick Start Guide

## Installation (5 minutes)

### Step 1: Install FFmpeg
**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Extract and add to PATH
3. Test: `ffmpeg -version`

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Step 2: Install Python Dependencies
```bash
# Run the setup script
./setup.sh          # Mac/Linux
setup.bat           # Windows

# Or manually:
pip install -r requirements.txt
```

### Step 3: Setup API Credentials
Edit `.env` file and add your credentials:
```env
TIKTOK_CLIENT_KEY=your_key
TIKTOK_CLIENT_SECRET=your_secret
TIKTOK_ACCESS_TOKEN=your_token
YOUTUBE_API_KEY=your_youtube_key
```

**Get TikTok credentials:** https://developers.tiktok.com/  
**Get YouTube API key:** https://console.cloud.google.com/

---

## System 1: yt2tik - YouTube to TikTok

### Basic Usage
```bash
# Download, convert, and upload to TikTok
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --auto-upload
```

### Advanced Examples

**Specify exact clip:**
```bash
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --start 00:01:30 \
  --duration 45 \
  --auto-upload
```

**Auto-detect best segment (AI-powered):**
```bash
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --auto-detect \
  --duration 30 \
  --auto-upload
```

**Custom caption and hashtags:**
```bash
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --caption "🔥 This is incredible! Must watch!" \
  --hashtags "#fyp #viral #trending #amazing" \
  --auto-upload
```

**Test without uploading:**
```bash
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --dry-run
```

---

## System 2: yt_analyzer - Find Viral Content

### Analyze by Channel
```bash
# Find top videos from a channel
python -m yt_analyzer.main \
  --mode channel \
  --channel "@MrBeast" \
  --limit 30 \
  --output mrbeast_report.md
```

### Analyze by Keyword
```bash
# Search for viral content
python -m yt_analyzer.main \
  --mode search \
  --query "satisfying videos 2024" \
  --limit 25 \
  --output satisfying_report.md
```

### Use Niche Presets
```bash
# Available niches: cooking, fitness, tech, comedy, motivation, 
#                   satisfying, gaming, beauty, travel, diy

python -m yt_analyzer.main \
  --mode search \
  --niche cooking \
  --limit 30 \
  --output cooking_report.md
```

### Auto-Upload Top Video
```bash
# Analyze AND automatically upload #1 video to TikTok
python -m yt_analyzer.main \
  --mode search \
  --query "viral moments 2024" \
  --limit 20 \
  --auto-upload-top \
  --output report.md
```

### Advanced Filtering
```bash
# Filter by duration (60-600 seconds) and minimum views
python -m yt_analyzer.main \
  --mode search \
  --query "tech tutorials" \
  --filter-duration 60-600 \
  --filter-views 10000 \
  --filter-date 2024-01-01:2024-12-31 \
  --output tech_report.md
```

---

## 🎯 Complete Workflows

### Workflow 1: Quick Upload
```bash
# Find a YouTube video and upload to TikTok in one command
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXX" \
  --auto-detect \
  --auto-upload
```

### Workflow 2: Research → Manual Upload
```bash
# Step 1: Research best videos
python -m yt_analyzer.main \
  --mode search \
  --niche satisfying \
  --limit 30 \
  --output report.md

# Step 2: Review report.md and pick a video

# Step 3: Upload your choice
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXX" \
  --start 00:00:15 \
  --duration 45 \
  --auto-upload
```

### Workflow 3: Fully Automated
```bash
# Analyze niche and auto-upload #1 video
python -m yt_analyzer.main \
  --mode search \
  --niche comedy \
  --limit 25 \
  --auto-upload-top
```

---

## 📊 Understanding the Output

### System 1 Output
```
✅ Upload Complete!
📹 TikTok URL: https://tiktok.com/@user/video/XXXXX
📊 Video Duration: 45s | Size: 23MB | Caption: 2100 chars
```

### System 2 Output
Creates a markdown report with:
- **Top 25 videos** ranked by viral score
- **Insights**: Best duration, peak upload days, engagement rates
- **Recommendation**: #1 video to convert with reasoning
- **Viral Score Formula**: Engagement (40%) + Velocity (30%) + Like Ratio (20%) + Views (10%)

---

## 🔧 Troubleshooting

### "FFmpeg not found"
```bash
# Test if installed
ffmpeg -version

# If not found, install and add to PATH
```

### "YouTube API quota exceeded"
- YouTube API has daily limits
- Wait 24 hours or create a new API key
- Reduce --limit to analyze fewer videos

### "TikTok upload failed (401)"
- Access token expired
- Generate new token from TikTok Developer Portal
- Update .env file

### "Video file too large (>72MB)"
- Reduce --duration (try 30s instead of 60s)
- TikTok has 72MB limit

---

## 📁 File Locations

- **Downloaded videos**: `tmp/yt2tik/downloads/`
- **Converted videos**: `tmp/yt2tik/output/`
- **Reports**: `reports/` or current directory
- **Logs**: `logs/yt2tik_YYYY-MM-DD.log`

---

## ⚡ Pro Tips

1. **Use --auto-detect** for best results - AI finds the most engaging segment
2. **Start with --dry-run** to test before uploading
3. **Use niche presets** for faster research
4. **Filter by duration 30-90s** for TikTok-optimized content
5. **Check logs/** if something goes wrong

---

## 🆘 Need Help?

1. Check `README.md` for detailed documentation
2. Review log files in `logs/` directory
3. Verify API credentials in `.env`
4. Test with `--dry-run` first

---

**Built for content creators who want to automate their TikTok workflow** 🚀
