# Vercel Deployment Issues

## Current Error
`500: INTERNAL_SERVER_ERROR - FUNCTION_INVOCATION_FAILED`

## Root Causes

Your application has **fundamental architectural incompatibilities** with Vercel's serverless platform:

### 1. ❌ Background Threading
```python
thread = threading.Thread(target=process_video, ...)
thread.start()
```
- **Problem**: Serverless functions are stateless and short-lived
- **Impact**: Background threads are killed when the function returns
- **Result**: Video processing never completes

### 2. ❌ File System Access
```python
OUTPUT_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'output'
DOWNLOAD_DIR = BASE_DIR / 'tmp' / 'yt2tik' / 'downloads'
```
- **Problem**: Vercel functions have read-only file systems (except `/tmp`)
- **Impact**: Cannot write downloaded videos or converted files
- **Limit**: `/tmp` has only 512MB and is cleared between invocations

### 3. ❌ Execution Time Limits
- **Hobby Plan**: 10 seconds max
- **Pro Plan**: 60 seconds max
- **Your app**: Video download + conversion can take 2-5 minutes
- **Result**: Function times out before completion

### 4. ❌ In-Memory State
```python
jobs = {}  # Global dictionary
session['current_job_id'] = job_id
```
- **Problem**: Each serverless invocation is isolated
- **Impact**: Job status tracking doesn't work across requests
- **Result**: Status checks fail because jobs dict is empty

### 5. ❌ FFmpeg Dependency
- **Problem**: FFmpeg binary not included in deployment
- **Impact**: Video conversion fails
- **Solution**: Would need custom build with FFmpeg layer (complex)

### 6. ❌ Session Management
```python
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'integrated-secret-key')
```
- **Problem**: Flask sessions stored in cookies, but OAuth flows need server-side storage
- **Impact**: TikTok/YouTube OAuth callbacks may fail

## Solutions

### Option A: Refactor for Serverless (Complex)
**Required Changes:**
1. Replace threading with external queue system (AWS SQS, Redis Queue, Celery)
2. Use cloud storage (AWS S3, Cloudflare R2) for video files
3. Use external database (Redis, PostgreSQL) for job tracking
4. Split into multiple functions:
   - API endpoint (triggers job)
   - Worker function (processes video)
   - Status endpoint (checks job)
5. Add FFmpeg layer or use external video processing service
6. Implement webhook-based status updates

**Estimated Effort**: 2-3 days of development

**Additional Costs**:
- Cloud storage: ~$5-20/month
- Database: ~$5-15/month
- Queue system: ~$0-10/month

### Option B: Deploy to Platform-as-a-Service (Recommended)
**Better platforms for this app:**

1. **Railway.app** ⭐ (Recommended)
   - Supports long-running processes
   - Persistent file storage
   - Built-in PostgreSQL/Redis
   - Easy deployment from GitHub
   - Cost: ~$5-10/month

2. **Render.com**
   - Similar to Railway
   - Free tier available (with limitations)
   - Persistent disks
   - Cost: Free or $7+/month

3. **Fly.io**
   - Full VM control
   - Persistent volumes
   - Global deployment
   - Cost: ~$5-15/month

4. **DigitalOcean App Platform**
   - Managed platform
   - Persistent storage
   - Cost: $5+/month

5. **Traditional VPS** (AWS EC2, DigitalOcean Droplet, Linode)
   - Full control
   - No serverless limitations
   - Cost: $5-10/month

### Option C: Hybrid Approach
- Keep Vercel for static frontend/API
- Use separate service for video processing:
  - AWS Lambda with S3 + SQS
  - Google Cloud Functions + Cloud Storage
  - Dedicated worker server

## Immediate Fix for Testing

I've created a simple test endpoint (`api/test.py`) to verify Vercel deployment works at all.

**To test:**
1. Deploy to Vercel
2. Visit your deployment URL
3. If you see `{"status": "ok", "message": "Vercel deployment is working"}`, then Vercel itself works
4. The issue is the architectural incompatibility, not Vercel configuration

## Recommendation

**Switch to Railway.app** - it's the easiest migration path:

1. Push code to GitHub
2. Connect Railway to your repo
3. Add environment variables
4. Deploy (Railway auto-detects Flask apps)
5. Your app will work without any code changes

Vercel is excellent for static sites and simple APIs, but not suitable for:
- Long-running processes
- File processing
- Background jobs
- Stateful applications

Your app needs a traditional server environment, not serverless.
