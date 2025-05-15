"""
Slug utilities for chat names normalization in Arcanum.

Provides:
- Transliteration of Cyrillic chat names.
- Safe slug generation from chat titles.
- Collision-resistant slug resolution.
"""

import re
import unicodedata
import hashlib
import logging

from app.services.chats_service import slug_exists

logger = logging.getLogger(__name__)

# Cyrillic to Latin transliteration mapping
CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "h", "ґ": "g", "д": "d", "е": "e",
    "є": "ie", "ж": "zh", "з": "z", "и": "y", "і": "i", "ї": "i", "й": "y",
    "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ь": "", "ю": "iu", "я": "ia"
}


def transliterate(text: str) -> str:
    """
    Transliterate a Cyrillic string into Latin characters.

    :param text: Input string (chat name).
    :type text: str
    :return: Transliterated lowercase string.
    :rtype: str
    """
    return ''.join(CYR_TO_LAT.get(char, char) for char in text.lower())


def slugify(text: str, max_words: int = 3) -> str:
    """
    Generate a safe slug from a Telegram chat name.

    Applies transliteration, normalization, and character filtering.
    Limits slug to first N words. Uses hash fallback for edge cases.

    :param text: Input string to convert.
    :type text: str
    :param max_words: Maximum number of words in the slug.
    :type max_words: int
    :return: Resulting slug string (e.g., "chat_name" or "chat_ab12ef").
    :rtype: str
    """
    original_text = str(text) if text is not None else ""
    text = unicodedata.normalize("NFKD", original_text)
    text = transliterate(text)
    text = re.sub(r"[^a-z0-9 ]", "", text)
    words = text.strip().split()

    slug = "_".join(words[:max_words])

    if not slug or not any(char.isalnum() for char in slug):
        hash_part = hashlib.sha1(original_text.encode("utf-8")).hexdigest()[:6]
        logger.warning(
            "[SLUG|FALLBACK] Generated hash slug for empty result "
            "from input '%s'.", original_text
        )
        return f"chat_{hash_part}"

    return slug


def generate_unique_slug(
    base_slug: str, seed: str, max_tries: int = 10
) -> str:
    """
    Ensure a slug is unique among existing chats.

    Appends short hash suffix to base_slug in case of collisions.

    :param base_slug: Primary slug candidate.
    :type base_slug: str
    :param seed: Seed for hash generation (e.g., name + link).
    :type seed: str
    :param max_tries: Maximum attempts to resolve collision.
    :type max_tries: int
    :return: Unique slug string.
    :rtype: str
    :raises ValueError: If unique slug cannot be generated.
    """
    for i in range(max_tries):
        suffix = hashlib.sha1((seed + str(i)).encode()).hexdigest()[:6]
        new_slug = f"{base_slug}_{suffix}"
        if not slug_exists(new_slug):
            if i > 0:
                logger.info(
                    "[SLUG|RESOLVE] Collision detected, resolved to '%s'.",
                    new_slug
                )
            return new_slug

    logger.error(
        "[SLUG|FAIL] Failed to generate unique slug after %d attempts.",
        max_tries
    )
    raise ValueError("Could not generate unique slug after collision retries.")
