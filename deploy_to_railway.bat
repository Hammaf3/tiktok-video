@echo off
REM Deployment Script for Railway (Windows)

echo ==========================================
echo 🚀 Railway Deployment Script
echo ==========================================
echo.

REM Check if we're in the right directory
if not exist "integrated_app.py" (
    echo ❌ Error: integrated_app.py not found
    echo Please run this script from the project root directory
    exit /b 1
)

echo 📋 Step 1: Checking files...
echo.

REM Check if enhanced downloader exists
if exist "yt2tik\downloader_enhanced.py" (
    echo ✅ Enhanced downloader found
) else (
    echo ❌ Enhanced downloader not found
    exit /b 1
)

REM Check if production Dockerfile exists
if exist "Dockerfile.production_final" (
    echo ✅ Production Dockerfile found
) else (
    echo ❌ Production Dockerfile not found
    exit /b 1
)

echo.
echo 📋 Step 2: Preparing files...
echo.

REM Copy production Dockerfile to Dockerfile
copy /Y Dockerfile.production_final Dockerfile
echo ✅ Copied Dockerfile.production_final → Dockerfile

REM Copy production requirements
if exist "requirements.production.txt" (
    copy /Y requirements.production.txt requirements.txt
    echo ✅ Copied requirements.production.txt → requirements.txt
)

echo.
echo 📋 Step 3: Git status check...
echo.

git status --short

echo.
echo 📋 Step 4: Adding files to git...
echo.

git add integrated_app.py
git add yt2tik\downloader_enhanced.py
git add yt2tik\config.py
git add Dockerfile
git add requirements.txt
git add IMPLEMENTATION_COMPLETE.md

echo ✅ Files staged for commit

echo.
echo 📋 Step 5: Creating commit...
echo.

git commit -m "Production deployment: Enhanced error handling and Railway optimizations - Add comprehensive error detection (HTTP 429, login required, private videos, etc.) - Implement retry logic with exponential backoff - Add user-friendly error messages - Optimize Dockerfile for Railway - Use /tmp directory for Railway ephemeral storage - Enhanced health checks with component status - Update dependencies for production stability"

echo ✅ Commit created

echo.
echo 📋 Step 6: Pushing to GitHub...
echo.

git push origin master

if %errorlevel% equ 0 (
    echo ✅ Successfully pushed to GitHub
) else (
    echo ❌ Failed to push to GitHub
    exit /b 1
)

echo.
echo ==========================================
echo ✅ Deployment Complete!
echo ==========================================
echo.
echo Railway will now automatically deploy your application.
echo.
echo 📊 Next Steps:
echo 1. Wait 5-10 minutes for Railway to build and deploy
echo 2. Check Railway dashboard for deployment status
echo 3. Test health endpoint: https://your-app.up.railway.app/health
echo 4. Monitor logs for any errors
echo.
echo Expected health response:
echo {
echo   "status": "healthy",
echo   "components": {
echo     "enhanced_downloader": true,
echo     "ffmpeg": true,
echo     "yt_dlp": true
echo   }
echo }
echo.
echo ==========================================

pause
