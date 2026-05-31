"""
Viral score calculation
"""
import math
from datetime import datetime, timezone
from typing import Dict, List
from .config import (
    ENGAGEMENT_WEIGHT, VELOCITY_WEIGHT, LIKE_RATIO_WEIGHT, VIEWS_WEIGHT,
    SHORT_CONTENT_MIN, SHORT_CONTENT_MAX, SHORT_CONTENT_BONUS,
    RECENT_DAYS_THRESHOLD, RECENCY_BONUS,
    CATEGORY_VIRAL, CATEGORY_GROWING, CATEGORY_UNDERRATED, CATEGORY_DECLINING,
    VIRAL_SCORE_THRESHOLD, GROWING_VELOCITY_THRESHOLD, UNDERRATED_VIEW_THRESHOLD
)


def calculate_days_since_published(published_at: datetime) -> float:
    """Calculate days since video was published"""
    now = datetime.now(timezone.utc)
    delta = now - published_at.replace(tzinfo=timezone.utc)
    return max(1, delta.total_seconds() / 86400)  # At least 1 day


def calculate_engagement_rate(views: int, likes: int, comments: int) -> float:
    """
    Calculate engagement rate

    Args:
        views: View count
        likes: Like count
        comments: Comment count

    Returns:
        Engagement rate as percentage
    """
    if views == 0:
        return 0.0

    return ((likes + comments) / views) * 100


def calculate_velocity(views: int, days_old: float) -> float:
    """
    Calculate views per day

    Args:
        views: View count
        days_old: Days since published

    Returns:
        Views per day
    """
    return views / max(1, days_old)


def calculate_like_ratio(likes: int, views: int) -> float:
    """
    Calculate like ratio

    Args:
        likes: Like count
        views: View count

    Returns:
        Like ratio (0-1)
    """
    if views == 0:
        return 0.0

    # Estimate dislikes as 5% of views (conservative)
    estimated_dislikes = views * 0.05
    total_reactions = likes + estimated_dislikes

    if total_reactions == 0:
        return 0.0

    return likes / total_reactions


def calculate_viral_score(video: Dict) -> float:
    """
    Calculate viral score (0-100)

    Formula:
    - Engagement rate (40%)
    - Velocity/views per day (30%)
    - Like ratio (20%)
    - Total views (10%)
    - Duration bonus (1.2x for 30-90s videos)
    - Recency bonus (1.3x for videos < 30 days old)

    Args:
        video: Video data dict

    Returns:
        Viral score (0-100)
    """
    views = video['view_count']
    likes = video['like_count']
    comments = video['comment_count']
    duration = video['duration_seconds']
    days_old = calculate_days_since_published(video['published_at'])

    # Calculate components
    engagement_rate = calculate_engagement_rate(views, likes, comments)
    velocity = calculate_velocity(views, days_old)
    like_ratio = calculate_like_ratio(likes, views)

    # Weighted score
    raw_score = (
        (engagement_rate * ENGAGEMENT_WEIGHT) +
        (math.log10(max(1, velocity)) * VELOCITY_WEIGHT) +
        (like_ratio * LIKE_RATIO_WEIGHT) +
        (math.log10(max(1, views)) * VIEWS_WEIGHT)
    )

    # Duration bonus
    duration_bonus = 1.0
    if SHORT_CONTENT_MIN <= duration <= SHORT_CONTENT_MAX:
        duration_bonus = SHORT_CONTENT_BONUS

    # Recency bonus
    recency_bonus = 1.0
    if days_old <= RECENT_DAYS_THRESHOLD:
        recency_bonus = RECENCY_BONUS

    # Final score
    final_score = raw_score * duration_bonus * recency_bonus

    return min(100.0, max(0.0, final_score))


def categorize_video(video: Dict, viral_score: float) -> str:
    """
    Categorize video based on metrics

    Args:
        video: Video data dict
        viral_score: Calculated viral score

    Returns:
        Category string
    """
    views = video['view_count']
    days_old = calculate_days_since_published(video['published_at'])
    velocity = calculate_velocity(views, days_old)

    # Viral: High score
    if viral_score >= VIRAL_SCORE_THRESHOLD:
        return CATEGORY_VIRAL

    # Growing: High velocity
    if velocity >= GROWING_VELOCITY_THRESHOLD:
        return CATEGORY_GROWING

    # Underrated: Low views but good engagement
    engagement_rate = calculate_engagement_rate(
        views, video['like_count'], video['comment_count']
    )
    if views < UNDERRATED_VIEW_THRESHOLD and engagement_rate > 3.0:
        return CATEGORY_UNDERRATED

    # Declining: Old video with low velocity
    if days_old > 60 and velocity < 1000:
        return CATEGORY_DECLINING

    return CATEGORY_GROWING  # Default


def score_videos(videos: List[Dict]) -> List[Dict]:
    """
    Score and categorize all videos

    Args:
        videos: List of video dicts

    Returns:
        List of videos with scores and categories
    """
    scored_videos = []

    for video in videos:
        viral_score = calculate_viral_score(video)
        category = categorize_video(video, viral_score)
        days_old = calculate_days_since_published(video['published_at'])

        scored_video = {
            **video,
            'viral_score': viral_score,
            'category': category,
            'days_old': days_old,
            'velocity': calculate_velocity(video['view_count'], days_old),
            'engagement_rate': calculate_engagement_rate(
                video['view_count'],
                video['like_count'],
                video['comment_count']
            )
        }

        scored_videos.append(scored_video)

    return scored_videos


def sort_videos(videos: List[Dict], sort_by: str = 'viral-score') -> List[Dict]:
    """
    Sort videos by specified metric

    Args:
        videos: List of scored videos
        sort_by: Sort metric (viral-score, engagement, views, velocity)

    Returns:
        Sorted list of videos
    """
    if sort_by == 'viral-score':
        return sorted(videos, key=lambda v: v['viral_score'], reverse=True)
    elif sort_by == 'engagement':
        return sorted(videos, key=lambda v: v['engagement_rate'], reverse=True)
    elif sort_by == 'views':
        return sorted(videos, key=lambda v: v['view_count'], reverse=True)
    elif sort_by == 'velocity':
        return sorted(videos, key=lambda v: v['velocity'], reverse=True)
    else:
        return videos
