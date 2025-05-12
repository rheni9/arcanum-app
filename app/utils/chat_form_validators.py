"""
Chat form validation utilities for the Arcanum application.

Provides helpers for validating individual chat form fields, including:
- chat name,
- chat ID,
- chat link (URL),
- join date (cannot be in the future).

Centralizes validation logic with structured logging for diagnostics.
"""

import logging
from datetime import date
from urllib.parse import urlparse
from typing import Tuple

from app.utils.time_utils import parse_date

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """
    Validate a URL to ensure it uses a valid HTTP(S) scheme.

    Supports only http and https protocols.
    Logs a warning if validation fails due to invalid format.

    :param url: Input URL string.
    :type url: str
    :return: True if URL has a valid scheme and network location,
             False otherwise.
    :rtype: bool
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except (TypeError, AttributeError) as e:
        logger.warning(
            "[FORM-VALIDATION] Invalid link value: '%s': %s", url, e
        )
        return False


def validate_chat_form(data: dict) -> Tuple[dict, dict]:
    """
    Validate and clean specific fields from the chat form.

    Checks name presence, chat_id format, link URL validity, and join date.

    :param data: Cleaned form input.
    :type data: dict
    :return: Tuple of (validated fields, error messages).
    :rtype: Tuple[dict, dict]
    """
    errors = {}
    result = {}

    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Chat name is required."
        logger.warning("[FORM-VALIDATION] Chat name is missing.")
    result["name"] = name or None

    chat_id = (data.get("chat_id") or "").strip()
    if chat_id and not chat_id.isdigit():
        errors["chat_id"] = "Chat ID must contain only digits."
        logger.warning(
            "[FORM-VALIDATION] Invalid chat_id value: '%s'.", chat_id
        )
    result["chat_id"] = chat_id or None

    link = (data.get("link") or "").strip()
    if link and not is_valid_url(link):
        errors["link"] = (
            "Please enter a valid URL (starting with http:// or https://)."
        )
    result["link"] = link or None

    joined_raw = data.get("joined")
    joined = parse_date(joined_raw) if joined_raw else None
    result["joined"] = joined

    if joined and joined > date.today().isoformat():
        errors["joined"] = "Join date cannot be in the future."
        logger.warning(
            "[FORM-VALIDATION] Join date is in the future: '%s'.", joined
        )

    if errors:
        logger.info("[FORM-VALIDATION] Validation errors: %s", errors)

    return result, errors
