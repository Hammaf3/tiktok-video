#!/bin/bash
# Entrypoint script for Hugging Face Spaces
# Handles PORT environment variable with proper empty string handling

set -e

# Handle PORT environment variable
if [ -z "$PORT" ]; then
    echo "⚠️  PORT environment variable is empty or not set"
    export PORT=7860
    echo "✅ Using fallback PORT: $PORT"
else
    echo "✅ Using PORT from environment: $PORT"
fi

echo ""
echo "=========================================="
echo "🚀 YouTube to TikTok Converter"
echo "=========================================="
echo "Starting server on 0.0.0.0:$PORT"
echo "=========================================="
echo ""

# Start gunicorn with the properly set PORT
exec gunicorn integrated_app:app \
    --bind "0.0.0.0:$PORT" \
    --workers 2 \
    --timeout 300 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
