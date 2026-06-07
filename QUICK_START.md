# 🚀 QUICK START - Get Running in 5 Minutes

## For Impatient Developers 😎

Skip the docs. Just run this.

---

## Local Testing (Windows)

```cmd
test_production.bat
```

Opens at: http://localhost:7860

---

## Local Testing (Linux/Mac)

```bash
chmod +x test_production.sh
./test_production.sh
```

Opens at: http://localhost:7860

---

## Deploy to Railway

1. **Push code to GitHub**
2. **Go to [railway.app](https://railway.app)**
3. **New Project → Deploy from GitHub repo**
4. **Add environment variables:**
   ```
   FLASK_SECRET_KEY=your-random-secret-key-here
   ENABLE_YOUTUBE_COOKIES=false
   ```
5. **Deploy** (automatic)

Done. Your app is live.

---

## Deploy to Hugging Face

1. **Rename Dockerfile:**
   ```bash
   cp Dockerfile.production_fixed Dockerfile
   ```

2. **Push to HF Space:**
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
   git push space main
   ```

3. **Add secrets in Space settings:**
   ```
   FLASK_SECRET_KEY=your-random-secret
   ENABLE_YOUTUBE_COOKIES=false
   ```

Done. Your Space is live.

---

## Test Your Deployment

```bash
# Replace YOUR_URL with your Railway/HF URL
curl https://YOUR_URL/health
```

Should return:
```json
{"status": "healthy"}
```

---

## What Files to Use

| File | Use This |
|------|----------|
| Main app | `app_production.py` |
| Dockerfile | `Dockerfile.production_fixed` |
| Environment | `.env.production` (copy to `.env` and configure) |

---

## Need Help?

- **Full guide:** `DEPLOYMENT_PRODUCTION.md`
- **Quick reference:** `PRODUCTION_SUMMARY.md`
- **Troubleshooting:** `DEPLOYMENT_PRODUCTION.md` → Troubleshooting section

---

## That's It! 🎉

Your production-ready YouTube to TikTok converter is ready to deploy.

No more LOGIN_REQUIRED. No more crashes. Just works.
