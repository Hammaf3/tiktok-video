"""
YouTube Data API fetcher
"""
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from .config import (
    YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    YOUTUBE_MAX_RESULTS_PER_PAGE
)

# Load environment variables
load_dotenv()


class YouTubeFetcher:
    """YouTube Data API wrapper"""

    def __init__(self):
        """Initialize YouTube API client"""
        api_key = os.getenv('YOUTUBE_API_KEY')

        if not api_key:
            raise Exception(
                "❌ Missing YouTube API key. "
                "Please set YOUTUBE_API_KEY in .env file"
            )

        self.youtube = build(
            YOUTUBE_API_SERVICE_NAME,
            YOUTUBE_API_VERSION,
            developerKey=api_key
        )

    def resolve_channel_id(self, channel_handle: str) -> Optional[str]:
        """
        Resolve channel handle to channel ID

        Args:
            channel_handle: Channel handle (e.g., @MrBeast)

        Returns:
            Channel ID or None
        """
        try:
            # Remove @ if present
            handle = channel_handle.lstrip('@')

            # Try searching by username
            request = self.youtube.search().list(
                part='snippet',
                q=handle,
                type='channel',
                maxResults=1
            )
            response = request.execute()

            if response['items']:
                return response['items'][0]['snippet']['channelId']

            return None

        except HttpError as e:
            raise Exception(f"Failed to resolve channel: {str(e)}")

    def get_channel_videos(
        self,
        channel_id: str,
        limit: int = 50
    ) -> List[str]:
        """
        Get video IDs from a channel

        Args:
            channel_id: YouTube channel ID
            limit: Maximum number of videos

        Returns:
            List of video IDs
        """
        try:
            video_ids = []
            next_page_token = None

            while len(video_ids) < limit:
                request = self.youtube.search().list(
                    part='id',
                    channelId=channel_id,
                    type='video',
                    order='date',
                    maxResults=min(YOUTUBE_MAX_RESULTS_PER_PAGE, limit - len(video_ids)),
                    pageToken=next_page_token
                )
                response = request.execute()

                for item in response['items']:
                    if item['id']['kind'] == 'youtube#video':
                        video_ids.append(item['id']['videoId'])

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return video_ids[:limit]

        except HttpError as e:
            if 'quotaExceeded' in str(e):
                raise Exception("❌ YouTube API quota exceeded. Try again tomorrow.")
            raise Exception(f"Failed to fetch channel videos: {str(e)}")

    def search_videos(
        self,
        query: str,
        limit: int = 50,
        published_after: Optional[str] = None,
        published_before: Optional[str] = None
    ) -> List[str]:
        """
        Search for videos by query

        Args:
            query: Search query
            limit: Maximum number of videos
            published_after: ISO 8601 date (e.g., 2024-01-01T00:00:00Z)
            published_before: ISO 8601 date

        Returns:
            List of video IDs
        """
        try:
            video_ids = []
            next_page_token = None

            while len(video_ids) < limit:
                request_params = {
                    'part': 'id',
                    'q': query,
                    'type': 'video',
                    'order': 'relevance',
                    'maxResults': min(YOUTUBE_MAX_RESULTS_PER_PAGE, limit - len(video_ids)),
                    'pageToken': next_page_token
                }

                if published_after:
                    request_params['publishedAfter'] = published_after
                if published_before:
                    request_params['publishedBefore'] = published_before

                request = self.youtube.search().list(**request_params)
                response = request.execute()

                for item in response['items']:
                    if item['id']['kind'] == 'youtube#video':
                        video_ids.append(item['id']['videoId'])

                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break

            return video_ids[:limit]

        except HttpError as e:
            if 'quotaExceeded' in str(e):
                raise Exception("❌ YouTube API quota exceeded. Try again tomorrow.")
            raise Exception(f"Failed to search videos: {str(e)}")

    def get_video_details(self, video_ids: List[str]) -> List[Dict]:
        """
        Get detailed information for videos

        Args:
            video_ids: List of video IDs

        Returns:
            List of video detail dicts
        """
        try:
            videos = []

            # Process in batches of 50 (API limit)
            for i in range(0, len(video_ids), YOUTUBE_MAX_RESULTS_PER_PAGE):
                batch = video_ids[i:i + YOUTUBE_MAX_RESULTS_PER_PAGE]

                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(batch)
                )
                response = request.execute()

                for item in response['items']:
                    snippet = item['snippet']
                    statistics = item['statistics']
                    content_details = item['contentDetails']

                    # Parse duration (ISO 8601 format: PT1M30S)
                    duration_str = content_details['duration']
                    duration_seconds = self._parse_duration(duration_str)

                    # Parse published date
                    published_at = datetime.fromisoformat(
                        snippet['publishedAt'].replace('Z', '+00:00')
                    )

                    video_data = {
                        'video_id': item['id'],
                        'title': snippet['title'],
                        'description': snippet.get('description', '')[:300],
                        'channel_title': snippet['channelTitle'],
                        'channel_id': snippet['channelId'],
                        'published_at': published_at,
                        'thumbnail_url': snippet['thumbnails']['high']['url'],
                        'duration_seconds': duration_seconds,
                        'view_count': int(statistics.get('viewCount', 0)),
                        'like_count': int(statistics.get('likeCount', 0)),
                        'comment_count': int(statistics.get('commentCount', 0)),
                        'url': f"https://youtube.com/watch?v={item['id']}"
                    }

                    videos.append(video_data)

            return videos

        except HttpError as e:
            if 'quotaExceeded' in str(e):
                raise Exception("❌ YouTube API quota exceeded. Try again tomorrow.")
            raise Exception(f"Failed to fetch video details: {str(e)}")

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse ISO 8601 duration to seconds

        Args:
            duration_str: Duration string (e.g., PT1M30S)

        Returns:
            Duration in seconds
        """
        # Remove PT prefix
        duration_str = duration_str.replace('PT', '')

        hours = 0
        minutes = 0
        seconds = 0

        # Extract hours
        if 'H' in duration_str:
            hours = int(duration_str.split('H')[0])
            duration_str = duration_str.split('H')[1]

        # Extract minutes
        if 'M' in duration_str:
            minutes = int(duration_str.split('M')[0])
            duration_str = duration_str.split('M')[1]

        # Extract seconds
        if 'S' in duration_str:
            seconds = int(duration_str.split('S')[0])

        return hours * 3600 + minutes * 60 + seconds

    def get_channel_info(self, channel_id: str) -> Dict:
        """
        Get channel information

        Args:
            channel_id: Channel ID

        Returns:
            Channel info dict
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()

            if not response['items']:
                return {}

            item = response['items'][0]
            snippet = item['snippet']
            statistics = item['statistics']

            return {
                'channel_id': channel_id,
                'title': snippet['title'],
                'description': snippet.get('description', ''),
                'subscriber_count': int(statistics.get('subscriberCount', 0)),
                'video_count': int(statistics.get('videoCount', 0)),
                'view_count': int(statistics.get('viewCount', 0))
            }

        except HttpError as e:
            return {}
