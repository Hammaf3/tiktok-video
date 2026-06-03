#!/bin/bash
# Railway Debug Script - Run this in Railway shell

echo "=== yt-dlp Configuration Detective ==="
echo ""

echo "1. Searching for yt-dlp config files..."
find / -name "yt-dlp.conf" 2>/dev/null || echo "   Not found"
find / -name "yt-dlp" -type d 2>/dev/null | head -5
echo ""

echo "2. Checking common config locations..."
cat ~/.config/yt-dlp/config 2>/dev/null && echo "   ✅ Found in ~/.config/yt-dlp/config" || echo "   ❌ Not in ~/.config/yt-dlp/config"
cat ~/.yt-dlp.conf 2>/dev/null && echo "   ✅ Found in ~/.yt-dlp.conf" || echo "   ❌ Not in ~/.yt-dlp.conf"
cat /etc/yt-dlp.conf 2>/dev/null && echo "   ✅ Found in /etc/yt-dlp.conf" || echo "   ❌ Not in /etc/yt-dlp.conf"
echo ""

echo "3. Searching for 'deno' in config directories..."
grep -r "deno" ~/.config/ 2>/dev/null | head -10 || echo "   Not found"
grep -r "js_runtime" ~/.config/ 2>/dev/null | head -10 || echo "   Not found"
echo ""

echo "4. Checking Python cache..."
find /app -name "__pycache__" -type d 2>/dev/null | head -10
find /app -name "*.pyc" 2>/dev/null | head -10
echo ""

echo "5. Checking environment variables..."
env | grep -i ytdl || echo "   No YTDL variables"
env | grep -i deno || echo "   No DENO variables"
echo ""

echo "6. yt-dlp package info..."
python3 -c "import yt_dlp; print('Version:', yt_dlp.version.__version__); print('Location:', yt_dlp.__file__)"
echo ""

echo "=== Search Complete ==="
