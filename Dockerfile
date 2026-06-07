# Hugging Face Spaces - FastAPI Docker Configuration
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

# Hugging Face Spaces provides PORT environment variable
# Default fallback is handled in app.py (7860)

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run FastAPI application with uvicorn
# The app.py handles PORT environment variable correctly with fallback to 7860
CMD ["python", "app.py"]
