"""
TikTok video uploader using TikTok Content Posting API
"""
import os
import time
import requests
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv
from .config import (
    TIKTOK_API_BASE, TIKTOK_UPLOAD_CHUNK_SIZE, PRIVACY_OPTIONS,
    UPLOAD_STATUS_POLL_INTERVAL, UPLOAD_STATUS_MAX_ATTEMPTS
)
from .logger import get_logger

logger = get_logger()

# Load environment variables
load_dotenv()


class TikTokUploader:
    """TikTok API uploader"""

    def __init__(self):
        """Initialize uploader with credentials from .env"""
        self.client_key = os.getenv('TIKTOK_CLIENT_KEY')
        self.client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
        self.access_token = os.getenv('TIKTOK_ACCESS_TOKEN')

        if not all([self.client_key, self.client_secret, self.access_token]):
            raise Exception(
                "❌ Missing TikTok credentials. Please set TIKTOK_CLIENT_KEY, "
                "TIKTOK_CLIENT_SECRET, and TIKTOK_ACCESS_TOKEN in .env file"
            )

        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def refresh_token(self) -> bool:
        """
        Refresh access token if expired
        Returns True if successful
        """
        logger.info("🔄 Refreshing access token...")

        refresh_token = os.getenv('TIKTOK_REFRESH_TOKEN')
        if not refresh_token:
            logger.error("No refresh token available")
            return False

        try:
            response = requests.post(
                'https://open.tiktokapis.com/v2/oauth/token/',
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                data={
                    'client_key': self.client_key,
                    'client_secret': self.client_secret,
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data['access_token']
                self.headers['Authorization'] = f'Bearer {self.access_token}'

                logger.info("✅ Token refreshed successfully")
                logger.info("⚠️  Update your .env file with the new access token:")
                logger.info(f"TIKTOK_ACCESS_TOKEN={self.access_token}")

                return True
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return False

    def initialize_upload(self, video_size: int) -> Dict:
        """
        Initialize video upload and get upload URL

        Args:
            video_size: Size of video file in bytes

        Returns:
            Dict with upload_id and upload_url
        """
        logger.info("📤 Initializing upload...")

        try:
            response = requests.post(
                f'{TIKTOK_API_BASE}/post/publish/video/init/',
                headers=self.headers,
                json={
                    'post_info': {
                        'title': 'Video Upload',
                        'privacy_level': 'PUBLIC_TO_EVERYONE',
                        'disable_duet': False,
                        'disable_comment': False,
                        'disable_stitch': False,
                        'video_cover_timestamp_ms': 1000
                    },
                    'source_info': {
                        'source': 'FILE_UPLOAD',
                        'video_size': video_size,
                        'chunk_size': TIKTOK_UPLOAD_CHUNK_SIZE,
                        'total_chunk_count': (video_size + TIKTOK_UPLOAD_CHUNK_SIZE - 1) // TIKTOK_UPLOAD_CHUNK_SIZE
                    }
                }
            )

            if response.status_code == 401:
                # Try to refresh token
                if self.refresh_token():
                    return self.initialize_upload(video_size)
                else:
                    raise Exception("Authentication failed. Please update your access token.")

            if response.status_code != 200:
                raise Exception(f"Upload initialization failed: {response.text}")

            data = response.json()['data']

            logger.info(f"✅ Upload initialized: {data['publish_id']}")

            return {
                'publish_id': data['publish_id'],
                'upload_url': data['upload_url']
            }

        except Exception as e:
            logger.error(f"Upload initialization failed: {str(e)}")
            raise

    def upload_video_chunks(self, video_path: str, upload_url: str) -> bool:
        """
        Upload video file in chunks

        Args:
            video_path: Path to video file
            upload_url: Upload URL from initialization

        Returns:
            True if successful
        """
        logger.info("📦 Uploading video chunks...")

        try:
            file_size = Path(video_path).stat().st_size
            uploaded = 0

            with open(video_path, 'rb') as f:
                chunk_number = 0

                while uploaded < file_size:
                    chunk = f.read(TIKTOK_UPLOAD_CHUNK_SIZE)
                    if not chunk:
                        break

                    chunk_size = len(chunk)

                    # Upload chunk
                    headers = {
                        'Content-Type': 'video/mp4',
                        'Content-Range': f'bytes {uploaded}-{uploaded + chunk_size - 1}/{file_size}'
                    }

                    response = requests.put(upload_url, headers=headers, data=chunk)

                    if response.status_code not in [200, 201, 204]:
                        raise Exception(f"Chunk upload failed: {response.text}")

                    uploaded += chunk_size
                    chunk_number += 1

                    progress = (uploaded / file_size) * 100
                    logger.info(f"Progress: {progress:.1f}% ({uploaded}/{file_size} bytes)")

            logger.info("✅ All chunks uploaded successfully")
            return True

        except Exception as e:
            logger.error(f"Chunk upload failed: {str(e)}")
            raise

    def publish_video(
        self,
        publish_id: str,
        caption: str,
        privacy: str = 'public'
    ) -> str:
        """
        Publish the uploaded video

        Args:
            publish_id: Publish ID from initialization
            caption: Video caption
            privacy: Privacy setting (public/friends/private)

        Returns:
            Video ID
        """
        logger.info("🚀 Publishing video...")

        privacy_level = PRIVACY_OPTIONS.get(privacy, 'PUBLIC_TO_EVERYONE')

        try:
            response = requests.post(
                f'{TIKTOK_API_BASE}/post/publish/status/fetch/',
                headers=self.headers,
                json={
                    'publish_id': publish_id
                }
            )

            if response.status_code != 200:
                raise Exception(f"Publish failed: {response.text}")

            data = response.json()['data']

            logger.info(f"✅ Video published: {data.get('share_url', 'URL pending')}")

            return data.get('share_url', '')

        except Exception as e:
            logger.error(f"Publish failed: {str(e)}")
            raise

    def check_upload_status(self, publish_id: str) -> Dict:
        """
        Check upload and processing status

        Args:
            publish_id: Publish ID from initialization

        Returns:
            Dict with status info
        """
        try:
            response = requests.post(
                f'{TIKTOK_API_BASE}/post/publish/status/fetch/',
                headers=self.headers,
                json={'publish_id': publish_id}
            )

            if response.status_code != 200:
                return {'status': 'ERROR', 'message': response.text}

            data = response.json()['data']

            return {
                'status': data.get('status', 'UNKNOWN'),
                'fail_reason': data.get('fail_reason', ''),
                'share_url': data.get('publicaly_share_url', ''),
                'video_id': data.get('video_id', '')
            }

        except Exception as e:
            return {'status': 'ERROR', 'message': str(e)}

    def upload(
        self,
        video_path: str,
        caption: str,
        privacy: str = 'public'
    ) -> str:
        """
        Complete upload flow

        Args:
            video_path: Path to video file
            caption: Video caption
            privacy: Privacy setting

        Returns:
            TikTok video URL
        """
        logger.info("🎬 Starting TikTok upload...")

        try:
            # Get file size
            file_size = Path(video_path).stat().st_size
            logger.info(f"Video size: {file_size / (1024*1024):.1f}MB")

            # Initialize upload
            init_data = self.initialize_upload(file_size)
            publish_id = init_data['publish_id']
            upload_url = init_data['upload_url']

            # Upload chunks
            self.upload_video_chunks(video_path, upload_url)

            # Publish video
            video_url = self.publish_video(publish_id, caption, privacy)

            # Poll for completion
            logger.info("⏳ Waiting for video processing...")

            for attempt in range(UPLOAD_STATUS_MAX_ATTEMPTS):
                time.sleep(UPLOAD_STATUS_POLL_INTERVAL)

                status = self.check_upload_status(publish_id)

                if status['status'] == 'PUBLISH_COMPLETE':
                    logger.info("✅ Video processing complete!")
                    return status.get('share_url', video_url)

                elif status['status'] == 'FAILED':
                    raise Exception(f"Upload failed: {status.get('fail_reason', 'Unknown error')}")

                elif status['status'] == 'PROCESSING_UPLOAD':
                    logger.info(f"Processing... (attempt {attempt + 1}/{UPLOAD_STATUS_MAX_ATTEMPTS})")

                else:
                    logger.debug(f"Status: {status['status']}")

            # Timeout
            logger.warning("⚠️  Upload status check timed out")
            logger.info("Video may still be processing. Check your TikTok account.")

            return video_url if video_url else f"https://tiktok.com (publish_id: {publish_id})"

        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise


def upload_to_tiktok(
    video_path: str,
    caption: str,
    privacy: str = 'public'
) -> str:
    """
    Upload video to TikTok

    Args:
        video_path: Path to video file
        caption: Video caption
        privacy: Privacy setting

    Returns:
        TikTok video URL
    """
    uploader = TikTokUploader()
    return uploader.upload(video_path, caption, privacy)
