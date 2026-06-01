# 🍪 YouTube Cookies Setup Guide

Age-restricted videos ko download karne ke liye aapko YouTube cookies ki zaroorat hai. Ye guide aapko step-by-step batayega.

## ⚠️ Kya Problem Hai?

YouTube age-restricted videos ko download karne ke liye authentication chahiye. Localhost par kabhi kabhi kaam ho jata hai browser cookies ki wajah se, lekin production/domain par fail ho jata hai.

## ✅ Solution: Browser Cookies Export Karo

### Method 1: Browser Extension (Recommended - Sabse Aasan)

#### Chrome/Edge Users:

1. **Extension Install Karo:**
   - Chrome Web Store se "Get cookies.txt LOCALLY" extension install karo
   - Link: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

2. **YouTube Par Login Karo:**
   - YouTube.com par jao
   - Apne account se login karo (jis account se age-restricted videos dekh sakte ho)

3. **Cookies Export Karo:**
   - YouTube.com par hi raho
   - Extension icon par click karo (browser toolbar mein)
   - "Export" button par click karo
   - File save ho jayegi `youtube.com_cookies.txt` naam se

4. **File Ko Project Mein Copy Karo:**
   - Downloaded file ko rename karo: `youtube_cookies.txt`
   - Is file ko apne project ke root folder mein paste karo
   - Path hona chahiye: `tiktok video uploader/youtube_cookies.txt`

#### Firefox Users:

1. **Extension Install Karo:**
   - Firefox Add-ons se "cookies.txt" extension install karo
   - Link: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. **Baaki steps same hain** (YouTube login → Export → Rename → Copy)

### Method 2: Manual Export (Advanced)

Agar extension use nahi karna chahte:

1. **Browser DevTools Kholo:**
   - YouTube.com par jao (logged in)
   - Press `F12` ya Right-click → "Inspect"
   - "Application" tab par jao (Chrome) ya "Storage" tab (Firefox)

2. **Cookies Copy Karo:**
   - Left sidebar mein "Cookies" → "https://www.youtube.com" select karo
   - Saari cookies copy karo

3. **Netscape Format Mein Convert Karo:**
   - Ye thoda technical hai, isliye extension use karna better hai

---

## 🚀 Deployment Par Cookies Kaise Use Karein?

### Railway.app / Render.com / Fly.io:

**Option 1: Environment Variable (Recommended for Production)**

1. **Cookies ko Base64 Encode Karo:**
   ```bash
   # Windows PowerShell
   $content = Get-Content youtube_cookies.txt -Raw
   $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
   $encoded = [Convert]::ToBase64String($bytes)
   echo $encoded
   
   # Linux/Mac
   base64 youtube_cookies.txt
   ```

2. **Environment Variable Set Karo:**
   - Railway/Render dashboard mein jao
   - Environment Variables section mein:
     - Name: `YOUTUBE_COOKIES_BASE64`
     - Value: (jo base64 string copy ki hai wo paste karo)

3. **Code Update (Already Done):**
   - Code automatically cookies use karega agar file exist karti hai

**Option 2: Direct File Upload (Simple but Less Secure)**

1. **Git Repository Mein Add Karo:**
   ```bash
   # .gitignore mein se youtube_cookies.txt ko remove karo (agar hai to)
   git add youtube_cookies.txt
   git commit -m "Add YouTube cookies for age-restricted videos"
   git push
   ```

2. **⚠️ Warning:** Cookies sensitive hain, public repository mein mat daalo!

---

## 🔒 Security Tips

1. **Private Repository Use Karo:**
   - Agar cookies git mein add kar rahe ho, repository private honi chahiye

2. **Cookies Expire Hote Hain:**
   - Har 2-3 mahine mein cookies refresh karo
   - Agar download fail ho to naye cookies export karo

3. **Production Mein Environment Variable Use Karo:**
   - Cookies ko environment variable mein store karna zyada secure hai

---

## 🧪 Test Karo

### Local Testing:

```bash
# Test age-restricted video
python -m yt2tik.main --url "https://www.youtube.com/watch?v=AGE_RESTRICTED_VIDEO_ID" --dry-run
```

Agar cookies sahi se setup hain to ye message aayega:
```
Using YouTube cookies for authentication
```

### Production Testing:

1. Cookies setup karne ke baad app redeploy karo
2. Age-restricted video try karo
3. Error nahi aana chahiye

---

## 🐛 Troubleshooting

### Error: "Age-restricted video" abhi bhi aa raha hai

**Solution:**
1. Check karo `youtube_cookies.txt` file project root mein hai
2. File ka naam exactly `youtube_cookies.txt` hona chahiye
3. Cookies fresh hain? (2-3 mahine se purani to nahi?)
4. YouTube account se logout karke phir login karo, naye cookies export karo

### Error: "Cookies file not found"

**Solution:**
```bash
# Check file location
ls youtube_cookies.txt

# File path sahi hai?
# Hona chahiye: tiktok video uploader/youtube_cookies.txt
```

### Cookies Kaam Nahi Kar Rahe

**Solution:**
1. Browser se logout karo
2. Phir login karo
3. Naye cookies export karo
4. Purani `youtube_cookies.txt` delete karke nayi paste karo

---

## 📝 File Format Example

`youtube_cookies.txt` file ka format Netscape format hona chahiye:

```
# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	abcdef123456
.youtube.com	TRUE	/	TRUE	1234567890	LOGIN_INFO	xyz789
```

---

## ✅ Final Checklist

- [ ] Browser extension install kiya
- [ ] YouTube par login kiya
- [ ] Cookies export kiye
- [ ] File rename kari: `youtube_cookies.txt`
- [ ] File project root mein copy ki
- [ ] Local test kiya
- [ ] Production par deploy kiya
- [ ] Age-restricted video test kiya

---

## 🎯 Quick Commands

```bash
# Check if cookies file exists
ls youtube_cookies.txt

# Test with age-restricted video
python -m yt2tik.main --url "YOUR_VIDEO_URL" --dry-run

# Deploy to Railway (if using Railway)
railway up

# Check logs
railway logs
```

---

**Need Help?** Check the logs in `logs/` directory for detailed error messages.
