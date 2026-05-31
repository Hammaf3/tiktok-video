# 🔧 TikTok OAuth Troubleshooting Guide

## Problem: "code_challenge" Error

Agar TikTok OAuth connect nahi ho raha, to ye steps follow karein:

---

## ✅ Solution 1: Updated Code (Already Done)

Main code already update ho gaya hai with PKCE support. 

**Restart karein:**
```bash
# CTRL+C dabao
# Phir:
python web_app.py
```

---

## ✅ Solution 2: TikTok App Settings Check

### Step 1: TikTok Developer Portal
```
https://developers.tiktok.com/
```

### Step 2: Your App > Settings

**Redirect URI must be EXACTLY:**
```
http://localhost:5000/tiktok/callback
```

**Common mistakes:**
- ❌ `http://127.0.0.1:5000/tiktok/callback` (wrong)
- ❌ `http://localhost:5000/callback` (wrong)
- ❌ `https://localhost:5000/tiktok/callback` (https wrong for local)
- ✅ `http://localhost:5000/tiktok/callback` (correct)

### Step 3: Scopes

Enable these scopes:
- ✅ video.upload
- ✅ video.publish
- ✅ user.info.basic (optional)

### Step 4: App Status

App must be:
- ✅ "In Review" or "Live"
- ❌ NOT "Draft"

---

## ✅ Solution 3: Manual Token (Temporary)

Agar OAuth kaam nahi kar raha, to manually token use karein:

### Method A: Developer Portal

1. Go to: https://developers.tiktok.com/
2. Your App > "Tools" > "Generate Access Token"
3. Select scopes: video.upload, video.publish
4. Copy token
5. Paste in `.env`:
   ```env
   TIKTOK_ACCESS_TOKEN=act.xxxxxxxxxxxxxxxxxx
   ```

### Method B: Postman/cURL

```bash
# Step 1: Get authorization code manually
# Open this URL in browser:
https://www.tiktok.com/v2/auth/authorize/?client_key=YOUR_CLIENT_KEY&scope=video.upload,video.publish&response_type=code&redirect_uri=http://localhost:5000/tiktok/callback

# Step 2: After login, copy the 'code' from URL
# URL will be: http://localhost:5000/tiktok/callback?code=XXXXX

# Step 3: Exchange code for token
curl -X POST 'https://open.tiktokapis.com/v2/oauth/token/' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_key=YOUR_CLIENT_KEY' \
  -d 'client_secret=YOUR_CLIENT_SECRET' \
  -d 'code=XXXXX' \
  -d 'grant_type=authorization_code' \
  -d 'redirect_uri=http://localhost:5000/tiktok/callback'

# Step 4: Copy access_token from response
# Paste in .env file
```

---

## ✅ Solution 4: Test Without TikTok (Recommended for Now)

Agar TikTok OAuth mushkil ho raha hai, to pehle **YouTube analyzer** test karein:

```bash
# System 2 test karo (TikTok ki zaroorat nahi)
python -m yt_analyzer.main --mode search --query "cooking" --limit 5
```

Ye kaam karega aur aapko best videos ka report dega. Phir manually upload kar sakte hain.

---

## ✅ Solution 5: Skip OAuth for Testing

Web app mein temporary bypass:

Edit `web_app.py` and add this route:

```python
@app.route('/tiktok/skip')
def tiktok_skip():
    """Skip TikTok connection for testing"""
    session['tiktok_connected'] = True
    return redirect(url_for('index'))
```

Then visit: `http://localhost:5000/tiktok/skip`

**Note:** Upload won't work without real token, but you can test the UI.

---

## 🎯 Recommended Approach

### For Development/Testing:
1. Use YouTube Analyzer (no TikTok needed)
2. Test video conversion with `--dry-run`
3. Manually upload to TikTok

### For Production:
1. Get TikTok app approved (takes 1-3 days)
2. Use proper OAuth flow
3. Store tokens in database

---

## 📞 Still Having Issues?

### Check These:

1. **TikTok App Status**
   - Is it approved?
   - Are scopes enabled?
   - Is redirect URI correct?

2. **Browser Console**
   - Press F12 in browser
   - Check for JavaScript errors
   - Check Network tab for failed requests

3. **Flask Logs**
   - Check terminal where Flask is running
   - Look for error messages

4. **Environment Variables**
   - Check `.env` file
   - Are TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET set?

---

## 💡 Alternative: Use CLI Instead

Agar web OAuth mushkil hai, to CLI use karein:

```bash
# Direct CLI upload (no OAuth needed if you have token)
python -m yt2tik.main \
  --url "https://youtube.com/watch?v=XXX" \
  --auto-upload
```

---

## 🎉 Summary

**Best approach for now:**

1. ✅ Test YouTube Analyzer (works without TikTok)
2. ✅ Test video conversion with --dry-run
3. ⏳ Wait for TikTok app approval
4. ✅ Then setup OAuth properly

**Don't waste time on OAuth if app isn't approved yet!**

---

Need more help? Let me know the exact error message you're seeing.
