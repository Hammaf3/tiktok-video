"""
Configuration for yt_analyzer
"""
from pathlib import Path

# Directories
BASE_DIR = Path(__file__).parent.parent
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Create directories
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# YouTube API Configuration
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_MAX_RESULTS_PER_PAGE = 50

# Analysis defaults
DEFAULT_LIMIT = 25
DEFAULT_SORT = "viral-score"

# Viral score weights
ENGAGEMENT_WEIGHT = 40
VELOCITY_WEIGHT = 30
LIKE_RATIO_WEIGHT = 20
VIEWS_WEIGHT = 10

# Duration bonuses
SHORT_CONTENT_MIN = 30  # seconds
SHORT_CONTENT_MAX = 90  # seconds
SHORT_CONTENT_BONUS = 1.2

# Recency bonus
RECENT_DAYS_THRESHOLD = 30
RECENCY_BONUS = 1.3

# Video categories
CATEGORY_VIRAL = "🔥 Viral"
CATEGORY_GROWING = "📈 Growing"
CATEGORY_UNDERRATED = "💎 Underrated"
CATEGORY_DECLINING = "📉 Declining"

# Thresholds for categorization
VIRAL_SCORE_THRESHOLD = 75
GROWING_VELOCITY_THRESHOLD = 10000  # views per day
UNDERRATED_VIEW_THRESHOLD = 100000
