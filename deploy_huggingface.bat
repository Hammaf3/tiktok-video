@echo off
REM Hugging Face Spaces Deployment Script for Windows

echo ==================================================
echo 🚀 Deploying to Hugging Face Spaces
echo ==================================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo ❌ Not a git repository. Initializing...
    git init
    git add .
    git commit -m "Initial commit"
)

echo 📝 Adding Hugging Face remote...
git remote add huggingface https://huggingface.co/spaces/Hammaf3213/youtube 2>nul || echo Remote already exists

echo.
echo 📦 Adding files for deployment...
git add Dockerfile
git add README.md
git add requirements.txt
git add .dockerignore
git add .env.example
git add integrated_app.py
git add yt2tik/
git add templates/
git add DEPLOYMENT_HUGGINGFACE.md
git add DEPLOY_COMMANDS.md

echo.
echo ✅ Files staged for commit
echo.
git status

echo.
echo ==================================================
echo Ready to deploy!
echo ==================================================
echo.
echo Next steps:
echo 1. Review the staged changes above
echo 2. Run: git commit -m "Deploy to Hugging Face Spaces"
echo 3. Run: git push huggingface master
echo.
echo After deployment:
echo 1. Go to https://huggingface.co/spaces/Hammaf3213/youtube/settings
echo 2. Add environment variables (YOUTUBE_API_KEY, FLASK_SECRET_KEY)
echo 3. Wait 5-10 minutes for build
echo 4. Visit https://huggingface.co/spaces/Hammaf3213/youtube
echo.
pause
