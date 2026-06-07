---
title: YouTube to TikTok Converter
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: docker
pinned: false
app_port: 7860
---

# YouTube to TikTok Converter

Production-ready video converter with:
- ✅ Fallback extraction (android → web → ios)
- ✅ Cookie support (auto-detect)
- ✅ Thread-safe job tracking
- ✅ Structured error handling
- ✅ Zero-crash architecture

## Endpoints

- `GET /health` - Health check
- `POST /convert` - Start conversion
- `GET /status/<job_id>` - Check status
- `GET /download/<filename>` - Download video

## Usage

```bash
curl -X POST https://your-space.hf.space/convert \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=VIDEO_ID",
    "duration": 30
  }'
```

## Optional: Add Cookies

For age-restricted videos, add `youtube_cookies.txt` to project root.

Export from browser using "Get cookies.txt LOCALLY" extension.
