"""
yt_analyzer - YouTube Viral Content Analyzer
"""

__version__ = '1.0.0'
__author__ = 'yt_analyzer'

from .fetcher import YouTubeFetcher
from .scorer import score_videos, sort_videos
from .reporter import generate_markdown_report
from .niche_presets import get_niche_keywords, get_available_niches

__all__ = [
    'YouTubeFetcher',
    'score_videos',
    'sort_videos',
    'generate_markdown_report',
    'get_niche_keywords',
    'get_available_niches',
]
