# YouTube OAuth Debug Steps

## Problem
YouTube account link ho gaya hai lekin channel ki profile picture aur videos nahi dikh rahi hain.

## Solution Steps

### Step 1: Stop Current App
Agar integrated_app.py chal raha hai to usko band kar dein (Ctrl+C)

### Step 2: Start App with Logging
```bash
cd "C:\Users\Faraz\Desktop\tiktok video uploader"
python integrated_app.py
```

### Step 3: Test the Flow
1. Browser mein jao: http://localhost:5000
2. "My YouTube Videos" tab par click karein
3. Agar "Connect YouTube Account" button dikhe to:
   - Click karein aur phir se connect karein
   - Google se permission dein
   - Redirect hone ke baad "My YouTube Videos" tab par wapas jao

4. Console/terminal mein logs dekhein - yeh dikhega:
   ```
   === YouTube Channels Request ===
   Session youtube_connected: True/False
   Credentials found: token=...
   Building YouTube client...
   Fetching channels...
   ```

### Step 4: Check for Errors
Console mein koi bhi error message dhundein:
- "ERROR: YouTube not connected in session"
- "ERROR: No credentials in session"
- "ERROR: Channel not found"
- Ya koi API error

### Common Issues & Fixes

#### Issue 1: Session Expired
**Symptom:** "YouTube account not connected" error
**Fix:** 
- Browser cookies clear ho gaye honge
- Phir se connect karein: http://localhost:5000/youtube/connect

#### Issue 2: Token Expired
**Symptom:** "Invalid credentials" ya "Token expired" error
**Fix:**
- Phir se connect karein
- Ya refresh token use karein (automatic hona chahiye)

#### Issue 3: Wrong Scopes
**Symptom:** "Insufficient permissions" error
**Fix:**
- YouTube OAuth scopes check karein
- Phir se authorize karein with proper scopes

#### Issue 4: API Quota Exceeded
**Symptom:** "quotaExceeded" error
**Fix:**
- 24 hours wait karein
- Ya naya API key banao

### Step 5: Share Logs
Console mein jo bhi output aaye, wo copy karke mujhe bhejein.

## Quick Test Commands

### Test 1: Check if app is running
```bash
curl http://localhost:5000
```

### Test 2: Check YouTube connection status
Browser console mein:
```javascript
fetch('/youtube/channels')
  .then(r => r.json())
  .then(d => console.log(d))
```

### Test 3: Clear session and reconnect
Browser mein:
1. Developer Tools kholo (F12)
2. Application tab → Cookies → localhost:5000
3. Sab cookies delete karo
4. Page refresh karo
5. Phir se YouTube connect karo
