#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     RAILWAY DEPLOYMENT FIX - QUICK DEPLOY SCRIPT                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "This script will:"
echo "  1. Create a minimal working Railway deployment"
echo "  2. Test if Railway works at all"
echo "  3. Help diagnose the issue"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

cd "$(dirname "$0")"

echo ""
echo "Step 1: Creating minimal Procfile for testing..."
cat > Procfile.minimal << 'EOF'
web: gunicorn test_app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
EOF

echo "✅ Created Procfile.minimal"

echo ""
echo "Step 2: Backing up current Procfile..."
cp Procfile Procfile.backup

echo "✅ Backed up to Procfile.backup"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CHOOSE AN OPTION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Option 1: Test with minimal app (recommended)"
echo "  - Deploys simple test_app.py to verify Railway works"
echo "  - If this works, issue is with integrated_app.py"
echo "  - Type: 1"
echo ""
echo "Option 2: Deploy full app with all fixes"
echo "  - Deploys integrated_app.py with defensive imports"
echo "  - Type: 2"
echo ""
echo "Option 3: Show diagnostic information only"
echo "  - Shows current configuration"
echo "  - Type: 3"
echo ""
read -p "Enter option (1/2/3): " OPTION

case $OPTION in
  1)
    echo ""
    echo "Deploying minimal test app..."
    cp Procfile.minimal Procfile
    git add Procfile test_app.py
    git commit -m "Test: Deploy minimal app to diagnose Railway issue"
    git push origin master
    echo ""
    echo "✅ Pushed minimal test app"
    echo ""
    echo "Wait 2-3 minutes, then test:"
    echo "  curl https://tiktok-video-production.up.railway.app/"
    echo ""
    echo "If you see JSON with 'status: alive', Railway works!"
    echo "Then restore full app with: cp Procfile.backup Procfile"
    ;;

  2)
    echo ""
    echo "Deploying full app with fixes..."
    # Procfile already correct
    git add integrated_app.py
    git commit -m "Deploy full app with defensive imports" || echo "No changes to commit"
    git push origin master
    echo ""
    echo "✅ Pushed full app"
    echo ""
    echo "Wait 3-5 minutes, then test:"
    echo "  curl https://tiktok-video-production.up.railway.app/health"
    ;;

  3)
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  DIAGNOSTIC INFORMATION                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Current Procfile:"
    echo "────────────────────────────────────────────────────────────────────"
    cat Procfile
    echo ""
    echo ""
    echo "Requirements.txt (gunicorn):"
    echo "────────────────────────────────────────────────────────────────────"
    grep gunicorn requirements.txt || echo "❌ gunicorn NOT FOUND in requirements.txt"
    echo ""
    echo ""
    echo "Git Status:"
    echo "────────────────────────────────────────────────────────────────────"
    git status --short
    echo ""
    echo ""
    echo "Recent Commits:"
    echo "────────────────────────────────────────────────────────────────────"
    git log --oneline -n 5
    echo ""
    ;;

  *)
    echo "Invalid option"
    exit 1
    ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Go to Railway dashboard: https://railway.app/dashboard"
echo "2. Check deployment status"
echo "3. View logs (Build Logs + Deploy Logs)"
echo "4. Copy any error messages"
echo ""
echo "Common error patterns to look for:"
echo "  • 'ModuleNotFoundError' - missing Python package"
echo "  • 'ffmpeg: not found' - FFmpeg not installed"
echo "  • 'ImportError' - code import issue"
echo "  • 'Address already in use' - port binding issue"
echo ""
