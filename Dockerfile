# Railway Deployment - YouTube to TikTok Converter
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Upgrade yt-dlp to latest version
RUN pip install --no-cache-dir --upgrade yt-dlp

# Copy application code
COPY . .

# Create necessary directories for uploads/downloads
RUN mkdir -p tmp/yt2tik/downloads tmp/yt2tik/output logs reports

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=integrated_app.py

# Railway provides PORT environment variable dynamically
# Do NOT set a default port here - let Railway control it

# Expose port (Railway ignores this but good practice)
EXPOSE 8080

# Run the application - $PORT is provided by Railway
# Use app.py for simple API or integrated_app.py for full web app
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --access-logfile - --error-logfile -
