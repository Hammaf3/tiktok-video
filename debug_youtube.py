"""
Debug script to test YouTube OAuth and API calls
"""
from flask import Flask, session, redirect, url_for, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'test-secret-key')

YOUTUBE_SCOPES = [
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

@app.route('/')
def index():
    """Test page"""
    youtube_connected = session.get('youtube_connected', False)

    html = f"""
    <h1>YouTube OAuth Debug</h1>
    <p><strong>Status:</strong> {'✅ Connected' if youtube_connected else '❌ Not Connected'}</p>

    {f'<p><strong>Session Data:</strong></p><pre>{json.dumps(dict(session), indent=2, default=str)}</pre>' if youtube_connected else ''}

    <hr>
    <a href="/test_channels">Test: Fetch Channels</a><br><br>
    <a href="/test_api_key">Test: API Key (Public)</a><br><br>
    <a href="/clear_session">Clear Session</a><br><br>
    """

    return html

@app.route('/test_channels')
def test_channels():
    """Test fetching channels with OAuth"""
    try:
        if not session.get('youtube_connected'):
            return "<h2>❌ Not Connected</h2><p>YouTube account not connected in session</p><a href='/'>← Back</a>"

        creds_data = session.get('youtube_credentials')
        if not creds_data:
            return "<h2>❌ No Credentials</h2><p>No credentials found in session</p><a href='/'>← Back</a>"

        # Create credentials object
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        # Build YouTube client
        youtube = build('youtube', 'v3', credentials=credentials)

        # Fetch channels
        channels_response = youtube.channels().list(
            part='snippet,contentDetails,statistics',
            mine=True
        ).execute()

        channels = []
        for item in channels_response.get('items', []):
            channels.append({
                'id': item['id'],
                'title': item['snippet']['title'],
                'description': item['snippet']['description'][:100],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'subscriber_count': item['statistics'].get('subscriberCount', 0),
                'video_count': item['statistics'].get('videoCount', 0),
            })

        html = f"""
        <h1>✅ Channels Fetched Successfully</h1>
        <p><strong>Total Channels:</strong> {len(channels)}</p>
        <hr>
        """

        for channel in channels:
            html += f"""
            <div style="border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <img src="{channel['thumbnail']}" style="width: 100px; height: 100px; border-radius: 50%;">
                <h3>{channel['title']}</h3>
                <p>{channel['description']}</p>
                <p>👥 {channel['subscriber_count']} subscribers | 🎬 {channel['video_count']} videos</p>
                <p><strong>Channel ID:</strong> {channel['id']}</p>
                <a href="/test_videos/{channel['id']}">View Videos →</a>
            </div>
            """

        html += '<hr><a href="/">← Back</a>'
        return html

    except Exception as e:
        return f"""
        <h1>❌ Error</h1>
        <p><strong>Error Type:</strong> {type(e).__name__}</p>
        <p><strong>Error Message:</strong> {str(e)}</p>
        <pre>{repr(e)}</pre>
        <hr>
        <a href="/">← Back</a>
        """

@app.route('/test_videos/<channel_id>')
def test_videos(channel_id):
    """Test fetching videos from a channel"""
    try:
        if not session.get('youtube_connected'):
            return "<h2>❌ Not Connected</h2><a href='/'>← Back</a>"

        creds_data = session.get('youtube_credentials')
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )

        youtube = build('youtube', 'v3', credentials=credentials)

        # Get channel's uploads playlist
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()

        if not channel_response.get('items'):
            return f"<h2>❌ Channel not found</h2><p>Channel ID: {channel_id}</p><a href='/'>← Back</a>"

        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # Get videos from uploads playlist
        playlist_response = youtube.playlistItems().list(
            part='snippet',
            playlistId=uploads_playlist_id,
            maxResults=10
        ).execute()

        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_response.get('items', [])]

        if not video_ids:
            return f"<h2>⚠️ No Videos Found</h2><p>Channel ID: {channel_id}</p><a href='/'>← Back</a>"

        # Get video details
        videos_response = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=','.join(video_ids)
        ).execute()

        html = f"""
        <h1>✅ Videos Fetched Successfully</h1>
        <p><strong>Total Videos:</strong> {len(videos_response.get('items', []))}</p>
        <hr>
        """

        for item in videos_response.get('items', []):
            html += f"""
            <div style="border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 8px;">
                <img src="{item['snippet']['thumbnails']['high']['url']}" style="width: 200px;">
                <h3>{item['snippet']['title']}</h3>
                <p>👁️ {item['statistics'].get('viewCount', 0)} views</p>
                <p>👍 {item['statistics'].get('likeCount', 0)} likes</p>
                <p><a href="https://youtube.com/watch?v={item['id']}" target="_blank">Watch on YouTube</a></p>
            </div>
            """

        html += '<hr><a href="/">← Back</a>'
        return html

    except Exception as e:
        return f"""
        <h1>❌ Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <pre>{repr(e)}</pre>
        <hr>
        <a href="/">← Back</a>
        """

@app.route('/test_api_key')
def test_api_key():
    """Test YouTube API with API key (public data)"""
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            return "<h2>❌ No API Key</h2><p>YOUTUBE_API_KEY not found in .env</p><a href='/'>← Back</a>"

        youtube = build('youtube', 'v3', developerKey=api_key)

        # Search for a popular video
        search_response = youtube.search().list(
            q='python tutorial',
            part='id,snippet',
            type='video',
            maxResults=5
        ).execute()

        html = f"""
        <h1>✅ API Key Working</h1>
        <p><strong>API Key:</strong> {api_key[:20]}...</p>
        <p><strong>Results:</strong> {len(search_response.get('items', []))} videos found</p>
        <hr>
        """

        for item in search_response.get('items', []):
            html += f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                <h4>{item['snippet']['title']}</h4>
                <p>{item['snippet']['channelTitle']}</p>
            </div>
            """

        html += '<hr><a href="/">← Back</a>'
        return html

    except Exception as e:
        return f"""
        <h1>❌ Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <hr>
        <a href="/">← Back</a>
        """

@app.route('/clear_session')
def clear_session():
    """Clear session data"""
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    print("="*60)
    print("YouTube OAuth Debug Tool")
    print("="*60)
    print("")
    print("Open: http://localhost:5001")
    print("")
    print("This tool will help debug YouTube OAuth issues")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=5001)
