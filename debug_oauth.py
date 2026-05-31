"""
Debug version - Shows exact OAuth URL and credentials
"""
from flask import Flask, render_template, redirect, url_for
import os
from dotenv import load_dotenv
import hashlib
import base64
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = 'debug-secret-key'


@app.route('/')
def index():
    """Debug page"""
    client_key = os.getenv('TIKTOK_CLIENT_KEY')
    client_secret = os.getenv('TIKTOK_CLIENT_SECRET')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TikTok OAuth Debug</title>
        <style>
            body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
            .box {{ background: white; padding: 30px; border-radius: 10px; margin: 20px 0; }}
            .success {{ background: #d4edda; border-left: 4px solid #28a745; }}
            .error {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
            .info {{ background: #d1ecf1; border-left: 4px solid #0c5460; }}
            code {{ background: #f8f9fa; padding: 5px 10px; border-radius: 5px; }}
            pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            .btn {{ display: inline-block; padding: 15px 30px; background: #007bff; color: white;
                    text-decoration: none; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>🔍 TikTok OAuth Debug Tool</h1>

        <div class="box {'success' if client_key else 'error'}">
            <h2>1. Environment Variables</h2>
            <p><strong>TIKTOK_CLIENT_KEY:</strong>
                {'✅ ' + client_key if client_key else '❌ NOT SET'}
            </p>
            <p><strong>TIKTOK_CLIENT_SECRET:</strong>
                {'✅ ' + client_secret[:10] + '...' if client_secret else '❌ NOT SET'}
            </p>
        </div>

        <div class="box info">
            <h2>2. Redirect URI</h2>
            <p>Your redirect URI should be:</p>
            <pre>http://localhost:5000/tiktok/callback</pre>
            <p>Make sure this EXACTLY matches in TikTok Developer Portal!</p>
        </div>

        <div class="box info">
            <h2>3. OAuth URL</h2>
            <p>This is the URL that will be used for OAuth:</p>
            <pre>{url_for('get_oauth_url', _external=True)}</pre>
            <a href="/oauth_url" class="btn">View Full OAuth URL</a>
        </div>

        <div class="box info">
            <h2>4. Test OAuth</h2>
            <p>Click below to test TikTok OAuth:</p>
            <a href="/test_oauth" class="btn">Test TikTok OAuth</a>
        </div>

        <div class="box info">
            <h2>5. Checklist</h2>
            <ul>
                <li>{'✅' if client_key else '❌'} Client Key is set in .env</li>
                <li>{'✅' if client_secret else '❌'} Client Secret is set in .env</li>
                <li>⏳ Redirect URI matches in TikTok Portal</li>
                <li>⏳ Scopes enabled (video.upload, video.publish)</li>
                <li>⏳ App status is "Live" or "In Review"</li>
            </ul>
        </div>
    </body>
    </html>
    """


@app.route('/oauth_url')
def get_oauth_url():
    """Show OAuth URL"""
    client_key = os.getenv('TIKTOK_CLIENT_KEY')
    redirect_uri = url_for('tiktok_callback', _external=True)

    # Generate PKCE
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    state = secrets.token_urlsafe(32)

    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&scope=video.upload,video.publish"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&state={state}"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth URL</title>
        <style>
            body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
            pre {{ background: white; padding: 20px; border-radius: 10px;
                   word-wrap: break-word; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>Full OAuth URL</h1>
        <pre>{oauth_url}</pre>
        <p><a href="/">← Back</a></p>
    </body>
    </html>
    """


@app.route('/test_oauth')
def test_oauth():
    """Test OAuth"""
    client_key = os.getenv('TIKTOK_CLIENT_KEY')

    if not client_key:
        return "ERROR: TIKTOK_CLIENT_KEY not set in .env file", 500

    redirect_uri = url_for('tiktok_callback', _external=True)

    # Generate PKCE
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    state = secrets.token_urlsafe(32)

    oauth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={client_key}"
        f"&scope=video.upload,video.publish"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
        f"&state={state}"
    )

    return redirect(oauth_url)


@app.route('/tiktok/callback')
def tiktok_callback():
    """OAuth callback"""
    from flask import request

    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth Error</title>
            <style>
                body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
                .error {{ background: #f8d7da; padding: 30px; border-radius: 10px;
                         border-left: 4px solid #dc3545; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>❌ OAuth Error</h1>
                <p><strong>Error:</strong> {error}</p>
                <p><strong>Description:</strong> {error_description or 'No description'}</p>
                <p><a href="/">← Back to Debug</a></p>
            </div>
        </body>
        </html>
        """

    if code:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OAuth Success</title>
            <style>
                body {{ font-family: Arial; padding: 40px; background: #f5f5f5; }}
                .success {{ background: #d4edda; padding: 30px; border-radius: 10px;
                           border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h1>✅ OAuth Successful!</h1>
                <p><strong>Authorization Code:</strong> {code[:20]}...</p>
                <p>OAuth is working! Now you can use the full web_app.py</p>
                <p><a href="/">← Back to Debug</a></p>
            </div>
        </body>
        </html>
        """

    return "No code or error received", 400


if __name__ == '__main__':
    print("="*60)
    print("🔍 TikTok OAuth Debug Tool")
    print("="*60)
    print("")
    print("Open in browser: http://localhost:5000")
    print("")
    print("This will help diagnose OAuth issues")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=5000)
