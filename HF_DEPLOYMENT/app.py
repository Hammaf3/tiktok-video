"""
FastAPI Application for Hugging Face Spaces
With Frontend Integration
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import os
import sys

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

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve frontend HTML"""
    return templates.TemplateResponse("index.html", {"request": request})

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
            {"path": "/", "method": "GET", "description": "Frontend UI"},
            {"path": "/health", "method": "GET", "description": "Health check"},
            {"path": "/api/info", "method": "GET", "description": "API information"},
            {"path": "/convert", "method": "POST", "description": "Convert video"},
            {"path": "/docs", "method": "GET", "description": "API documentation"},
        ]
    }

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
    port_env = os.getenv("PORT", "").strip()

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
