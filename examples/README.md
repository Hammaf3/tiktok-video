# 📚 Example Scripts

This directory contains ready-to-use example scripts demonstrating common workflows.

## 🚀 Quick Start

All scripts are bash scripts. Make them executable first:

```bash
chmod +x examples/*.sh
```

---

## 📋 Available Examples

### Example 1: Quick TikTok Upload
**File:** `example1_quick_upload.sh`

Downloads a YouTube video, auto-detects the best 30-second segment, and uploads to TikTok.

```bash
./examples/example1_quick_upload.sh
```

**What it does:**
- Downloads YouTube video
- Auto-detects best segment using AI
- Converts to TikTok format
- Uploads to TikTok

---

### Example 2: Custom Clip with Caption
**File:** `example2_custom_clip.sh`

Creates a specific clip with custom start time, duration, caption, and hashtags.

```bash
./examples/example2_custom_clip.sh
```

**What it does:**
- Clips from specific timestamp (00:01:30)
- 45-second duration
- Custom caption and hashtags
- Uploads to TikTok

---

### Example 3: Analyze Channel
**File:** `example3_analyze_channel.sh`

Analyzes a YouTube channel to find top-performing videos.

```bash
./examples/example3_analyze_channel.sh
```

**What it does:**
- Fetches 30 videos from @MrBeast
- Calculates viral scores
- Generates markdown report
- Shows insights and recommendations

---

### Example 4: Find Viral Content by Niche
**File:** `example4_niche_search.sh`

Searches for viral content in a specific niche using presets.

```bash
./examples/example4_niche_search.sh
```

**What it does:**
- Searches "satisfying" niche
- Filters by duration (30-90s)
- Ranks by viral score
- Generates report

**Available niches:**
- cooking, fitness, tech, comedy, motivation
- satisfying, gaming, beauty, travel, diy

---

### Example 5: Fully Automated Workflow
**File:** `example5_automated.sh`

Analyzes a niche and automatically uploads the #1 video.

```bash
./examples/example5_automated.sh
```

**What it does:**
- Searches for viral content
- Filters by duration and views
- Ranks all videos
- **Automatically uploads #1 video to TikTok**

⚠️ **Warning:** This will actually upload to TikTok!

---

### Example 6: Test Run (Dry Run)
**File:** `example6_test_run.sh`

Tests the entire pipeline without uploading.

```bash
./examples/example6_test_run.sh
```

**What it does:**
- Downloads and converts video
- Generates caption
- **Skips TikTok upload** (dry-run mode)
- Perfect for testing!

---

## ✏️ Customizing Examples

Edit the scripts and change these variables:

```bash
# In example1_quick_upload.sh
YOUTUBE_URL="https://youtube.com/watch?v=YOUR_VIDEO_ID"

# In example2_custom_clip.sh
START_TIME="00:01:30"
DURATION=45
CAPTION="Your custom caption here"
HASHTAGS="#your #hashtags #here"

# In example3_analyze_channel.sh
CHANNEL="@YourChannel"
LIMIT=30

# In example4_niche_search.sh
NICHE="cooking"  # or fitness, tech, comedy, etc.

# In example5_automated.sh
QUERY="your search query"
LIMIT=20
```

---

## 🎯 Recommended Learning Path

1. **Start with Example 6** (Test Run)
   - Verify your setup works
   - No upload, safe to test

2. **Try Example 1** (Quick Upload)
   - Simple one-command upload
   - Uses auto-detection

3. **Experiment with Example 2** (Custom Clip)
   - Learn to specify exact clips
   - Customize captions

4. **Explore Example 3** (Analyze Channel)
   - Research content without uploading
   - Understand viral scores

5. **Use Example 4** (Niche Search)
   - Find trending content
   - Use niche presets

6. **Master Example 5** (Fully Automated)
   - Complete automation
   - Research + Upload in one command

---

## 💡 Pro Tips

1. **Always test with --dry-run first**
   ```bash
   python -m yt2tik.main --url "..." --dry-run
   ```

2. **Check logs if something fails**
   ```bash
   cat logs/yt2tik_*.log
   ```

3. **Start with small limits**
   ```bash
   --limit 5  # Instead of 50
   ```

4. **Use filters to find TikTok-ready content**
   ```bash
   --filter-duration 30-60  # Perfect for TikTok
   ```

5. **Review reports before auto-uploading**
   - Run analysis first
   - Review the markdown report
   - Then manually upload your choice

---

## 🔧 Troubleshooting

**Script won't run:**
```bash
chmod +x examples/*.sh
```

**"Command not found":**
```bash
# Run from project root
cd "/path/to/tiktok video uploader"
./examples/example1_quick_upload.sh
```

**Python module not found:**
```bash
# Install dependencies first
pip install -r requirements.txt
```

**API errors:**
- Check your `.env` file has valid credentials
- Verify TikTok/YouTube API keys are correct

---

## 📞 Need Help?

1. Check `../README.md` for detailed documentation
2. Review `../QUICKSTART.md` for quick reference
3. Check `../logs/` for error details
4. Verify `.env` has your API credentials

---

**Happy automating! 🚀**
