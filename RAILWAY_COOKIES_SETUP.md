# 🚂 Railway Deployment - YouTube Cookies Setup

## Problem
Age-restricted videos Railway par download nahi ho rahi kyunki cookies missing hain.

## Solution (10 Minutes)

### Step 1: Browser Extension Install Karo

**Chrome/Edge Users:**
1. Is link par jao: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
2. "Add to Chrome" click karo
3. Extension install ho jayega

**Firefox Users:**
1. Is link par jao: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
2. "Add to Firefox" click karo

### Step 2: YouTube Cookies Export Karo

1. **YouTube.com par jao**: https://youtube.com
2. **Login karo** (agar already logged in nahi ho)
   - Wo account use karo jo age-restricted videos dekh sakta hai
3. **Extension icon click karo** (browser toolbar mein, top-right corner)
4. **"Export" button click karo**
5. File download hogi: `youtube.com_cookies.txt`

### Step 3: Cookies Ko Base64 Encode Karo

**Windows PowerShell mein ye commands run karo:**

```powershell
# 1. Downloaded file ka path set karo (apna path adjust karo)
cd "C:\Users\Faraz\Downloads"

# 2. File ko rename karo
Rename-Item "youtube.com_cookies.txt" "youtube_cookies.txt"

# 3. Base64 encode karo
$content = Get-Content youtube_cookies.txt -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$encoded = [Convert]::ToBase64String($bytes)

# 4. Encoded string ko file mein save karo (copy karna easy ho jayega)
$encoded | Out-File "youtube_cookies_base64.txt"

# 5. Screen par bhi print karo
Write-Host "Encoded cookies saved to: youtube_cookies_base64.txt"
Write-Host ""
Write-Host "Copy this encoded string:"
Write-Host $encoded
```

**Ya agar Linux/Mac use kar rahe ho:**

```bash
# Downloads folder mein jao
cd ~/Downloads

# File rename karo
mv youtube.com_cookies.txt youtube_cookies.txt

# Base64 encode karo
base64 youtube_cookies.txt > youtube_cookies_base64.txt

# Print karo
cat youtube_cookies_base64.txt
```

### Step 4: Railway Dashboard Mein Add Karo

1. **Railway Dashboard Open Karo:**
   - https://railway.app/dashboard
   - Apna project select karo: `tiktok-video-production`

2. **Variables Tab Par Jao:**
   - Left sidebar mein "Variables" click karo

3. **New Variable Add Karo:**
   - Click "New Variable"
   - **Variable Name:** `YOUTUBE_COOKIES_BASE64`
   - **Value:** (encoded string paste karo jo Step 3 mein mila)
   - "Add" button click karo

4. **Save Karo:**
   - Variables automatically save ho jayenge

### Step 5: Redeploy Karo

**Option A: Automatic (Recommended)**
- Railway automatically redeploy kar dega jab variable add hoga
- Wait karo 2-3 minutes

**Option B: Manual**
- Deployments tab par jao
- "Deploy" button click karo

### Step 6: Test Karo

1. **Apni Railway app open karo:**
   - https://tiktok-video-production.up.railway.app

2. **Age-restricted video try karo**

3. **Success!** Ab download hona chahiye

---

## 🐛 Troubleshooting

### Error: Still getting "Age-restricted video"

**Check 1: Variable Name Sahi Hai?**
```
Railway Variables mein check karo:
Name exactly ye hona chahiye: YOUTUBE_COOKIES_BASE64
```

**Check 2: Cookies Fresh Hain?**
- Browser se logout karo
- Phir login karo
- Naye cookies export karo
- Steps repeat karo

**Check 3: Deployment Complete Hua?**
- Railway dashboard → Deployments
- Latest deployment "Success" show kar raha hai?
- Logs mein koi error to nahi?

**Check 4: Correct Account?**
- YouTube account jo age-restricted videos dekh sakta hai
- Age verification complete hona chahiye

### Error: "Invalid base64 string"

**Solution:**
- Encoding step phir se karo
- Make sure puri string copy ki hai (koi space ya newline extra nahi)

### Logs Kaise Dekhe?

```bash
# Railway CLI install karo (optional)
npm i -g @railway/cli

# Login karo
railway login

# Project link karo
railway link

# Logs dekho
railway logs
```

**Ya Railway Dashboard Mein:**
- Deployments tab → Latest deployment → View Logs

---

## ✅ Verification

Agar sab kuch sahi hai to Railway logs mein ye message dikhna chahiye:

```
Using YouTube cookies for authentication
✅ Download complete
```

---

## 🔒 Security Note

- `YOUTUBE_COOKIES_BASE64` environment variable secure hai
- Railway dashboard mein value hidden rehti hai
- Cookies expire hote hain (2-3 mahine mein refresh karo)

---

## 📝 Quick Reference

| Step | Action | Time |
|------|--------|------|
| 1 | Install browser extension | 1 min |
| 2 | Export cookies from YouTube | 2 min |
| 3 | Base64 encode cookies | 2 min |
| 4 | Add to Railway variables | 2 min |
| 5 | Wait for redeploy | 2-3 min |
| 6 | Test | 1 min |

**Total Time: ~10 minutes**

---

Need help? Check Railway logs or ask for assistance!
