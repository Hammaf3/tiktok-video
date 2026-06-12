---
title: YouTube to TikTok Converter
emoji: 🎬
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🎬 YouTube to TikTok Converter

Convert YouTube videos to TikTok format with automatic optimization and optional upload to TikTok.

## ✨ Features

- **YouTube Video Search**: Search viral videos by keyword and country
- **Smart Conversion**: Automatically converts videos to TikTok's 9:16 format
- **Auto-Detection**: Intelligently finds the best clip segment
- **TikTok Upload**: Direct upload to TikTok with OAuth authentication
- **YouTube Channel Browser**: Browse your YouTube channels and videos
- **Production Ready**: Comprehensive error handling and validation

## 📦 Two Powerful Systems

### System 1: yt2tik - YouTube to TikTok Converter
Convert any YouTube video into a TikTok-optimized clip and auto-upload it.

### System 2: yt_analyzer - YouTube Viral Content Analyzer
Analyze channels or niches to find the best-performing videos, then auto-convert the top pick.

---

## 🚀 Quick Start

### Installation

1. **Clone or download this repository**

2. **Install Python 3.10+**
   ```bash
   python --version  # Should be 3.10 or higher
   ```

3. **Install FFmpeg**
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **Mac**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Setup credentials**
   ```bash
   cp .env.example .env
   # Edit .env and add your API credentials
   ```

---

## 🔑 Getting API Credentials

### TikTok API (Required for uploads)

1. Go to [TikTok for Developers](https://developers.tiktok.com/)
2. Create an app and get OAuth 2.0 credentials
3. Generate an access token with `video.upload` scope
4. Add credentials to `.env`:
   ```
   TIKTOK_CLIENT_KEY=your_key
   TIKTOK_CLIENT_SECRET=your_secret
   TIKTOK_ACCESS_TOKEN=your_token
   ```

### YouTube Data API v3 (Required for System 2)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable YouTube Data API v3
3. Create API credentials (API Key)
4. Add to `.env`:
   ```
   YOUTUBE_API_KEY=your_api_key
   ```

---

## 📖 System 1: yt2tik Usage

### Basic Usage

```bash
# Download, convert, and upload to TikTok
python -m yt2tik.main --url "https://youtube.com/watch?v=XXXX" --auto-upload
```

### Advanced Examples

```bash
# Specify start time and duration
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --start 00:01:20 \
  --duration 45 \
  --auto-upload

# Custom caption and hashtags
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --caption "🔥 Must watch! This is incredible!" \
  --hashtags "#fyp #viral #trending #amazing" \
  --auto-upload

# Auto-detect best segment (AI-powered)
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --auto-detect \
  --duration 30 \
  --auto-upload

# Add watermark
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --watermark "@YourUsername" \
  --auto-upload

# Dry run (test without uploading)
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --dry-run

# Set privacy level
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --privacy private \
  --auto-upload
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | YouTube video URL (required) | - |
| `--start` | Start timestamp (HH:MM:SS or MM:SS or SS) | Auto or 0:00 |
| `--duration` | Clip duration in seconds | 30 |
| `--caption` | Custom caption text | Auto-generated |
| `--hashtags` | Custom hashtags | Auto-generated |
| `--watermark` | Watermark text | None |
| `--privacy` | Privacy: public/friends/private | public |
| `--auto-upload` | Upload to TikTok after conversion | False |
| `--auto-detect` | Auto-detect best segment | False |
| `--dry-run` | Skip upload (testing) | False |
| `--output` | Output filename | Auto-generated |

---

## 📊 System 2: yt_analyzer Usage

### Analyze by Channel

```bash
# Analyze a channel's top videos
python -m yt_analyzer.main \
  --mode channel \
  --channel "@MrBeast" \
  --limit 30 \
  --output report.md
```

### Analyze by Keyword/Niche

```bash
# Search for videos by keyword
python -m yt_analyzer.main \
  --mode search \
  --query "satisfying videos 2024" \
  --limit 25 \
  --output report.md

# Use niche presets
python -m yt_analyzer.main \
  --mode search \
  --niche cooking \
  --limit 30 \
  --output cooking_report.md
```

### Auto-Upload Top Video

```bash
# Analyze and auto-upload the #1 video to TikTok
python -m yt_analyzer.main \
  --mode search \
  --query "viral moments 2024" \
  --limit 20 \
  --auto-upload-top \
  --output report.md
```

### Advanced Filtering

```bash
# Filter by duration and views
python -m yt_analyzer.main \
  --mode search \
  --query "tech tutorials" \
  --filter-duration 60-600 \
  --filter-views 10000 \
  --filter-date 2024-01-01:2024-12-31 \
  --output tech_report.md
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Analysis mode: channel or search | - |
| `--channel` | Channel handle (e.g., @MrBeast) | - |
| `--query` | Search query/keyword | - |
| `--niche` | Niche preset (cooking/fitness/tech/etc.) | - |
| `--limit` | Number of videos to analyze | 25 |
| `--sort` | Sort by: engagement/viral-score/views | viral-score |
| `--filter-duration` | Duration range (e.g., 60-600) | None |
| `--filter-views` | Minimum view count | None |
| `--filter-date` | Date range (YYYY-MM-DD:YYYY-MM-DD) | None |
| `--output` | Output markdown file | report.md |
| `--auto-upload-top` | Auto-upload #1 video to TikTok | False |
| `--dry-run` | Skip upload | False |

---

## 🎯 Niche Presets

Available niche presets for `--niche` option:

- `cooking` - Quick recipes, cooking hacks, food tutorials
- `fitness` - Workouts, gym motivation, weight loss
- `tech` - AI tutorials, coding tips, tech reviews
- `comedy` - Funny moments, pranks, fails
- `motivation` - Success mindset, morning routines
- `satisfying` - Oddly satisfying, ASMR, relaxing

---

## 📁 Project Structure

```
tiktok-video-uploader/
├── yt2tik/                    # System 1: YouTube to TikTok
│   ├── __init__.py
│   ├── main.py               # CLI entry point
│   ├── config.py             # Configuration
│   ├── logger.py             # Logging setup
│   ├── downloader.py         # YouTube download
│   ├── converter.py          # FFmpeg conversion
│   ├── caption_gen.py        # Caption generator
│   └── uploader.py           # TikTok API upload
│
├── yt_analyzer/              # System 2: YouTube Analyzer
│   ├── __init__.py
│   ├── main.py               # CLI entry point
│   ├── config.py             # Configuration
│   ├── fetcher.py            # YouTube API calls
│   ├── scorer.py             # Viral score calculation
│   ├── reporter.py           # Markdown report generator
│   ├── niche_presets.py      # Keyword presets
│   └── uploader_bridge.py    # Bridge to System 1
│
├── tmp/                      # Temporary files
│   └── yt2tik/
│       ├── downloads/        # Downloaded videos
│       └── output/           # Converted videos
│
├── logs/                     # Log files
├── requirements.txt          # Python dependencies
├── .env                      # API credentials (create from .env.example)
├── .env.example              # Example credentials file
└── README.md                 # This file
```

---

## 🍪 Age-Restricted Videos Support

To download age-restricted YouTube videos, you need to provide YouTube cookies:

1. **See detailed guide:** `COOKIES_SETUP.md`
2. **Quick steps:**
   - Install browser extension "Get cookies.txt LOCALLY"
   - Login to YouTube
   - Export cookies
   - Save as `youtube_cookies.txt` in project root

The app will automatically use cookies if the file exists.

---

## 🚀 Deployment

**Important:** This app cannot run on Vercel (serverless limitations).

**Recommended Platform:** Railway.app

See detailed deployment guide: `DEPLOYMENT_GUIDE.md`

**Quick Deploy to Railway:**
1. Push code to GitHub
2. Sign up at railway.app
3. Deploy from GitHub repo
4. Add environment variables
5. Done! App will be live in 2-3 minutes

---

## 🔧 Troubleshooting

### Age-restricted video error
- **Solution:** Setup YouTube cookies (see `COOKIES_SETUP.md`)
- Export cookies from your browser after logging into YouTube
- Place `youtube_cookies.txt` in project root

### FFmpeg not found
```bash
# Test if FFmpeg is installed
ffmpeg -version

# If not found, install it:
# Windows: Download from ffmpeg.org and add to PATH
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### TikTok upload fails with 401
- Your access token may have expired
- Run the upload again - it will attempt to refresh automatically
- If refresh fails, generate a new token from TikTok Developer Portal

### YouTube download fails
- **Age-restricted videos:** Setup cookies (see `COOKIES_SETUP.md`)
- **Private videos:** Cannot be downloaded
- **Geo-blocked:** Try using a VPN
- **Update yt-dlp:** `pip install -U yt-dlp`

### Video file too large (>72MB)
- Reduce `--duration` (try 30s instead of 60s)
- The converter automatically optimizes for TikTok's 72MB limit

### YouTube API quota exceeded
- YouTube Data API has a daily quota limit
- Wait 24 hours or create a new API key
- Reduce `--limit` to analyze fewer videos

---

## 📝 Example Workflows

### Workflow 1: Quick TikTok Upload
```bash
# Find a trending YouTube video, convert, and upload
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --auto-detect \
  --auto-upload
```

### Workflow 2: Research Then Upload
```bash
# Step 1: Analyze a niche
python -m yt_analyzer.main \
  --mode search \
  --niche satisfying \
  --limit 30 \
  --output satisfying_report.md

# Step 2: Review report.md and pick a video

# Step 3: Convert and upload manually
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXXX" \
  --start 00:00:15 \
  --duration 45 \
  --auto-upload
```

### Workflow 3: Fully Automated
```bash
# Analyze and auto-upload the best video in one command
python -m yt_analyzer.main \
  --mode search \
  --query "viral moments 2024" \
  --limit 20 \
  --auto-upload-top
```

---

## ⚠️ Important Notes

1. **TikTok API Access**: You need approved TikTok Developer access to use the upload feature
2. **Copyright**: Only upload videos you have rights to use
3. **Rate Limits**: Both TikTok and YouTube APIs have rate limits
4. **File Size**: TikTok has a 72MB file size limit
5. **Duration**: TikTok videos can be up to 60 seconds (this tool enforces this)

---

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

---

## 📄 License

This project is for educational purposes. Ensure you comply with YouTube's Terms of Service and TikTok's API Terms when using this tool.

---

## 🆘 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review the log files in `logs/` directory
3. Ensure all API credentials are correctly set in `.env`

---

**Built with ❤️ for content creators**
