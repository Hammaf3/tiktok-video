---
title: YouTube to TikTok Converter
emoji: 🎬
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
app_port: 7860
---

# 🎬 YouTube to TikTok Converter

FastAPI application for converting YouTube videos to TikTok format.

## Features

- ✅ YouTube video downloading
- ✅ Video format conversion
- ✅ TikTok-optimized output
- ✅ FastAPI backend with interactive docs
- ✅ Docker deployment ready

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check for monitoring
- `GET /api/info` - Detailed API information
- `GET /docs` - Interactive API documentation (Swagger UI)

## Usage

Once deployed, visit:
- **API Root**: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME`
- **Interactive Docs**: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/docs`
- **Health Check**: `https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/health`

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

The app will start on `http://localhost:7860`

## Docker

```bash
# Build
docker build -t yt2tik-api .

# Run
docker run -p 7860:7860 yt2tik-api
```

## Environment Variables

- `PORT` - Port to run the server (default: 7860)

## Tech Stack

- **Framework**: FastAPI
- **Server**: Uvicorn
- **Video Processing**: FFmpeg, yt-dlp
- **Python**: 3.12

## License

See LICENSE file for details.
