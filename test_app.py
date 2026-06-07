"""
Minimal Flask app for Railway deployment testing
If this doesn't work, the issue is with Railway configuration
"""
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'alive',
        'message': 'Minimal test app is working',
        'port': os.getenv('PORT', 'not set')
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/terms')
def terms():
    return '<h1>Terms of Service</h1><p>Test page</p>'

@app.route('/privacy')
def privacy():
    return '<h1>Privacy Policy</h1><p>Test page</p>'

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
