"""
Simple test endpoint for Vercel debugging
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Vercel deployment is working',
        'platform': 'vercel'
    })

@app.route('/api/test')
def test():
    return jsonify({
        'status': 'ok',
        'message': 'API endpoint working'
    })
