"""
Caption and hashtag generator
"""
import re
from typing import List, Optional
from .config import TIKTOK_MAX_CAPTION_LENGTH, DEFAULT_HASHTAGS
from .logger import get_logger

logger = get_logger()


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text
    Simple implementation: most common words excluding stopwords
    """
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
        'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just'
    }

    # Clean and tokenize
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()

    # Filter stopwords and short words
    words = [w for w in words if w not in stopwords and len(w) > 3]

    # Count frequency
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    # Return top keywords
    return [word for word, freq in sorted_words[:max_keywords]]


def generate_hashtags(keywords: List[str], custom_hashtags: Optional[str] = None) -> List[str]:
    """
    Generate hashtags from keywords and custom hashtags

    Args:
        keywords: List of keywords
        custom_hashtags: Custom hashtags string (space or comma separated)

    Returns:
        List of hashtags (with # prefix)
    """
    hashtags = []

    # Add custom hashtags first
    if custom_hashtags:
        # Split by space or comma
        custom = re.split(r'[,\s]+', custom_hashtags.strip())
        for tag in custom:
            tag = tag.strip()
            if tag:
                # Add # if not present
                if not tag.startswith('#'):
                    tag = f'#{tag}'
                # Remove any invalid characters
                tag = re.sub(r'[^\w#]', '', tag)
                if len(tag) > 1:  # Must have at least one character after #
                    hashtags.append(tag)

    # Add keyword-based hashtags
    for keyword in keywords:
        tag = f'#{keyword.lower()}'
        if tag not in hashtags:
            hashtags.append(tag)

    # Add default hashtags if not already present
    for default_tag in DEFAULT_HASHTAGS:
        if default_tag not in hashtags:
            hashtags.append(default_tag)

    return hashtags


def generate_caption(
    title: str,
    description: Optional[str] = None,
    custom_caption: Optional[str] = None,
    custom_hashtags: Optional[str] = None
) -> str:
    """
    Generate TikTok caption

    Args:
        title: Video title
        description: Video description
        custom_caption: Custom caption text
        custom_hashtags: Custom hashtags

    Returns:
        Complete caption with hashtags
    """
    logger.info("📝 Generating caption...")

    # Use custom caption if provided
    if custom_caption:
        caption_text = custom_caption
        keywords = extract_keywords(title + ' ' + (description or ''))
    else:
        # Auto-generate caption from title
        keywords = extract_keywords(title + ' ' + (description or ''))

        # Create engaging hook
        hooks = [
            "🔥 You need to see this!",
            "💯 This is incredible!",
            "⚡ Wait for it...",
            "🎯 Must watch!",
            "✨ Amazing!",
            "🚀 Mind-blowing!",
        ]

        # Pick hook based on title length (deterministic)
        hook = hooks[len(title) % len(hooks)]

        # Build caption
        caption_text = f"{hook}\n\n{title[:100]}"

        # Add emojis based on keywords
        emoji_map = {
            'food': '🍕', 'cooking': '👨‍🍳', 'recipe': '🍳',
            'fitness': '💪', 'workout': '🏋️', 'gym': '🏃',
            'tech': '💻', 'coding': '👨‍💻', 'ai': '🤖',
            'funny': '😂', 'comedy': '🤣', 'meme': '😆',
            'music': '🎵', 'dance': '💃', 'song': '🎶',
            'travel': '✈️', 'adventure': '🌍', 'nature': '🌿',
            'art': '🎨', 'drawing': '✏️', 'design': '🖌️',
            'game': '🎮', 'gaming': '🕹️', 'esports': '🏆',
        }

        emojis = []
        for keyword in keywords:
            if keyword in emoji_map and emoji_map[keyword] not in emojis:
                emojis.append(emoji_map[keyword])

        if emojis:
            caption_text += ' ' + ' '.join(emojis[:3])

    # Generate hashtags
    hashtags = generate_hashtags(keywords, custom_hashtags)

    # Combine caption and hashtags
    full_caption = caption_text + '\n\n' + ' '.join(hashtags)

    # Truncate if too long
    if len(full_caption) > TIKTOK_MAX_CAPTION_LENGTH:
        # Try to fit as many hashtags as possible
        available_length = TIKTOK_MAX_CAPTION_LENGTH - len(caption_text) - 2  # -2 for \n\n
        hashtag_text = ' '.join(hashtags)

        if len(hashtag_text) > available_length:
            # Keep only hashtags that fit
            fitted_hashtags = []
            current_length = 0
            for tag in hashtags:
                if current_length + len(tag) + 1 <= available_length:
                    fitted_hashtags.append(tag)
                    current_length += len(tag) + 1
                else:
                    break
            hashtag_text = ' '.join(fitted_hashtags)

        full_caption = caption_text[:TIKTOK_MAX_CAPTION_LENGTH - len(hashtag_text) - 2] + '\n\n' + hashtag_text

    logger.info(f"✅ Caption generated ({len(full_caption)} chars)")
    logger.debug(f"Caption preview: {full_caption[:100]}...")

    return full_caption


def validate_caption(caption: str) -> bool:
    """
    Validate caption meets TikTok requirements

    Args:
        caption: Caption text

    Returns:
        True if valid, False otherwise
    """
    if not caption:
        return False

    if len(caption) > TIKTOK_MAX_CAPTION_LENGTH:
        logger.error(f"Caption too long: {len(caption)} > {TIKTOK_MAX_CAPTION_LENGTH}")
        return False

    return True
