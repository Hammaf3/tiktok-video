# 🎯 Age-Restricted Video Fix - Step by Step

## ✅ Code Update Complete!

Code GitHub par push ho gaya hai. Ab Railway automatically redeploy karega.

---

## 📋 Ab Ye Steps Follow Karo (15 Minutes)

### Step 1: Browser Extension Install Karo (2 minutes)

**Chrome/Edge Users:**
1. Is link ko **new tab** mein open karo:
   ```
   https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   ```
2. **"Add to Chrome"** button click karo
3. Extension install ho jayega (browser restart ki zaroorat nahi)

**Firefox Users:**
1. Is link ko open karo:
   ```
   https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/
   ```
2. **"Add to Firefox"** click karo

---

### Step 2: YouTube Se Cookies Export Karo (3 minutes)

1. **YouTube.com par jao:**
   ```
   https://youtube.com
   ```

2. **Login Check Karo:**
   - Agar logged in nahi ho, to login karo
   - Wo account use karo jo age-restricted videos dekh sakta hai
   - Age verification complete hona chahiye

3. **Extension Use Karo:**
   - Browser ke **top-right corner** mein extension icon dikhega
   - Extension icon par **click** karo
   - **"Export"** button click karo
   - File download hogi: `youtube.com_cookies.txt`

4. **File Location:**
   - Usually `C:\Users\Faraz\Downloads\youtube.com_cookies.txt` mein hogi

---

### Step 3: Cookies Ko Base64 Encode Karo (5 minutes)

**Windows PowerShell mein ye commands run karo:**

```powershell
# 1. Downloads folder mein jao
cd "C:\Users\Faraz\Downloads"

# 2. Check karo file hai ya nahi
dir youtube.com_cookies.txt

# 3. File ko rename karo
Rename-Item "youtube.com_cookies.txt" "youtube_cookies.txt"

# 4. Base64 encode karo
$content = Get-Content youtube_cookies.txt -Raw
$bytes = [System.Text.Encoding]::UTF8.GetBytes($content)
$encoded = [Convert]::ToBase64String($bytes)

# 5. Encoded string ko file mein save karo
$encoded | Out-File "youtube_cookies_base64.txt"

# 6. Screen par print karo (copy karne ke liye)
Write-Host "=" * 80
Write-Host "COPY THIS ENCODED STRING:"
Write-Host "=" * 80
Write-Host $encoded
Write-Host "=" * 80
Write-Host ""
Write-Host "Also saved to: youtube_cookies_base64.txt"
```

**Important:** Puri encoded string copy karo (bahut lambi hogi, 5000+ characters)

---

### Step 4: Railway Dashboard Mein Add Karo (3 minutes)

1. **Railway Dashboard Open Karo:**
   ```
   https://railway.app/dashboard
   ```

2. **Apna Project Select Karo:**
   - `tiktok-video-production` project par click karo

3. **Variables Tab Par Jao:**
   - Left sidebar mein **"Variables"** tab click karo

4. **New Variable Add Karo:**
   - **"New Variable"** button click karo
   - **Variable Name:** `YOUTUBE_COOKIES_BASE64`
   - **Value:** (Step 3 mein jo encoded string copy ki, wo paste karo)
   - **"Add"** button click karo

5. **Verify:**
   - Variable list mein `YOUTUBE_COOKIES_BASE64` dikhna chahiye
   - Value hidden rahegi (security ke liye)

---

### Step 5: Railway Redeploy Wait Karo (2-3 minutes)

1. **Automatic Redeploy:**
   - Railway automatically redeploy start kar dega
   - Environment variable add hone par automatic trigger hota hai

2. **Check Deployment Status:**
   - **"Deployments"** tab par jao
   - Latest deployment **"Building"** → **"Deploying"** → **"Success"** dikhega
   - Wait karo jab tak **"Success"** na ho jaye

3. **Check Logs (Optional):**
   - Deployment par click karo
   - **"View Logs"** click karo
   - Ye message dikhna chahiye:
     ```
     ✅ YouTube cookies loaded from environment variable
     ```

---

### Step 6: Test Karo! (2 minutes)

1. **Railway App Open Karo:**
   ```
   https://tiktok-video-production.up.railway.app
   ```

2. **Age-Restricted Video Try Karo:**
   - Koi bhi age-restricted YouTube video ka URL daalo
   - Convert button click karo

3. **Success!**
   - Error nahi aana chahiye
   - Video download hona chahiye
   - "Using YouTube cookies for authentication" message logs mein dikhega

---

## 🎉 Done!

Agar sab steps sahi se follow kiye to age-restricted videos ab kaam karni chahiye!

---

## 🐛 Agar Abhi Bhi Error Aa Raha Hai?

### Check 1: Variable Name Sahi Hai?

Railway Variables mein check karo:
- Name **exactly** ye hona chahiye: `YOUTUBE_COOKIES_BASE64`
- Spelling mistake nahi honi chahiye
- Capital letters sahi hone chahiye

### Check 2: Puri String Copy Ki?

- Encoded string bahut lambi hoti hai (5000+ characters)
- Make sure puri string copy ki hai
- Koi space ya newline extra nahi hona chahiye

### Check 3: Deployment Success Hui?

Railway Deployments tab mein check karo:
- Latest deployment **"Success"** show kar raha hai?
- Koi error to nahi?

### Check 4: Cookies Fresh Hain?

- YouTube se logout karo
- Phir login karo
- Naye cookies export karo
- Steps 2-5 repeat karo

### Check 5: Correct YouTube Account?

- Wo account use karo jo age-restricted videos dekh sakta hai
- Age verification complete hona chahiye
- Adult account hona chahiye (18+)

---

## 📞 Railway Logs Kaise Dekhe?

**Option 1: Dashboard**
1. Railway dashboard → Deployments
2. Latest deployment par click karo
3. "View Logs" click karo

**Option 2: CLI (Advanced)**
```bash
# Railway CLI install karo
npm i -g @railway/cli

# Login karo
railway login

# Logs dekho
railway logs
```

---

## 🔒 Security

- `YOUTUBE_COOKIES_BASE64` secure hai
- Railway dashboard mein value hidden rehti hai
- Cookies expire hote hain (2-3 mahine mein refresh karo)
- Kisi ke saath share mat karo

---

## ✅ Success Checklist

- [ ] Browser extension install kiya
- [ ] YouTube par login kiya (correct account)
- [ ] Cookies export kiye
- [ ] Base64 encode kiya
- [ ] Railway variable add kiya (`YOUTUBE_COOKIES_BASE64`)
- [ ] Deployment success hui
- [ ] Age-restricted video test kiya
- [ ] Error nahi aaya!

---

## 📚 Additional Help

- **Detailed Guide:** `RAILWAY_COOKIES_SETUP.md`
- **General Cookies Setup:** `COOKIES_SETUP.md`
- **Deployment Guide:** `DEPLOYMENT_GUIDE.md`

---

**Need Help?** Check Railway logs ya mujhe batao!
