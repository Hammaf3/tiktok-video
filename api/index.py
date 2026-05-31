"""
Vercel Serverless Function Entry Point - Minimal Version
This version removes features incompatible with serverless:
- No background threading
- No file system operations
- No long-running video processing
"""
from flask import Flask, jsonify, request, render_template_string
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'vercel-secret-key')

# Simple HTML template
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>YouTube to TikTok Converter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .info {
            background: #d1ecf1;
            border: 1px solid #0dcaf0;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #dc3545;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        ul { line-height: 1.8; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube to TikTok Converter</h1>

        <div class="error">
            <strong>⚠️ Deployment Issue Detected</strong>
            <p>This application cannot run on Vercel's serverless platform due to architectural limitations.</p>
        </div>

        <div class="info">
            <strong>✅ Vercel Connection Working</strong>
            <p>Your Vercel deployment is configured correctly, but this app needs a traditional server environment.</p>
        </div>

        <h2>Why This Doesn't Work on Vercel:</h2>
        <ul>
            <li><strong>Video Processing:</strong> Takes 2-5 minutes (Vercel limit: 10-60 seconds)</li>
            <li><strong>File Storage:</strong> Needs persistent storage (Vercel: read-only filesystem)</li>
            <li><strong>Background Jobs:</strong> Uses threading (Vercel: stateless functions)</li>
            <li><strong>FFmpeg:</strong> Requires binary not available in Vercel runtime</li>
        </ul>

        <h2>✨ Recommended Solution: Railway.app</h2>
        <div class="info">
            <p><strong>Railway.app</strong> is perfect for this application:</p>
            <ul>
                <li>✅ Supports long-running processes</li>
                <li>✅ Persistent file storage</li>
                <li>✅ FFmpeg pre-installed</li>
                <li>✅ Easy GitHub deployment</li>
                <li>✅ Cost: ~$5/month</li>
            </ul>
        </div>

        <h2>🚀 Quick Migration Steps:</h2>
        <ol>
            <li>Push your code to GitHub (if not already)</li>
            <li>Go to <a href="https://railway.app" target="_blank">railway.app</a></li>
            <li>Sign up with GitHub</li>
            <li>Click "New Project" → "Deploy from GitHub repo"</li>
            <li>Select your repository</li>
            <li>Add environment variables from your <code>.env</code> file</li>
            <li>Railway will auto-detect Flask and deploy</li>
            <li>Your app will be live in 2-3 minutes!</li>
        </ol>

        <h2>📋 Alternative Platforms:</h2>
        <ul>
            <li><strong>Render.com</strong> - Free tier available</li>
            <li><strong>Fly.io</strong> - Global deployment</li>
            <li><strong>DigitalOcean App Platform</strong> - $5/month</li>
            <li><strong>Heroku</strong> - Classic PaaS (more expensive)</li>
        </ul>

        <div class="warning">
            <strong>📝 Note:</strong> See <code>VERCEL_DEPLOYMENT_ISSUES.md</code> in your project for detailed technical explanation.
        </div>

        <h2>🔧 API Status Check:</h2>
        <p><a href="/api/health">Check API Health</a></p>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page explaining the deployment issue"""
    return render_template_string(HOME_TEMPLATE)

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Vercel deployment is working',
        'platform': 'vercel',
        'note': 'Video processing features disabled - incompatible with serverless',
        'recommendation': 'Deploy to Railway.app or similar PaaS platform'
    })

@app.route('/api/info')
def info():
    """Deployment information"""
    return jsonify({
        'platform': 'Vercel',
        'compatible': False,
        'issues': [
            'Execution time limit (10-60s)',
            'Read-only filesystem',
            'No background processing',
            'No FFmpeg binary'
        ],
        'recommended_platforms': [
            'Railway.app',
            'Render.com',
            'Fly.io',
            'DigitalOcean App Platform'
        ]
    })

# Catch-all route
@app.route('/<path:path>')
def catch_all(path):
    """Catch all other routes"""
    return jsonify({
        'error': 'This endpoint is not available in the Vercel deployment',
        'message': 'Please deploy to Railway.app or similar platform for full functionality',
        'requested_path': f'/{path}'
    }), 404

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found', 'message': 'Deploy to Railway.app for full functionality'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error', 'message': str(e)}), 500
