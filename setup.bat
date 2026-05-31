@echo off
REM Quick Start Script for yt2tik (Windows)

echo 🎬 yt2tik - YouTube to TikTok Automation Suite
echo ==============================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg not found. Please install FFmpeg first.
    echo    Download from: https://ffmpeg.org/download.html
    echo    Add to PATH after installation
    exit /b 1
) else (
    echo ✓ FFmpeg installed
)

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.example .env
    echo ✓ Created .env file. Please add your API credentials.
)

REM Install dependencies
echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo ✅ Setup complete!
echo.
echo 📖 Quick Usage:
echo.
echo System 1 - Convert YouTube to TikTok:
echo   python -m yt2tik.main --url "https://youtube.com/watch?v=XXX" --auto-upload
echo.
echo System 2 - Analyze YouTube content:
echo   python -m yt_analyzer.main --mode search --query "viral videos" --limit 25
echo.
echo For more examples, see README.md

pause
