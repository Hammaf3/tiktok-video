# 🚀 Railway.app Deployment Guide

## Why Railway Instead of Vercel?

Your application **cannot work on Vercel** because:
- ❌ Video processing takes 2-5 minutes (Vercel timeout: 10-60 seconds)
- ❌ Needs file storage for videos (Vercel: read-only filesystem)
- ❌ Uses background threading (Vercel: stateless functions)
- ❌ Requires FFmpeg binary (not available in Vercel)

**Railway.app is perfect** because:
- ✅ No execution time limits
- ✅ Persistent file storage
- ✅ FFmpeg pre-installed
- ✅ Supports long-running processes
- ✅ Easy deployment from GitHub
- ✅ Cost: ~$5/month (free trial available)

---

## 📋 Prerequisites

1. **GitHub Account** - Your code needs to be on GitHub
2. **Railway Account** - Sign up at https://railway.app
3. **Environment Variables** - Have your `.env` file ready

---

## 🎯 Step-by-Step Deployment

### Step 1: Push Code to GitHub

If you haven't already:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### Step 2: Sign Up for Railway

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Sign in with GitHub
4. Authorize Railway to access your repositories

### Step 3: Deploy from GitHub

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: `tiktok-video-uploader`
4. Railway will automatically detect it's a Python/Flask app

### Step 4: Add Environment Variables

Click on your project → **"Variables"** tab → Add these:

```
FLASK_SECRET_KEY=your-secret-key-here
YOUTUBE_API_KEY=your-youtube-api-key
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
TIKTOK_ACCESS_TOKEN=your-tiktok-access-token
TIKTOK_REFRESH_TOKEN=your-tiktok-refresh-token
PORT=5000
```

**Important:** Copy these from your local `.env` file!

### Step 5: Configure Build Settings (Optional)

Railway auto-detects settings, but you can customize:

1. Go to **"Settings"** tab
2. **Build Command**: `pip install -r requirements.txt` (auto-detected)
3. **Start Command**: `gunicorn integrated_app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300` (from Procfile)

### Step 6: Deploy!

1. Railway will automatically start building
2. Watch the build logs in real-time
3. Build takes ~2-3 minutes
4. Once deployed, you'll get a public URL like: `https://your-app.up.railway.app`

### Step 7: Update OAuth Redirect URIs

**Important:** Update your OAuth callback URLs:

#### YouTube OAuth:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to your project → APIs & Services → Credentials
3. Edit your OAuth 2.0 Client ID
4. Add authorized redirect URI: `https://your-app.up.railway.app/youtube/callback`

#### TikTok OAuth:
1. Go to [TikTok Developer Portal](https://developers.tiktok.com/)
2. Navigate to your app settings
3. Add redirect URI: `https://your-app.up.railway.app/tiktok/callback`

---

## 🔧 Troubleshooting

### Build Fails

**Check logs:**
- Click on your deployment
- View **"Build Logs"**
- Look for error messages

**Common issues:**
- Missing dependencies in `requirements.txt` → Add them
- Python version mismatch → Check `runtime.txt`

### App Crashes After Deploy

**Check runtime logs:**
- Click **"View Logs"** in Railway dashboard
- Look for Python errors

**Common issues:**
- Missing environment variables → Add them in Variables tab
- Port binding issue → Railway sets `$PORT` automatically
- Import errors → Make sure all files are committed to GitHub

### FFmpeg Not Found

Railway includes FFmpeg by default, but if you get errors:

Add a `nixpacks.toml` file:

```toml
[phases.setup]
aptPkgs = ["ffmpeg"]
```

### File Storage Issues

Railway provides persistent storage, but files in `/tmp` are cleared on restart.

**Solution:** Use the configured directories:
- Downloads: `tmp/yt2tik/downloads`
- Output: `tmp/yt2tik/output`

These are created automatically by your app.

---

## 💰 Pricing

**Free Trial:**
- $5 free credit
- No credit card required
- Perfect for testing

**Hobby Plan:**
- $5/month
- Includes:
  - 512MB RAM
  - 1GB storage
  - Unlimited bandwidth
  - Custom domains

**Pro Plan:**
- $20/month
- More resources if needed

---

## 🎉 Post-Deployment

### Test Your App

1. Visit your Railway URL
2. Test YouTube search
3. Test video conversion
4. Test TikTok upload
5. Check OAuth flows work

### Monitor Your App

Railway dashboard shows:
- CPU usage
- Memory usage
- Request logs
- Error logs
- Deployment history

### Custom Domain (Optional)

1. Go to **"Settings"** → **"Domains"**
2. Click **"Add Domain"**
3. Enter your domain
4. Update DNS records as shown
5. SSL certificate auto-generated

---

## 🔄 Updating Your App

After making code changes:

```bash
git add .
git commit -m "Your update message"
git push
```

Railway automatically:
1. Detects the push
2. Rebuilds your app
3. Deploys the new version
4. Zero-downtime deployment

---

## 📊 Comparison: Vercel vs Railway

| Feature | Vercel | Railway |
|---------|--------|---------|
| Execution Time | 10-60s max | Unlimited |
| File Storage | Read-only | Persistent |
| Background Jobs | ❌ No | ✅ Yes |
| FFmpeg | ❌ No | ✅ Yes |
| Video Processing | ❌ No | ✅ Yes |
| Cost | Free tier | $5/month |
| Best For | Static sites, APIs | Full-stack apps |

---

## 🆘 Need Help?

**Railway Support:**
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app
- Status: https://status.railway.app

**Your App Issues:**
- Check Railway logs first
- Verify environment variables
- Test locally with `gunicorn integrated_app:app`

---

## ✅ Checklist

Before deploying, make sure:

- [ ] Code is pushed to GitHub
- [ ] All dependencies in `requirements.txt`
- [ ] `Procfile` exists and correct
- [ ] `.env` variables ready to copy
- [ ] Railway account created
- [ ] OAuth redirect URIs will be updated

After deploying:

- [ ] App builds successfully
- [ ] App starts without errors
- [ ] Can access the homepage
- [ ] YouTube search works
- [ ] Video conversion works
- [ ] OAuth flows updated and working

---

## 🎯 Quick Start (TL;DR)

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to Railway"
git push

# 2. Go to railway.app
# 3. New Project → Deploy from GitHub
# 4. Select your repo
# 5. Add environment variables
# 6. Wait 2-3 minutes
# 7. Done! 🎉
```

Your app will be live at: `https://your-app.up.railway.app`

---

**Note:** The current Vercel deployment will show an informational page explaining why it can't work. Once you deploy to Railway, you can delete the Vercel project.
