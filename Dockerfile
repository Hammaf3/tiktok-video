# Hugging Face Docker Space - YouTube to TikTok Converter
FROM python:3.11-slim

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
ENV PORT=7860

# Expose Hugging Face Space port
EXPOSE 7860

# Run the application on 0.0.0.0:7860
CMD ["gunicorn", "integrated_app:app", "--bind", "0.0.0.0:7860", "--workers", "2", "--timeout", "300", "--access-logfile", "-", "--error-logfile", "-"]
