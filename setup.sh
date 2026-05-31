#!/bin/bash
# Quick Start Script for yt2tik

echo "🎬 yt2tik - YouTube to TikTok Automation Suite"
echo "=============================================="
echo ""

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Check if FFmpeg is installed
if command -v ffmpeg &> /dev/null; then
    ffmpeg_version=$(ffmpeg -version 2>&1 | head -n 1 | awk '{print $3}')
    echo "✓ FFmpeg installed: $ffmpeg_version"
else
    echo "❌ FFmpeg not found. Please install FFmpeg first."
    echo "   Windows: Download from https://ffmpeg.org/download.html"
    echo "   Mac: brew install ffmpeg"
    echo "   Linux: sudo apt install ffmpeg"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✓ Created .env file. Please add your API credentials."
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Quick Usage:"
echo ""
echo "System 1 - Convert YouTube to TikTok:"
echo "  python -m yt2tik.main --url 'https://youtube.com/watch?v=XXX' --auto-upload"
echo ""
echo "System 2 - Analyze YouTube content:"
echo "  python -m yt_analyzer.main --mode search --query 'viral videos' --limit 25"
echo ""
echo "For more examples, see README.md"
