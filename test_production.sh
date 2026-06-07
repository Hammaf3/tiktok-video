#!/bin/bash
# Local Testing Script - Test production fixes before deploying

echo "🧪 Testing Production YouTube to TikTok Converter"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✅ Python 3 found"

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg not found - video conversion may fail"
    echo "   Install: sudo apt install ffmpeg (Linux) or brew install ffmpeg (Mac)"
else
    echo "✅ FFmpeg found"
fi

# Check requirements
echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check if production files exist
echo ""
echo "📁 Checking production files..."

if [ ! -f "app_production.py" ]; then
    echo "❌ app_production.py not found"
    exit 1
fi
echo "✅ app_production.py found"

if [ ! -f "yt2tik/downloader_production.py" ]; then
    echo "❌ yt2tik/downloader_production.py not found"
    exit 1
fi
echo "✅ downloader_production.py found"

if [ ! -f "job_store.py" ]; then
    echo "❌ job_store.py not found"
    exit 1
fi
echo "✅ job_store.py found"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating .env file from template..."
    cp .env.production .env
    echo "✅ .env created - configure it before deploying"
fi

# Create directories
echo ""
echo "📂 Creating directories..."
mkdir -p tmp/yt2tik/downloads tmp/yt2tik/output logs
echo "✅ Directories created"

# Run tests
echo ""
echo "🧪 Running production app..."
echo ""
echo "=================================================="
echo "Server will start on http://localhost:7860"
echo "Press Ctrl+C to stop"
echo "=================================================="
echo ""

# Set environment for testing
export FLASK_DEBUG=False
export ENABLE_YOUTUBE_COOKIES=false
export PORT=7860

# Start app
python3 app_production.py
