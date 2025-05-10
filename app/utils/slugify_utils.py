"""
Slug utilities: transliterate Cyrillic text and generate safe, unique slugs.

Includes tools for:
- converting text to ASCII-friendly slugs,
- generating unique slugs using hashes,
- transliterating Cyrillic symbols to Latin.
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

    :param text: Input string to transliterate.
    :type text: str
    :return: Transliterated lowercase Latin string.
    :rtype: str
    """
    return ''.join(CYR_TO_LAT.get(char, char) for char in text.lower())


def slugify(text: str, max_words: int = 3) -> str:
    """
    Convert a string into a slug suitable for filenames or identifiers.

    This includes transliteration, normalization, stripping special characters,
    word limiting, and a hash-based fallback if needed.

    :param text: Input string to convert.
    :type text: str
    :param max_words: Maximum number of words to include in the slug.
    :type max_words: int
    :return: Generated slug (e.g., "chat_name" or "chat_ab12ef").
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
            "Slugify fallback: using hash for input '%s'", original_text
        )
        return f"chat_{hash_part}"

    return slug


def generate_unique_slug(
    base_slug: str, seed: str, max_tries: int = 10
) -> str:
    """
    Generate a unique slug by appending a short hash to the base slug.

    :param base_slug: Base part of the slug.
    :type base_slug: str
    :param seed: Seed value for hash generation (e.g., name + link).
    :type seed: str
    :param max_tries: Maximum attempts to find an unused slug.
    :type max_tries: int
    :return: Unique slug string.
    :rtype: str
    :raises ValueError: If unique slug cannot be generated within max_tries.
    """
    for i in range(max_tries):
        suffix = hashlib.sha1((seed + str(i)).encode()).hexdigest()[:6]
        new_slug = f"{base_slug}_{suffix}"
        if not slug_exists(new_slug):
            if i > 0:
                logger.info("Slug collision: resolved with '%s'", new_slug)
            return new_slug
    logger.error("Failed to generate unique slug after %d attempts", max_tries)
    raise ValueError("Could not generate unique slug")
