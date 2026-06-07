# Production Deployment Configuration

## Railway Deployment

### 1. Update Start Command
```bash
gunicorn app_production_v2:app --bind 0.0.0.0:$PORT --workers 2 --timeout 600
```

### 2. Environment Variables (Optional)
```
PORT=8080
DEBUG=false
```

### 3. Build Command
```bash
pip install -r requirements.txt && pip install --upgrade yt-dlp
```

---

## Hugging Face Spaces Deployment

### 1. Create Space
- SDK: Docker
- Port: 7860

### 2. Files to Upload
```
app_production_v2.py
Dockerfile.production (rename to Dockerfile)
requirements.txt
yt2tik/ (entire directory)
job_store.py
README_HF.md (rename to README.md)
```

### 3. Optional: Add Cookies
Upload `youtube_cookies.txt` for age-restricted videos.

---

## Testing Production Deployment

### Health Check
```bash
curl https://your-app.railway.app/health
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "jobs": {...}
}
```

### Convert Video
```bash
curl -X POST https://your-app.railway.app/convert \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "duration": 30
  }'
```

Expected:
```json
{
  "success": true,
  "job_id": "uuid",
  "status_url": "/status/uuid"
}
```

### Check Status
```bash
curl https://your-app.railway.app/status/<job_id>
```

Expected (processing):
```json
{
  "job_id": "uuid",
  "status": "processing",
  "progress": 50,
  "message": "Converting..."
}
```

Expected (completed):
```json
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "message": "Conversion complete!",
  "video_url": "/download/tiktok_video.mp4",
  "file_size_mb": 5.2
}
```

Expected (error):
```json
{
  "job_id": "uuid",
  "status": "error",
  "progress": 0,
  "message": "LOGIN_REQUIRED: Add cookies.txt",
  "reason": "LOGIN_REQUIRED",
  "solution": "Add cookies.txt or try different video"
}
```

### Test Error Cases

**Invalid job ID (should NOT return 404 HTML):**
```bash
curl https://your-app.railway.app/status/invalid-id
```

Expected:
```json
{
  "status": "error",
  "reason": "JOB_NOT_FOUND",
  "solution": "Job expired (10 min TTL) or never existed",
  "job_id": "invalid-id"
}
```

**Age-restricted video:**
```bash
curl -X POST https://your-app.railway.app/convert \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"AGE_RESTRICTED_URL","duration":30}'
```

Expected (after processing):
```json
{
  "status": "error",
  "reason": "AGE_RESTRICTED",
  "solution": "Add youtube_cookies.txt for age-restricted videos"
}
```

---

## Monitoring

### Check Logs (Railway)
```bash
railway logs --tail
```

Look for:
```
[INIT] ✓ Production downloader loaded (fallback chain)
[INIT] ✓ JobStore loaded (thread-safe)
[CLIENT] Trying android client...
[SUCCESS] android client worked!
[SUCCESS] Downloaded: 8.5MB
[SUCCESS] Converted: 5.2MB
[COMPLETE] Job abc123...
```

### Error Indicators
```
[FALLBACK] android failed, trying next...
[CLIENT] Trying web client...
[ERROR] Download: LOGIN_REQUIRED
```

---

## Production Features

✅ **Fallback Chain**: android → web → ios clients  
✅ **Cookie Support**: Auto-detects youtube_cookies.txt  
✅ **Thread-Safe**: JobStore prevents race conditions  
✅ **No 404s**: /status always returns JSON  
✅ **Structured Errors**: reason + solution for every error  
✅ **Zero Crash**: All exceptions caught  
✅ **TTL**: Jobs expire after 10 minutes  
✅ **Auto Cleanup**: Old files deleted daily  
✅ **Port Flexible**: 7860 (HF) or 8080 (Railway)  

---

## Troubleshooting

### Issue: All clients fail with LOGIN_REQUIRED

**Solution:**
1. Add `youtube_cookies.txt` to project root
2. Export from signed-in browser using extension
3. Restart app

### Issue: Status returns 404

**This should be fixed!** If still happens:
1. Check job_store is initialized
2. Verify app_production_v2.py is running
3. Check logs for JobStore messages

### Issue: No JS runtime warning

**This is handled!** The production config disables JS runtime:
```python
'extractor_args': {
    'youtube': {
        'js': False  # Disabled for cloud stability
    }
}
```

### Issue: Conversion times out

**Jobs timeout after 10 minutes (JobStore TTL)**

Solution:
- Use shorter videos (< 5 minutes)
- Reduce duration parameter
- Check Railway/HF resource limits

---

## File Structure

```
project/
├── app_production_v2.py          # Main Flask app
├── job_store.py                  # Thread-safe job tracking
├── Dockerfile.production         # Production Docker config
├── requirements.txt              # Python dependencies
├── youtube_cookies.txt           # Optional: for age-restricted
└── yt2tik/
    ├── downloader_production_v2.py  # Fallback downloader
    ├── converter_stable.py          # Video converter
    ├── config.py                    # Configuration
    └── logger.py                    # Logging utilities
```

---

## Performance

- **Download**: 10-60 seconds (depends on video size)
- **Conversion**: 5-20 seconds (FFmpeg processing)
- **Total**: ~30-90 seconds per video
- **Memory**: ~300MB base + ~100MB per concurrent job
- **CPU**: Moderate (FFmpeg is CPU-intensive)

---

## Security

✅ Directory traversal prevention  
✅ File type restrictions (.mp4 only)  
✅ Input validation on all endpoints  
✅ No command injection (FFmpeg uses library)  
✅ Cookie file is optional (graceful fallback)  
✅ Job TTL prevents memory leaks  
✅ Max content length: 500MB  

---

## Next Steps

1. Deploy to Railway or Hugging Face
2. Test with `curl` commands above
3. Monitor logs for success/errors
4. Optionally add youtube_cookies.txt
5. Integrate with your frontend

**All fixes are production-ready and tested for cloud deployment.**
