# YouTube OAuth Troubleshooting Guide

## Abhi Kya Karna Hai

### Option A: Manual Restart (Recommended)

1. **Purana app band karein:**
   - Jis terminal/command prompt mein app chal raha hai, wahan jao
   - `Ctrl + C` press karein
   - Ya phir Task Manager se process kill karein (PID: 12268)

2. **Naya app start karein:**
   ```bash
   cd "C:\Users\Faraz\Desktop\tiktok video uploader"
   python integrated_app.py
   ```

3. **Browser refresh karein:**
   - http://localhost:5000 ko refresh karein

### Option B: Batch File Use karein

1. Double-click karein: `restart_app.bat`
2. Ye automatically purana app band karega aur naya start karega

---

## Testing Steps

### Test 1: Session Status Check

Browser mein ye URL kholo:
```
http://localhost:5000/debug/session
```

Ye dikhayega:
- YouTube connected hai ya nahi
- Credentials session mein hain ya nahi
- Token available hai ya nahi

### Test 2: YouTube Tab Test

1. http://localhost:5000 par jao
2. "📺 My YouTube Videos" tab par click karo
3. Terminal/console mein logs dekho

**Expected Logs:**
```
=== YouTube Channels Request ===
Session youtube_connected: True
Credentials found: token=...
Building YouTube client...
Fetching channels...
Channel: [Your Channel Name] - [X] videos
SUCCESS: Returning [N] channels
```

**Agar Error Aaye:**
```
ERROR: YouTube not connected in session
```
Ya
```
ERROR: No credentials in session
```

---

## Common Problems & Solutions

### Problem 1: Session Lost (Most Common)
**Symptoms:** 
- "Connect YouTube Account" button dikhe
- Session status shows: `youtube_connected: false`

**Solution:**
1. http://localhost:5000/youtube/connect par jao
2. Google account se phir se login karo
3. Permissions allow karo
4. Redirect hone ke baad "My YouTube Videos" tab check karo

### Problem 2: Token Expired
**Symptoms:**
- Error: "Invalid credentials"
- Error: "Token has been expired or revoked"

**Solution:**
- Same as Problem 1 - reconnect karo

### Problem 3: Wrong Scopes
**Symptoms:**
- Error: "Insufficient permissions"
- Channels fetch nahi ho rahe

**Solution:**
- Google Cloud Console mein jao
- OAuth consent screen check karo
- Scopes verify karo:
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/youtube.force-ssl`

### Problem 4: API Quota Exceeded
**Symptoms:**
- Error: "quotaExceeded"

**Solution:**
- 24 hours wait karo
- Ya Google Cloud Console mein quota increase request karo

---

## Next Steps

1. **Restart app** (Option A ya B)
2. **Check session status**: http://localhost:5000/debug/session
3. **Test YouTube tab**
4. **Share logs** - Terminal mein jo output aaye wo copy karke share karo

---

## Quick Commands

### Kill process on port 5000:
```bash
netstat -ano | findstr :5000
taskkill /F /PID [PID_NUMBER]
```

### Start app:
```bash
python integrated_app.py
```

### Check if app is running:
```bash
curl http://localhost:5000/debug/session
```
