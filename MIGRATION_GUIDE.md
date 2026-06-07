# 🔄 MIGRATION GUIDE - Switch to Production Code

## From Old Code → Production Code

This guide helps you migrate from your current implementation to the production-ready version.

---

## 📊 What Changed

### File Changes

| Old File | New File | Action |
|----------|----------|--------|
| `integrated_app.py` | `app_production.py` | **Replace** (import new downloader) |
| `yt2tik/downloader.py` | `yt2tik/downloader_production.py` | **Add** (keep old for reference) |
| `Dockerfile` | `Dockerfile.production_fixed` | **Replace** or rename |
| `.env` | `.env.production` | **Template** (copy and configure) |
| - | `test_production.bat/.sh` | **New** testing scripts |
| - | `DEPLOYMENT_PRODUCTION.md` | **New** documentation |

### Code Changes

| Component | Old Behavior | New Behavior |
|-----------|--------------|--------------|
| **Downloader** | Single android client, crashes on LOGIN_REQUIRED | Multi-client fallback, never crashes |
| **Error handling** | Generic exceptions | Structured `{reason, solution}` JSON |
| **Job status** | Returns 404 when job not found | Returns error JSON (200 status) |
| **Cookie support** | Always tries to use cookies | Optional via environment variable |
| **JS runtime** | Uses default (causes warnings) | Explicitly disabled |
| **Format selection** | Complex merging | Simple pre-merged formats |

---

## 🔧 Step-by-Step Migration

### Step 1: Backup Current Code

```bash
# Create backup branch
git checkout -b backup-before-production
git add .
git commit -m "Backup before production migration"
git checkout master
```

### Step 2: Verify New Files Exist

Check that these files were created:

```bash
# Check new files
ls -la app_production.py
ls -la yt2tik/downloader_production.py
ls -la Dockerfile.production_fixed
ls -la .env.production
ls -la DEPLOYMENT_PRODUCTION.md
```

All should exist. If missing, re-run the production fix script.

### Step 3: Update Imports (if modifying existing files)

**Option A: Use Production Files Directly (Recommended)**

Just use the new files without modifying the old ones:
- Run `app_production.py` instead of `integrated_app.py`
- Deploy with `Dockerfile.production_fixed`
- No code changes needed

**Option B: Update Existing integrated_app.py**

If you want to keep using `integrated_app.py`, change the import:

```python
# OLD (Line 40-45 in integrated_app.py)
try:
    from yt2tik.downloader_fixed import download_youtube_video
    # or
    from yt2tik.downloader import download_youtube_video
```

Change to:

```python
# NEW
try:
    from yt2tik.downloader_production import download_youtube_video, DownloadError
```

### Step 4: Update Error Handling

If you modified error handling in `integrated_app.py`, update it to handle `DownloadError`:

```python
# NEW error handling in process_video()
try:
    video_data = download_youtube_video(youtube_url)
    # ... rest of code
except DownloadError as e:
    # Structured error from production downloader
    update_status('error', 0, str(e), reason=e.reason, solution=e.solution)
    return
except Exception as e:
    # Generic error
    update_status('error', 0, f'Download failed: {str(e)}',
                  reason='DOWNLOAD_FAILED',
                  solution='Check video URL or try a different video')
    return
```

### Step 5: Update Status Endpoint

In `integrated_app.py`, change `/status/<job_id>` to never return 404:

```python
# OLD
@app.route('/status/<job_id>')
def get_status(job_id):
    job_data = job_store.get_job(job_id)
    if not job_data:
        return jsonify({'error': 'Job not found'}), 404  # ❌ Bad
    return jsonify(job_data), 200

# NEW
@app.route('/status/<job_id>')
def get_status(job_id):
    job_data = job_store.get_job(job_id)
    if not job_data:
        return jsonify({
            'status': 'error',
            'job_id': job_id,
            'reason': 'JOB_NOT_FOUND',
            'solution': 'Job may have expired (1 hour TTL)',
            'message': 'Job not found'
        }), 200  # ✅ Return 200, not 404
    return jsonify(job_data), 200
```

### Step 6: Update Environment Variables

Copy template and configure:

```bash
# Create your .env from template
cp .env.production .env

# Edit .env and set:
# - FLASK_SECRET_KEY=your-random-secret
# - ENABLE_YOUTUBE_COOKIES=false (for cloud)
```

### Step 7: Update Dockerfile

**Option A: Rename (Recommended)**

```bash
# Backup old Dockerfile
mv Dockerfile Dockerfile.old

# Use production Dockerfile
cp Dockerfile.production_fixed Dockerfile
```

**Option B: Update Existing Dockerfile**

Change the CMD line:

```dockerfile
# OLD
CMD gunicorn integrated_app:app --bind 0.0.0.0:$PORT ...

# NEW
CMD gunicorn app_production:app --bind 0.0.0.0:${PORT:-7860} ...
```

### Step 8: Test Locally

```bash
# Windows
test_production.bat

# Linux/Mac
./test_production.sh
```

Expected output:
```
✅ Production downloader loaded (multi-client fallback)
✅ JobStore loaded (thread-safe)
🚀 PRODUCTION YouTube to TikTok Converter
```

### Step 9: Test API

```bash
# Test health
curl http://localhost:7860/health

# Test conversion
curl -X POST http://localhost:7860/convert \
  -H "Content-Type: application/json" \
  -d '{"youtube_url":"https://youtube.com/watch?v=dQw4w9WgXcQ","duration":30}'
```

Should return `{"success": true, "job_id": "..."}` without errors.

### Step 10: Deploy

```bash
# Commit production code
git add .
git commit -m "Migrate to production-ready code"
git push

# Deploy to Railway/HF (auto-rebuilds)
```

---

## 🔍 Verification Checklist

After migration, verify:

### ✅ Code Verification

- [ ] `app_production.py` is being used (or imports updated)
- [ ] `downloader_production.py` is imported
- [ ] `DownloadError` exception is caught
- [ ] Status endpoint returns 200 (not 404)
- [ ] Error responses include `{reason, solution}`
- [ ] Environment variables configured

### ✅ Local Testing

- [ ] Server starts without errors
- [ ] Health endpoint returns `{"status": "healthy"}`
- [ ] Public video conversion works
- [ ] Error messages are structured JSON
- [ ] Jobs persist and don't disappear
- [ ] Frontend receives proper error messages

### ✅ Deployment Testing

- [ ] Docker build succeeds
- [ ] Container starts without errors
- [ ] Logs show "Production downloader loaded"
- [ ] Public videos work
- [ ] Age-restricted videos fail gracefully
- [ ] No LOGIN_REQUIRED errors on cloud
- [ ] Status polling works (no 404)

---

## 🐛 Common Migration Issues

### Issue: Import Error

**Error:** `ModuleNotFoundError: No module named 'yt2tik.downloader_production'`

**Solution:**
```bash
# Verify file exists
ls yt2tik/downloader_production.py

# If missing, create it from the production fix
# (Re-run production setup or copy from backup)
```

### Issue: DownloadError Not Defined

**Error:** `NameError: name 'DownloadError' is not defined`

**Solution:**
```python
# Add to imports
from yt2tik.downloader_production import download_youtube_video, DownloadError
```

### Issue: Old Behavior Still Happening

**Cause:** Still using old files

**Solution:**
```bash
# Check which file is running
ps aux | grep python  # Look for app_production.py or integrated_app.py

# Make sure gunicorn points to production app
# In Dockerfile: CMD gunicorn app_production:app ...
```

### Issue: Environment Variables Not Working

**Cause:** `.env` not loaded or Railway/HF not configured

**Solution:**
```bash
# Local: Check .env exists
ls -la .env

# Cloud: Check Railway/HF dashboard → Environment Variables
# Must have: ENABLE_YOUTUBE_COOKIES=false
```

---

## 🔄 Rollback Plan

If something goes wrong:

### Quick Rollback

```bash
# Switch to backup branch
git checkout backup-before-production

# Redeploy
git push --force
```

### Partial Rollback

Keep production fixes but revert specific changes:

```bash
# Revert specific file
git checkout backup-before-production -- integrated_app.py

# Or restore from backup
cp integrated_app.py.backup integrated_app.py
```

---

## 📊 Before/After Comparison

### API Response Comparison

**Before (Old Code):**
```json
// Error - returns 404
{
  "error": "Job not found"
}

// Download error - generic
{
  "error": "Download failed: Sign in to confirm you're not a bot"
}
```

**After (Production Code):**
```json
// Error - returns 200 with structured data
{
  "status": "error",
  "job_id": "abc-123",
  "reason": "JOB_NOT_FOUND",
  "solution": "Job may have expired (1 hour TTL)",
  "message": "Job not found"
}

// Download error - structured with solution
{
  "status": "error",
  "reason": "BOT_DETECTION",
  "solution": "Cookies may be invalid. Try refreshing cookies or use a different video.",
  "message": "YouTube bot detection triggered"
}
```

### Log Comparison

**Before:**
```
WARNING: js_runtimes not set, using default
ERROR: Sign in to confirm you're not a bot
Traceback (most recent call last):
  ... crash ...
```

**After:**
```
✅ Production downloader loaded (multi-client fallback)
✅ js_runtimes forced to {} - Android client pure mode
🔄 Attempt 1/4: client=android, cookies=false
📹 Video: Example Video (120s)
✅ Download complete: example.mp4 (45.2 MB)
[SUCCESS] Job abc-123 completed
```

---

## ✅ Migration Complete!

Once all checks pass, your migration is complete. You now have:

- ✅ Stable cloud deployment
- ✅ Multi-client fallback
- ✅ Structured error handling
- ✅ Thread-safe job tracking
- ✅ Zero-crash architecture

**Next Steps:**
1. Monitor logs for 24 hours
2. Check error rates decreased
3. Verify user complaints reduced
4. Remove old backup files after 1 week

---

**Need help?** See `DEPLOYMENT_PRODUCTION.md` for detailed troubleshooting.
