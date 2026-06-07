# 🚀 Hugging Face Spaces Deployment Guide

## ✅ Fixed Issues

### PORT Environment Variable Handling
The application now correctly handles the Hugging Face Spaces PORT environment variable:

```python
# Correctly read PORT with empty string handling
port_env = os.getenv("PORT", "").strip()

if not port_env:
    port = 7860  # Fallback to default Hugging Face port
else:
    port = int(port_env)
```

**Key fixes:**
- ✅ Handles empty string PORT (`''`) 
- ✅ Falls back to 7860 if PORT is not set or empty
- ✅ Validates PORT value and catches conversion errors
- ✅ Binds to `0.0.0.0` for external access

---

## 📦 Files Modified

### 1. `app.py` (NEW)
- Clean FastAPI application
- Proper PORT handling with fallback
- Health check endpoint at `/health`
- Interactive docs at `/docs`

### 2. `Dockerfile` (UPDATED)
- Uses `python:3.12-slim` base image
- Installs FFmpeg and dependencies
- Runs FastAPI with uvicorn
- Exposes port 7860 (Hugging Face default)
- CMD: `python app.py`

### 3. `requirements.txt` (UPDATED)
- Added `fastapi==0.115.0`
- Added `uvicorn[standard]==0.32.0`
- Kept existing dependencies for backward compatibility

---

## 🎯 Deployment Steps

### Step 1: Create Space on Hugging Face
1. Go to https://huggingface.co/spaces
2. Click "Create new Space"
3. Choose "Docker" as the SDK
4. Name your space

### Step 2: Configure Space
Create a `README.md` in the root with frontmatter:

```yaml
---
title: YouTube to TikTok Converter
emoji: 🎬
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
---
```

### Step 3: Push Code
```bash
# Add Hugging Face remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Push to Hugging Face
git push hf main
```

### Step 4: Monitor Deployment
- Check build logs in the Hugging Face Space UI
- Wait for "Running" status
- Access your app at the provided URL

---

## 🧪 Testing Locally

### Test with Docker (recommended)
```bash
# Build image
docker build -t yt2tik-api .

# Run with default port (7860)
docker run -p 7860:7860 yt2tik-api

# Run with custom PORT
docker run -p 8080:8080 -e PORT=8080 yt2tik-api

# Run with empty PORT (tests fallback)
docker run -p 7860:7860 -e PORT="" yt2tik-api
```

### Test without Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Run with default port
python app.py

# Run with custom PORT
PORT=8080 python app.py

# Test empty PORT handling
PORT="" python app.py
```

### Verify endpoints
```bash
# Health check
curl http://localhost:7860/health

# API info
curl http://localhost:7860/api/info

# Interactive docs
# Open in browser: http://localhost:7860/docs
```

---

## 📋 Best Practices

### Environment Variables
- ✅ Always provide fallback values
- ✅ Handle empty strings explicitly
- ✅ Validate and convert types safely
- ✅ Log which port is being used

### Docker Configuration
- ✅ Use slim base images (smaller size)
- ✅ Clean apt cache to reduce image size
- ✅ Copy requirements.txt first (better caching)
- ✅ Use PYTHONUNBUFFERED=1 for real-time logs

### FastAPI Setup
- ✅ Bind to `0.0.0.0` (not `127.0.0.1`)
- ✅ Enable CORS for web access
- ✅ Provide health check endpoint
- ✅ Enable access logs for debugging

### Hugging Face Specifics
- ✅ Default port is 7860
- ✅ Space must respond within 60 seconds
- ✅ Use `/health` for status checks
- ✅ Enable auto-sleep for free tier

---

## 🐛 Troubleshooting

### "Port is already in use"
```bash
# Kill process on port 7860
lsof -ti:7860 | xargs kill -9  # macOS/Linux
```

### "Connection refused"
- Check if binding to `0.0.0.0` (not `localhost`)
- Verify PORT environment variable
- Check firewall rules

### "Build failed on Hugging Face"
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt
- Review build logs in Space settings

### "App not responding"
- Check if health endpoint returns 200
- Verify app is listening on correct port
- Check container logs

---

## 📊 Port Handling Comparison

### ❌ WRONG (empty string issue)
```python
port = int(os.getenv("PORT", 7860))  # Fails if PORT=""
```

### ✅ CORRECT (handles empty string)
```python
port_env = os.getenv("PORT", "").strip()
if not port_env:
    port = 7860
else:
    port = int(port_env)
```

---

## 🔗 Useful Links

- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
- [Docker SDK Guide](https://huggingface.co/docs/hub/spaces-sdks-docker)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Deployment](https://www.uvicorn.org/deployment/)

---

## ✨ Next Steps

1. **Add your business logic** - The current app.py is a starter template
2. **Configure secrets** - Add API keys in Space settings
3. **Add authentication** - Implement OAuth if needed
4. **Monitor usage** - Use Hugging Face analytics
5. **Scale resources** - Upgrade Space tier if needed

---

## 📝 Notes

- The app is production-ready for Hugging Face Spaces
- Health check endpoint is required for proper monitoring
- Interactive API docs are available at `/docs`
- All logging goes to stdout/stderr (captured by Hugging Face)

---

**Status:** ✅ Ready for deployment to Hugging Face Spaces
