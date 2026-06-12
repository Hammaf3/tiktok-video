# Hugging Face Spaces - FastAPI Application with Embedded Frontend
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
# app.py handles PORT with fallback to 7860

# Expose port 7860 (Hugging Face Spaces default)
EXPOSE 7860

# Run FastAPI application
# app.py has proper PORT handling built-in
CMD ["python", "app.py"]
