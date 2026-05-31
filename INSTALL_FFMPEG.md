# FFmpeg Installation Guide for Windows

## Why FFmpeg is Needed?
FFmpeg is required to convert YouTube videos to TikTok format (9:16 aspect ratio, proper resolution).

## Installation Steps

### Method 1: Download Pre-built Binary (Recommended)

1. **Download FFmpeg:**
   - Go to: https://www.gyan.dev/ffmpeg/builds/
   - Download: `ffmpeg-release-essentials.zip` (around 70MB)
   - Or direct link: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip

2. **Extract the ZIP file:**
   - Right-click on downloaded ZIP → Extract All
   - Extract to: `C:\ffmpeg`
   - You should have: `C:\ffmpeg\bin\ffmpeg.exe`

3. **Add to System PATH:**
   
   **Option A: Using GUI**
   - Press `Windows + R`
   - Type: `sysdm.cpl` and press Enter
   - Go to "Advanced" tab
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New"
   - Add: `C:\ffmpeg\bin`
   - Click "OK" on all windows
   
   **Option B: Using PowerShell (Run as Administrator)**
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\ffmpeg\bin", "Machine")
   ```

4. **Verify Installation:**
   - Open NEW Command Prompt or PowerShell
   - Type: `ffmpeg -version`
   - You should see FFmpeg version info

5. **Restart Your App:**
   - Close the terminal running integrated_app.py
   - Open NEW terminal (important - to load new PATH)
   - Run: `python integrated_app.py`

---

## Method 2: Using Chocolatey Package Manager

If you have Chocolatey installed:

```bash
choco install ffmpeg
```

---

## Method 3: Using Scoop Package Manager

If you have Scoop installed:

```bash
scoop install ffmpeg
```

---

## Troubleshooting

### "ffmpeg: command not found" after installation

**Solution:**
1. Make sure you added `C:\ffmpeg\bin` to PATH (not `C:\ffmpeg`)
2. Close ALL terminal windows
3. Open a NEW terminal
4. Try `ffmpeg -version` again

### "Access Denied" when adding to PATH

**Solution:**
- Run PowerShell or Command Prompt as Administrator
- Or use the GUI method (sysdm.cpl)

### Still not working?

**Quick Test:**
```bash
C:\ffmpeg\bin\ffmpeg.exe -version
```

If this works, PATH is not set correctly. Repeat step 3.

---

## After Installation

1. **Close your current terminal** running the app
2. **Open a NEW terminal**
3. **Verify FFmpeg:** `ffmpeg -version`
4. **Start the app:** `python integrated_app.py`
5. **Try converting a video again**

---

## Alternative: Use Without FFmpeg

If you can't install FFmpeg, the app will use a fallback method:
- Videos will be copied without proper TikTok formatting
- No aspect ratio conversion (9:16)
- No resolution optimization
- But it will still work for basic conversion

**Recommendation:** Install FFmpeg for best results!
