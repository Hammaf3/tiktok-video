"""
Advanced YouTube Analyzer with Country Filter
Search any video type and get top ranked videos by country
"""
from flask import Flask, render_template, request, jsonify
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timezone
import math

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'analyzer-secret-key')

# Country codes for region filtering
COUNTRIES = {
    'pakistan': {'code': 'PK', 'name': 'Pakistan', 'flag': '🇵🇰'},
    'uk': {'code': 'GB', 'name': 'United Kingdom', 'flag': '🇬🇧'},
    'us': {'code': 'US', 'name': 'United States', 'flag': '🇺🇸'},
    'canada': {'code': 'CA', 'name': 'Canada', 'flag': '🇨🇦'},
    'australia': {'code': 'AU', 'name': 'Australia', 'flag': '🇦🇺'},
    'india': {'code': 'IN', 'name': 'India', 'flag': '🇮🇳'},
}


def get_youtube_client():
    """Initialize YouTube API client"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        raise Exception("YouTube API key not found in .env file")
    return build('youtube', 'v3', developerKey=api_key)


def search_videos(query, country_code, max_results=30):
    """Search videos by query and country"""
    youtube = get_youtube_client()

    try:
        # Search for videos
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            type='video',
            maxResults=max_results,
            order='viewCount',  # Order by view count
            regionCode=country_code,
            relevanceLanguage='en' if country_code in ['US', 'GB', 'CA', 'AU'] else None
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response['items']]

        if not video_ids:
            return []

        # Get detailed video statistics
        videos_response = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(video_ids)
        ).execute()

        videos = []
        for item in videos_response['items']:
            snippet = item['snippet']
            statistics = item['statistics']
            content_details = item['contentDetails']

            # Parse duration
            duration_seconds = parse_duration(content_details['duration'])

            # Parse published date
            published_at = datetime.fromisoformat(
                snippet['publishedAt'].replace('Z', '+00:00')
            )

            video_data = {
                'video_id': item['id'],
                'title': snippet['title'],
                'channel': snippet['channelTitle'],
                'published_at': published_at,
                'thumbnail': snippet['thumbnails']['high']['url'],
                'duration_seconds': duration_seconds,
                'view_count': int(statistics.get('viewCount', 0)),
                'like_count': int(statistics.get('likeCount', 0)),
                'comment_count': int(statistics.get('commentCount', 0)),
                'url': f"https://youtube.com/watch?v={item['id']}"
            }

            # Calculate viral score
            video_data['viral_score'] = calculate_viral_score(video_data)
            video_data['days_old'] = (datetime.now(timezone.utc) - published_at.replace(tzinfo=timezone.utc)).days

            videos.append(video_data)

        # Sort by viral score
        videos.sort(key=lambda x: x['viral_score'], reverse=True)

        return videos

    except Exception as e:
        raise Exception(f"Search failed: {str(e)}")


def parse_duration(duration_str):
    """Parse ISO 8601 duration to seconds"""
    duration_str = duration_str.replace('PT', '')

    hours = 0
    minutes = 0
    seconds = 0

    if 'H' in duration_str:
        hours = int(duration_str.split('H')[0])
        duration_str = duration_str.split('H')[1]

    if 'M' in duration_str:
        minutes = int(duration_str.split('M')[0])
        duration_str = duration_str.split('M')[1]

    if 'S' in duration_str:
        seconds = int(duration_str.split('S')[0])

    return hours * 3600 + minutes * 60 + seconds


def calculate_viral_score(video):
    """Calculate viral score (0-100)"""
    views = video['view_count']
    likes = video['like_count']
    comments = video['comment_count']
    duration = video['duration_seconds']
    days_old = (datetime.now(timezone.utc) - video['published_at'].replace(tzinfo=timezone.utc)).days

    if views == 0:
        return 0

    # Engagement rate
    engagement_rate = ((likes + comments) / views) * 100

    # Velocity (views per day)
    velocity = views / max(1, days_old)

    # Like ratio
    like_ratio = likes / views if views > 0 else 0

    # Duration bonus (30-90 seconds is ideal for TikTok)
    duration_bonus = 1.2 if 30 <= duration <= 90 else 1.0

    # Recency bonus
    recency_bonus = 1.3 if days_old <= 30 else 1.0

    # Calculate score
    raw_score = (
        (engagement_rate * 40) +
        (math.log10(max(1, velocity)) * 30) +
        (like_ratio * 100 * 20) +
        (math.log10(max(1, views)) * 10)
    )

    final_score = min(100, raw_score * duration_bonus * recency_bonus)

    return round(final_score, 1)


def format_number(num):
    """Format large numbers"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def format_duration(seconds):
    """Format duration as MM:SS"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


@app.route('/')
def index():
    """Main analyzer page"""
    return render_template('analyzer.html', countries=COUNTRIES)


@app.route('/search', methods=['POST'])
def search():
    """Search videos"""
    try:
        data = request.json
        query = data.get('query')
        country = data.get('country', 'us')
        limit = int(data.get('limit', 25))

        if not query:
            return jsonify({'error': 'Search query is required'}), 400

        country_code = COUNTRIES.get(country, {}).get('code', 'US')

        # Search videos
        videos = search_videos(query, country_code, limit)

        # Format for response
        results = []
        for i, video in enumerate(videos, 1):
            results.append({
                'rank': i,
                'title': video['title'],
                'channel': video['channel'],
                'url': video['url'],
                'thumbnail': video['thumbnail'],
                'views': format_number(video['view_count']),
                'views_raw': video['view_count'],
                'likes': format_number(video['like_count']),
                'comments': format_number(video['comment_count']),
                'duration': format_duration(video['duration_seconds']),
                'duration_seconds': video['duration_seconds'],
                'days_old': video['days_old'],
                'viral_score': video['viral_score'],
                'video_id': video['video_id']
            })

        return jsonify({
            'success': True,
            'query': query,
            'country': COUNTRIES.get(country, {}).get('name', 'Unknown'),
            'total': len(results),
            'videos': results
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/convert/<video_id>')
def convert_video(video_id):
    """Redirect to converter with video ID"""
    return f"https://youtube.com/watch?v={video_id}"


if __name__ == '__main__':
    print("="*60)
    print("🔍 YouTube Video Analyzer with Country Filter")
    print("="*60)
    print("")
    print("✅ Search any video type")
    print("✅ Filter by country (Pakistan, UK, US, Canada, Australia)")
    print("✅ Get top 20-30 videos ranked by viral score")
    print("✅ High views, best engagement")
    print("")
    print("Open in browser: http://localhost:5001")
    print("")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=5001)
