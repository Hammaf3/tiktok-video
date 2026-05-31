"""
Niche presets for keyword-based searches
"""

NICHE_PRESETS = {
    "cooking": [
        "quick recipe",
        "cooking hack",
        "food tutorial",
        "easy meal",
        "5 minute recipe",
        "cooking tips",
        "kitchen hack"
    ],
    "fitness": [
        "workout",
        "gym motivation",
        "weight loss",
        "home exercise",
        "fitness tips",
        "muscle building",
        "cardio workout"
    ],
    "tech": [
        "AI tutorial",
        "coding tips",
        "tech review",
        "software hack",
        "programming tutorial",
        "tech news",
        "gadget review"
    ],
    "comedy": [
        "funny moments",
        "prank",
        "fails compilation",
        "memes",
        "comedy skit",
        "funny videos",
        "hilarious moments"
    ],
    "motivation": [
        "success mindset",
        "morning routine",
        "hustle",
        "entrepreneur",
        "motivational speech",
        "self improvement",
        "productivity tips"
    ],
    "satisfying": [
        "satisfying",
        "oddly satisfying",
        "ASMR",
        "relaxing",
        "satisfying videos",
        "oddly satisfying videos",
        "most satisfying"
    ],
    "gaming": [
        "gaming highlights",
        "gameplay",
        "game review",
        "gaming tips",
        "best moments",
        "gaming montage",
        "pro gameplay"
    ],
    "beauty": [
        "makeup tutorial",
        "beauty tips",
        "skincare routine",
        "makeup hack",
        "beauty review",
        "makeup transformation",
        "skincare tips"
    ],
    "travel": [
        "travel vlog",
        "travel guide",
        "travel tips",
        "adventure",
        "travel destinations",
        "travel hack",
        "bucket list"
    ],
    "diy": [
        "DIY project",
        "DIY tutorial",
        "craft ideas",
        "DIY hack",
        "handmade",
        "DIY home decor",
        "easy DIY"
    ]
}


def get_niche_keywords(niche: str) -> list:
    """
    Get keywords for a niche

    Args:
        niche: Niche name

    Returns:
        List of keywords
    """
    return NICHE_PRESETS.get(niche.lower(), [])


def get_available_niches() -> list:
    """Get list of available niche names"""
    return list(NICHE_PRESETS.keys())


def is_valid_niche(niche: str) -> bool:
    """Check if niche is valid"""
    return niche.lower() in NICHE_PRESETS
