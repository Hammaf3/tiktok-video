"""
FastAPI Application for Hugging Face Spaces
Correctly handles PORT environment variable with fallback
"""
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import uuid
import asyncio
from pathlib import Path

# Fix Windows console encoding for Unicode characters
try:
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
except:
    pass

# Initialize FastAPI app
app = FastAPI(
    title="YouTube to TikTok Converter",
    description="Convert YouTube videos to TikTok format",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class ConvertRequest(BaseModel):
    youtube_url: str

class ConvertResponse(BaseModel):
    status: str
    message: str
    job_id: str = None
    download_url: str = None

# In-memory job store (simple implementation)
jobs = {}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Serves HTML frontend"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube to TikTok Converter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            animation: slideUp 0.5s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .logo {
            font-size: 48px;
            margin-bottom: 10px;
        }

        h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }

        .subtitle {
            color: #666;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }

        input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 15px;
            transition: all 0.3s ease;
            outline: none;
        }

        input[type="text"]:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            outline: none;
        }

        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .message {
            margin-top: 20px;
            padding: 16px;
            border-radius: 10px;
            font-size: 14px;
            display: none;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .message.success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }

        .message.error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }

        .message.info {
            background: #d1ecf1;
            border: 1px solid #bee5eb;
            color: #0c5460;
        }

        .loader {
            display: none;
            text-align: center;
            margin-top: 20px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .download-link {
            display: inline-block;
            margin-top: 12px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            transition: background 0.3s ease;
        }

        .download-link:hover {
            background: #218838;
        }

        .footer {
            text-align: center;
            margin-top: 30px;
            color: #999;
            font-size: 13px;
        }

        @media (max-width: 480px) {
            .container {
                padding: 30px 20px;
            }

            h1 {
                font-size: 24px;
            }

            .logo {
                font-size: 40px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎬</div>
            <h1>YouTube to TikTok Converter</h1>
            <p class="subtitle">Convert any YouTube video to TikTok format</p>
        </div>

        <form id="convertForm">
            <div class="form-group">
                <label for="youtubeUrl">YouTube Video URL</label>
                <input
                    type="text"
                    id="youtubeUrl"
                    name="youtube_url"
                    placeholder="https://www.youtube.com/watch?v=..."
                    required
                />
            </div>

            <button type="submit" id="convertBtn">
                Convert to TikTok
            </button>
        </form>

        <div class="loader" id="loader">
            <div class="spinner"></div>
            <p>Converting your video... Please wait</p>
        </div>

        <div class="message" id="message"></div>

        <div class="footer">
            Powered by FastAPI • Deployed on Hugging Face Spaces
        </div>
    </div>

    <script>
        const form = document.getElementById('convertForm');
        const convertBtn = document.getElementById('convertBtn');
        const loader = document.getElementById('loader');
        const message = document.getElementById('message');
        const youtubeUrl = document.getElementById('youtubeUrl');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const url = youtubeUrl.value.trim();

            if (!url) {
                showMessage('Please enter a YouTube URL', 'error');
                return;
            }

            // Basic URL validation
            if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                showMessage('Please enter a valid YouTube URL', 'error');
                return;
            }

            // Show loading state
            convertBtn.disabled = true;
            convertBtn.textContent = 'Converting...';
            loader.style.display = 'block';
            message.style.display = 'none';

            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ youtube_url: url })
                });

                const data = await response.json();

                if (response.ok) {
                    if (data.download_url) {
                        showMessage(
                            `✅ Video converted successfully!<br><a href="${data.download_url}" class="download-link" download>Download Video</a>`,
                            'success'
                        );
                    } else {
                        showMessage('✅ ' + (data.message || 'Video converted successfully!'), 'success');
                    }
                } else {
                    showMessage('❌ ' + (data.detail || data.error || 'Conversion failed'), 'error');
                }
            } catch (error) {
                showMessage('❌ Network error. Please try again.', 'error');
                console.error('Error:', error);
            } finally {
                // Reset UI
                convertBtn.disabled = false;
                convertBtn.textContent = 'Convert to TikTok';
                loader.style.display = 'none';
            }
        });

        function showMessage(text, type) {
            message.innerHTML = text;
            message.className = 'message ' + type;
            message.style.display = 'block';
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint for Hugging Face Spaces"""
    return {
        "status": "healthy",
        "port": os.getenv("PORT", "7860"),
        "environment": "huggingface"
    }

@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "YouTube to TikTok Converter",
        "version": "1.0.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Web UI"},
            {"path": "/convert", "method": "POST", "description": "Convert video"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/api/info", "method": "GET", "description": "API information"},
        ]
    }

@app.post("/convert")
async def convert_video(request: ConvertRequest):
    """Convert YouTube video to TikTok format"""
    youtube_url = request.youtube_url.strip()

    # Validate URL
    if not youtube_url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    if "youtube.com" not in youtube_url and "youtu.be" not in youtube_url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    # Generate job ID
    job_id = str(uuid.uuid4())

    try:
        # DEMO MODE: Skip actual conversion for now
        # TODO: Enable actual conversion after debugging
        print(f"📝 Demo mode: Request received for {youtube_url}")

        jobs[job_id] = {
            "status": "completed",
            "youtube_url": youtube_url,
            "demo": True
        }

        return {
            "status": "success",
            "message": "✅ Video URL validated! (Demo mode - actual conversion disabled for debugging)",
            "job_id": job_id,
            "download_url": None
        }

        # Original code commented out for debugging:
        """
        # Try to import and use the actual conversion modules
        try:
            from yt2tik.downloader_enhanced import download_youtube_video
            from yt2tik.converter import convert_to_tiktok_format

            # Create output directory
            output_dir = Path("tmp/yt2tik/output")
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download video
            print(f"📥 Downloading video: {youtube_url}")
            video_path = download_youtube_video(youtube_url)

            if not video_path or not Path(video_path).exists():
                raise Exception("Failed to download video")

            # Convert to TikTok format
            print(f"🔄 Converting to TikTok format...")
            output_path = convert_to_tiktok_format(video_path, str(output_dir))

            if not output_path or not Path(output_path).exists():
                raise Exception("Failed to convert video")

            # Store job result
            jobs[job_id] = {
                "status": "completed",
                "output_path": output_path,
                "youtube_url": youtube_url
            }

            # Return success with download link
            filename = Path(output_path).name
            return {
                "status": "success",
                "message": "Video converted successfully!",
                "job_id": job_id,
                "download_url": f"/download/{filename}"
            }

        except ImportError as e:
            # Modules not available - return mock response
            print(f"⚠️ Conversion modules not available: {e}")
            print(f"📝 Mock conversion for: {youtube_url}")

            jobs[job_id] = {
                "status": "completed",
                "youtube_url": youtube_url,
                "mock": True
            }

            return {
                "status": "success",
                "message": "Video conversion queued! (Demo mode - actual conversion modules not loaded)",
                "job_id": job_id,
                "download_url": None
            }
        """

    except Exception as e:
        # Handle any errors in demo mode
        error_msg = str(e)
        print(f"❌ Error in demo mode: {error_msg}")

        jobs[job_id] = {
            "status": "failed",
            "error": error_msg,
            "youtube_url": youtube_url
        }

        raise HTTPException(
            status_code=500,
            detail=f"Error: {error_msg}"
        )

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get conversion job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return jobs[job_id]

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download converted video file"""
    from fastapi.responses import FileResponse

    # Security: prevent directory traversal
    filename = Path(filename).name

    # Check in output directory
    file_path = Path("tmp/yt2tik/output") / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=filename
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Correctly read PORT environment variable with fallback
    # Handle empty string case explicitly
    port_env = os.getenv("PORT", "").strip()

    # Use 7860 as fallback if PORT is empty or not set
    if not port_env:
        port = 7860
        print(f"⚠️  PORT environment variable is empty or not set, using fallback: {port}")
    else:
        try:
            port = int(port_env)
            print(f"✅ Using PORT from environment: {port}")
        except ValueError:
            port = 7860
            print(f"⚠️  Invalid PORT value '{port_env}', using fallback: {port}")

    # Run uvicorn server
    print(f"🚀 Starting FastAPI server on 0.0.0.0:{port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
