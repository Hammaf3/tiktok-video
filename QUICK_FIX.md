# 🚨 Age-Restricted Video Error - Quick Fix

## Problem
```
❌ Error: Age-restricted video. Please try a different video.
```

## Why This Happens
- **Localhost par kaam karta tha** → Browser cookies automatically use ho rahe the
- **Domain/Production par fail** → Cookies available nahi hain
- YouTube age-restricted videos ke liye login chahiye

---

## ✅ Quick Solution (5 Minutes)

### Step 1: Install Browser Extension

**Chrome/Edge:**
- Extension: "Get cookies.txt LOCALLY"
- Link: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc

**Firefox:**
- Extension: "cookies.txt"
- Link: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

### Step 2: Export Cookies

1. **YouTube par jao** → https://youtube.com
2. **Login karo** (agar already logged in nahi ho)
3. **Extension icon click karo** (browser toolbar mein)
4. **"Export" button click karo**
5. File download hogi: `youtube.com_cookies.txt`

### Step 3: Setup in Project

1. **Downloaded file ko rename karo:**
   ```
   youtube.com_cookies.txt  →  youtube_cookies.txt
   ```

2. **Project root mein paste karo:**
   ```
   tiktok video uploader/
   ├── youtube_cookies.txt  ← Yahan paste karo
   ├── yt2tik/
   ├── web_app.py
   └── ...
   ```

3. **Done!** Ab age-restricted videos download ho jayengi

---

## 🧪 Test Karo

### Local Test:
```bash
python -m yt2tik.main --url "AGE_RESTRICTED_VIDEO_URL" --dry-run
```

**Success message:**
```
Using YouTube cookies for authentication
✅ Download complete
```

---

## 🚀 Production/Domain Setup

### Railway.app / Render.com:

**Option 1: Git mein add karo (Private repo only!)**
```bash
git add youtube_cookies.txt
git commit -m "Add YouTube cookies"
git push
```

**Option 2: Environment Variable (More Secure)**

1. **Cookies ko Base64 encode karo:**
   ```powershell
   # Windows PowerShell
   $content = Get-Content youtube_cookies.txt -Raw
   $bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
   $encoded = [Convert]::ToBase64String($bytes)
   echo $encoded
   ```

2. **Railway/Render dashboard mein:**
   - Environment Variables → Add Variable
   - Name: `YOUTUBE_COOKIES_BASE64`
   - Value: (encoded string paste karo)

3. **Redeploy karo**

---

## 🔒 Security Notes

1. **Cookies sensitive hain** - Apne YouTube account ka access dete hain
2. **Public repository mein mat daalo** - Private repo use karo
3. **Production mein environment variable use karo** - Zyada secure
4. **Cookies expire hote hain** - Har 2-3 mahine mein refresh karo

---

## 🐛 Still Not Working?

### Check 1: File Location
```bash
# Ye command run karo
ls youtube_cookies.txt

# Output hona chahiye:
# youtube_cookies.txt
```

### Check 2: File Format
```bash
# File open karke dekho
# First line honi chahiye:
# Netscape HTTP Cookie File
```

### Check 3: Fresh Cookies
- Purani cookies (2-3 mahine se zyada) kaam nahi karti
- Browser se logout → login → naye cookies export karo

### Check 4: Correct Account
- YouTube account se login karo jo age-restricted videos dekh sakta hai
- Age verification complete hona chahiye

---

## 📚 Detailed Guides

- **Full Cookie Setup:** `COOKIES_SETUP.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`
- **Main README:** `README.md`

---

## ✅ Checklist

- [ ] Browser extension install kiya
- [ ] YouTube par login kiya
- [ ] Cookies export kiye
- [ ] File rename kari: `youtube_cookies.txt`
- [ ] Project root mein paste kari
- [ ] Local test kiya
- [ ] Production par deploy kiya (agar zaroorat hai)

---

**🎉 Ab age-restricted videos download ho jayengi!**
