# Production Deployment Guide - YouTube to TikTok Converter

## 🎯 What Was Fixed

### 1. yt-dlp Issues ✅
- **Problem**: "Sign in to confirm you're not a bot" errors
- **Solution**: 
  - Proper error detection for age-restricted, private, members-only videos
  - Clear user-facing error messages
  - No bypass attempts (legal & safe)
  - Automatic retry logic for temporary failures only

### 2. /status Endpoint 404 ✅
- **Problem**: Job tracking system unreliable, returns 404
- **Solution**:
  - Thread-safe `JobStore` class
  - 1-hour TTL for jobs
  - Automatic cleanup of expired jobs
  - Timeout detection (10 minutes max)

### 3. App Stability ✅
- **Problem**: App crashes on errors
- **Solution**:
  - Zero-crash architecture: ALL exceptions caught
  - Background threads use safe wrapper
  - JSON error responses (never crashes)
  - Graceful degradation if modules missing

### 4. Conversion Pipeline ✅
- **Problem**: Unstable FFmpeg execution
- **Solution**:
  - Timeout protection (10 minutes)
  - Input validation
  - Output verification
  - Automatic cleanup of temporary files

---

## 📦 Files Created

### 1. `yt2tik/downloader_production.py`
Production-ready YouTube downloader with:
- VideoRestrictionError: Age-restricted, members-only, login-required
- VideoUnavailableError: Private, deleted, region-blocked
- Automatic retry for temporary failures (network, timeouts)
- Clear error messages for each scenario
- Optional cookies.txt support (user-provided)

### 2. `app.py`
Simple production API server with:
- Thread-safe job tracking
- Zero-crash error handling
- Automatic file cleanup
- RESTful API endpoints
- Health check endpoint

---

## 🚀 Quick Deploy to Railway

### Step 1: Choose Your App

**Option A: Simple API (Recommended)**
```bash
# Use app.py - minimal, fast, API-only
```

**Option B: Full Web App**
```bash
# Use integrated_app.py - includes web UI, analyzer, OAuth
```

### Step 2: Update Dockerfile

Replace the CMD line in your Dockerfile:

**For app.py (Simple API):**
```dockerfile
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --access-logfile - --error-logfile -
```

**For integrated_app.py (Full Web App):**
```dockerfile
CMD gunicorn integrated_app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --access-logfile - --error-logfile -
```

### Step 3: Update Procfile

```
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
```

### Step 4: Deploy

```bash
git add .
git commit -m "Production-ready deployment with fixed yt-dlp and job tracking"
git push railway master
```

### Step 5: Monitor

```bash
railway logs --tail
```

---

## 🧪 Testing Your Deployment

### Test 1: Health Check

```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "downloader": true,
  "converter": true,
  "jobs_count": 0,
  "timestamp": "2024-06-06T12:00:00Z"
}
```

### Test 2: Convert a Public Video

```bash
curl -X POST https://your-app.railway.app/convert \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "duration": 30
  }'
```

Expected response:
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Processing started",
  "status_url": "/status/550e8400-e29b-41d4-a716-446655440000"
}
```

### Test 3: Check Status

```bash
curl https://your-app.railway.app/status/550e8400-e29b-41d4-a716-446655440000
```

Poll this endpoint every 5 seconds until status is "completed" or "error".

### Test 4: Age-Restricted Video (Should Fail Gracefully)

```bash
curl -X POST https://your-app.railway.app/convert \
  -H "Content-Type: application/json" \
  -d '{
    "youtube_url": "https://www.youtube.com/watch?v=SOME_AGE_RESTRICTED_ID"
  }'
```

Expected: Job completes with error status and clear message about age restriction.

---

## 📊 API Endpoints

### GET /
Home/documentation endpoint

### GET /health
Health check for monitoring

### POST /convert
Start conversion job
- Body: `{youtube_url, start_time?, duration?, caption?}`
- Returns: `{job_id, status_url}`

### GET /status/<job_id>
Check job status
- Returns: `{status, progress, message, video_url?}`

### GET /download/<filename>
Download converted video

---

## 🔍 Error Handling Examples

### Age-Restricted Video
```json
{
  "status": "error",
  "message": "❌ Video Restricted: This video requires sign-in (age-restricted). Provide cookies.txt or try a different video."
}
```

### Private Video
```json
{
  "status": "error",
  "message": "❌ Video Unavailable: This video is private and cannot be accessed."
}
```

### Members-Only Video
```json
{
  "status": "error",
  "message": "❌ Video Restricted: This is a members-only video. Try a different video."
}
```

### Network Timeout
```json
{
  "status": "error",
  "message": "❌ Download timeout. Try a shorter video."
}
```

### Processing Timeout
```json
{
  "status": "error",
  "message": "Processing timeout. Please try a shorter video."
}
```

---

## 🛠️ Troubleshooting

### Issue: Still getting bot detection errors

**Cause**: Video requires authentication

**Solutions**:
1. Try a different public video (most videos work)
2. Provide cookies.txt from logged-in browser (optional)
3. Wait a few minutes if you hit rate limits

### Issue: Jobs disappear (404)

**Cause**: Job expired (1 hour TTL)

**Solution**: Jobs are kept for 1 hour. After that, they're cleaned up to prevent memory issues.

### Issue: Conversion fails immediately

**Check**:
1. Railway logs: `railway logs --tail`
2. FFmpeg is installed: Check Dockerfile
3. Video URL is valid
4. Video is not restricted

### Issue: Slow conversions

**Optimize**:
- Use shorter videos (< 3 minutes source)
- Keep duration at 30 seconds
- Railway free tier has resource limits

---

## 💾 Optional: Cookies Support

For age-restricted videos, you can optionally provide cookies:

### Step 1: Export Cookies

1. Install browser extension: "Get cookies.txt LOCALLY"
2. Visit YouTube while logged in
3. Click extension → Export cookies
4. Save as `youtube_cookies.txt`

### Step 2: Upload to Railway

```bash
# Add to project root
cp youtube_cookies.txt /app/youtube_cookies.txt

# Or set as Railway file
railway run --mount /app/youtube_cookies.txt
```

### Step 3: Update Downloader Call

The production downloader automatically detects `youtube_cookies.txt` in the config path.

**Note**: Cookies are OPTIONAL. Most videos work without them.

---

## 📈 Monitoring

### Railway Dashboard

Monitor:
- CPU usage
- Memory usage
- Request count
- Error rate

### Custom Monitoring

Add to your app:

```python
@app.route('/metrics')
def metrics():
    return jsonify({
        'active_jobs': len([j for j in job_store.jobs.values() if j['status'] == 'processing']),
        'total_jobs': len(job_store.jobs),
        'completed_jobs': len([j for j in job_store.jobs.values() if j['status'] == 'completed']),
        'failed_jobs': len([j for j in job_store.jobs.values() if j['status'] == 'error']),
    })
```

---

## 🔐 Security Checklist

- ✅ No YouTube bypass techniques
- ✅ Directory traversal prevention
- ✅ Input validation on all endpoints
- ✅ File type restrictions (.mp4 only)
- ✅ Timeout limits (prevents abuse)
- ✅ Automatic file cleanup
- ✅ Thread-safe operations

---

## 🎯 Next Steps (Optional Enhancements)

1. **Redis Integration**: Replace in-memory job store
2. **S3 Storage**: Store videos in cloud storage
3. **Rate Limiting**: Prevent abuse
4. **API Keys**: Add authentication
5. **Webhooks**: Notify when job completes
6. **Queue System**: Use Celery/RQ for background jobs

---

## 📞 Support

### Check Logs

```bash
# Railway
railway logs --tail

# Local
python app.py
```

### Common Issues

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Sign in to confirm" | Age-restricted video | Use public video or add cookies |
| "Video unavailable" | Deleted/private | Try different video |
| "Processing timeout" | Video too long | Use shorter video |
| "Job not found" | Job expired | Jobs expire after 1 hour |
| "Download failed after N attempts" | Network issue | Retry or check connection |

---

## ✅ Deployment Checklist

Before deploying:

- [ ] Dockerfile CMD uses correct app (app.py or integrated_app.py)
- [ ] Procfile matches Dockerfile CMD
- [ ] FFmpeg installed in Dockerfile
- [ ] Environment variable PORT is used (not hardcoded)
- [ ] requirements.txt includes all dependencies
- [ ] yt-dlp upgraded to latest version
- [ ] Test locally first (`python app.py`)
- [ ] Test /health endpoint works
- [ ] Test /convert with public video
- [ ] Monitor Railway logs during deployment

---

## 🎉 Success Indicators

Your deployment is working if:

✅ `/health` returns `{"status": "healthy"}`  
✅ Public videos convert successfully  
✅ Age-restricted videos show clear error messages  
✅ `/status/<job_id>` never returns 404  
✅ App doesn't crash on any error  
✅ Old files are cleaned up automatically  

---

## 📄 License & Terms

- Respect YouTube's Terms of Service
- No bot detection bypass
- No authentication spoofing
- Clear error messages for restricted content
- Use responsibly
