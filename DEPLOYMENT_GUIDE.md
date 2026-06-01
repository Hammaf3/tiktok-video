# 🚀 Complete Deployment Guide

## ⚠️ Important: Vercel Kaam Nahi Karega

Aapka app Vercel par **NAHI** chal sakta kyunki:
- Video processing 2-5 minutes leta hai (Vercel limit: 10-60 seconds)
- FFmpeg binary chahiye (Vercel mein nahi hai)
- File storage chahiye (Vercel read-only hai)

## ✅ Recommended: Railway.app

Railway.app perfect hai is app ke liye. Yahan step-by-step guide hai.

---

## 🎯 Railway.app Deployment

### Step 1: Prerequisites

1. **GitHub Account** (already hai aapke paas)
2. **Railway Account** - Sign up at https://railway.app
3. **Code Push Karo GitHub Par:**
   ```bash
   git add .
   git commit -m "Prepare for Railway deployment"
   git push origin master
   ```

### Step 2: Railway Setup

1. **Railway.app Par Jao:**
   - https://railway.app par jao
   - "Login" → "Login with GitHub" click karo

2. **New Project Banao:**
   - Dashboard mein "New Project" click karo
   - "Deploy from GitHub repo" select karo
   - Apni repository select karo: `tiktok-video-uploader`

3. **Railway Auto-Detect Karega:**
   - Railway automatically detect karega ki ye Flask app hai
   - Python environment setup ho jayega

### Step 3: Environment Variables Setup

Railway dashboard mein "Variables" tab par jao aur ye add karo:

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here-change-this

# TikTok API (Required for uploads)
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret
TIKTOK_ACCESS_TOKEN=your_tiktok_access_token

# YouTube API (Required for analyzer)
YOUTUBE_API_KEY=your_youtube_api_key

# YouTube Cookies (For age-restricted videos)
YOUTUBE_COOKIES_BASE64=your_base64_encoded_cookies
```

### Step 4: Add Buildpacks (Important!)

Railway mein FFmpeg install karne ke liye:

1. **Settings Tab Par Jao**
2. **"Build Command" Mein Ye Add Karo:**
   ```bash
   apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
   ```

3. **"Start Command" Mein Ye Add Karo:**
   ```bash
   python web_app.py
   ```

### Step 5: Deploy!

1. **Deploy Button Click Karo**
2. **Wait Karo** (2-3 minutes)
3. **Logs Check Karo** - "Deployments" tab mein
4. **URL Milega** - Railway automatically public URL dega

---

## 🍪 Age-Restricted Videos Setup

Age-restricted videos ke liye cookies chahiye. Do options hain:

### Option 1: Environment Variable (Recommended)

1. **Cookies Export Karo** (dekho `COOKIES_SETUP.md`)
2. **Base64 Encode Karo:**
   ```bash
   # Windows PowerShell
   $content = Get-Content youtube_cookies.txt -Raw
   $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
   $encoded = [Convert]::ToBase64String($bytes)
   echo $encoded
   ```

3. **Railway Mein Add Karo:**
   - Variables tab → Add Variable
   - Name: `YOUTUBE_COOKIES_BASE64`
   - Value: (encoded string paste karo)

### Option 2: Direct File Upload

1. **Cookies File Ko Git Mein Add Karo:**
   ```bash
   git add youtube_cookies.txt
   git commit -m "Add YouTube cookies"
   git push
   ```

2. **Railway Auto-Deploy Karega**

---

## 🔧 Post-Deployment Configuration

### 1. Check Deployment Status

```bash
# Railway CLI install karo (optional)
npm i -g @railway/cli

# Login karo
railway login

# Logs dekho
railway logs
```

### 2. Test Your Deployment

```bash
# Health check
curl https://your-app.railway.app/health

# Test conversion (browser mein)
https://your-app.railway.app
```

### 3. Custom Domain (Optional)

1. Railway dashboard → Settings → Domains
2. "Add Custom Domain" click karo
3. Apna domain add karo
4. DNS settings update karo (Railway instructions dega)

---

## 🐛 Common Issues & Solutions

### Issue 1: "FFmpeg not found"

**Solution:**
```bash
# Build command mein ye add karo:
apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt
```

### Issue 2: "Age-restricted video error"

**Solution:**
- Cookies setup karo (dekho `COOKIES_SETUP.md`)
- Environment variable `YOUTUBE_COOKIES_BASE64` add karo

### Issue 3: "TikTok upload failed"

**Solution:**
- Check karo TikTok API credentials sahi hain
- Access token expire to nahi ho gaya?
- TikTok Developer Portal mein token refresh karo

### Issue 4: "Application timeout"

**Solution:**
- Railway mein timeout nahi hota (unlike Vercel)
- Agar phir bhi issue hai to logs check karo

### Issue 5: "Out of memory"

**Solution:**
- Railway dashboard → Settings → Resources
- Memory limit increase karo (512MB → 1GB)

---

## 💰 Cost Estimate

### Railway.app Pricing:

- **Free Tier:** $5 credit/month (limited hours)
- **Hobby Plan:** $5/month (unlimited)
- **Pro Plan:** $20/month (more resources)

**Recommendation:** Start with Hobby plan ($5/month)

---

## 📊 Alternative Platforms

Agar Railway nahi use karna:

### 1. Render.com

**Pros:**
- Free tier available
- Easy setup
- Good documentation

**Cons:**
- Free tier slow hai
- Cold starts (app sleep ho jata hai)

**Setup:**
```bash
# render.yaml banao
services:
  - type: web
    name: yt2tik
    env: python
    buildCommand: "apt-get update && apt-get install -y ffmpeg && pip install -r requirements.txt"
    startCommand: "python web_app.py"
```

### 2. Fly.io

**Pros:**
- Global deployment
- Fast performance
- Good free tier

**Cons:**
- Thoda complex setup

**Setup:**
```bash
# Fly CLI install karo
curl -L https://fly.io/install.sh | sh

# Deploy karo
fly launch
fly deploy
```

### 3. DigitalOcean App Platform

**Pros:**
- Reliable
- Good support
- Predictable pricing

**Cons:**
- No free tier
- $5/month minimum

---

## ✅ Deployment Checklist

### Pre-Deployment:
- [ ] Code GitHub par push kiya
- [ ] `.env` file mein saari credentials hain
- [ ] Local testing ki (localhost par kaam kar raha hai)
- [ ] Cookies export kiye (agar age-restricted videos chahiye)

### Railway Setup:
- [ ] Railway account banaya
- [ ] GitHub se connect kiya
- [ ] Repository select kiya
- [ ] Environment variables add kiye
- [ ] Build command set kiya (FFmpeg install)
- [ ] Start command set kiya

### Post-Deployment:
- [ ] Deployment successful (logs check kiye)
- [ ] Health endpoint test kiya
- [ ] Video conversion test kiya
- [ ] Age-restricted video test kiya (agar cookies add kiye)
- [ ] TikTok upload test kiya

---

## 🎯 Quick Deploy Commands

```bash
# 1. Prepare code
git add .
git commit -m "Ready for deployment"
git push origin master

# 2. Railway CLI (optional)
npm i -g @railway/cli
railway login
railway link
railway up

# 3. Check status
railway status
railway logs

# 4. Open in browser
railway open
```

---

## 📝 Environment Variables Template

Railway dashboard mein copy-paste karo:

```
FLASK_SECRET_KEY=change-this-to-random-string
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_ACCESS_TOKEN=
YOUTUBE_API_KEY=
YOUTUBE_COOKIES_BASE64=
```

---

## 🆘 Need Help?

1. **Check Logs:**
   - Railway dashboard → Deployments → View Logs

2. **Check Local Logs:**
   - `logs/` directory mein detailed logs hain

3. **Test Locally First:**
   ```bash
   python web_app.py
   # Browser mein: http://localhost:5000
   ```

4. **Common Error Messages:**
   - "FFmpeg not found" → Build command check karo
   - "Age-restricted" → Cookies add karo
   - "401 Unauthorized" → TikTok token refresh karo

---

**🎉 Deployment successful hone ke baad aapka app live hoga!**

Your app URL: `https://your-app-name.railway.app`
