@echo off
REM Windows Testing Script - Test production fixes before deploying

echo 🧪 Testing Production YouTube to TikTok Converter
echo ==================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found
    exit /b 1
)
echo ✅ Python found

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  FFmpeg not found - video conversion may fail
    echo    Download from: https://ffmpeg.org/download.html
) else (
    echo ✅ FFmpeg found
)

REM Install dependencies
echo.
echo 📦 Installing dependencies...
pip install -q -r requirements.txt

REM Check production files
echo.
echo 📁 Checking production files...

if not exist "app_production.py" (
    echo ❌ app_production.py not found
    exit /b 1
)
echo ✅ app_production.py found

if not exist "yt2tik\downloader_production.py" (
    echo ❌ yt2tik\downloader_production.py not found
    exit /b 1
)
echo ✅ downloader_production.py found

if not exist "job_store.py" (
    echo ❌ job_store.py not found
    exit /b 1
)
echo ✅ job_store.py found

REM Create .env if not exists
if not exist ".env" (
    echo.
    echo 📝 Creating .env file from template...
    copy .env.production .env
    echo ✅ .env created - configure it before deploying
)

REM Create directories
echo.
echo 📂 Creating directories...
if not exist "tmp\yt2tik\downloads" mkdir tmp\yt2tik\downloads
if not exist "tmp\yt2tik\output" mkdir tmp\yt2tik\output
if not exist "logs" mkdir logs
echo ✅ Directories created

REM Run tests
echo.
echo 🧪 Running production app...
echo.
echo ==================================================
echo Server will start on http://localhost:7860
echo Press Ctrl+C to stop
echo ==================================================
echo.

REM Set environment for testing
set FLASK_DEBUG=False
set ENABLE_YOUTUBE_COOKIES=false
set PORT=7860

REM Start app
python app_production.py
