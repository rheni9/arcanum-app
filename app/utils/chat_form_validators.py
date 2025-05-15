"""
Chat form validation utilities for the Arcanum application.

Provides field-level validation for chat forms.
"""

import logging
import re
from datetime import datetime
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def validate_name(name: str) -> str:
    """
    Validate chat name field.

    :param name: Input name.
    :type name: str
    :returns: Normalized name.
    :rtype: str
    :raises ValueError: If validation fails.
    """
    name = (name or "").strip()

    if not name:
        logger.warning("[FORM|VALIDATION] Chat name is required.")
        raise ValueError("Chat name is required.")

    logger.debug("[FORM|VALIDATION] Validated name: '%s'.", name)
    return name.strip()


def validate_chat_id(chat_id: Optional[str]) -> Optional[int]:
    """
    Validate chat ID field (optional).

    :param chat_id: Input chat ID.
    :type chat_id: str
    :returns: Chat ID as integer, or None if empty.
    :rtype: Optional[int]
    :raises ValueError: If validation fails.
    """
    chat_id = (chat_id or "").strip()

    if not chat_id:
        logger.debug("[FORM|VALIDATION] Chat ID not provided (optional).")
        return None

    if not re.match(r"^\d+$", chat_id):
        logger.warning("[FORM|VALIDATION] Invalid chat ID format: '%s'.",
                       chat_id)
        raise ValueError("Chat ID must be a positive integer.")

    logger.debug("[FORM|VALIDATION] Validated chat ID: %s.", chat_id)
    return int(chat_id)


def validate_link(link: Optional[str]) -> str:
    """
    Validate chat link field (optional).

    Accepts links starting with 'https://' or 'http://'.

    :param link: Input link.
    :type link: Optional[str]
    :returns: Normalized link.
    :rtype: str
    :raises ValueError: If validation fails.
    """
    link = (link or "").strip()

    if not link:
        logger.debug("[FORM|VALIDATION] Link not provided (optional).")
        return ""

    if not (link.startswith("https://") or link.startswith("http://")):
        logger.warning(
            "[FORM|VALIDATION] Chat link must start with "
            "'https://' or 'http://'."
        )
        raise ValueError("Chat link must start with 'https://' or 'http://'.")

    logger.debug("[FORM|VALIDATION] Validated link: '%s'.", link)
    return link


def is_valid_join_date(joined: str) -> bool:
    """
    Check if join date is valid (not in the future).

    :param joined: Join date as string.
    :type joined: str
    :returns: True if valid, False otherwise.
    :rtype: bool
    """
    try:
        dt = datetime.fromisoformat(joined.replace("Z", "+00:00"))
    except ValueError:
        logger.warning(
            "[FORM|VALIDATION] Invalid join date format: '%s'.", joined
        )
        return False

    if dt.date() > datetime.utcnow().date():
        logger.warning(
            "[FORM|VALIDATION] Join date cannot be in the future: '%s'.",
            joined
        )
        return False

    return True


def validate_join_date(joined: Optional[str]) -> str:
    """
    Validate join date field (optional).

    :param joined: Input join date.
    :type joined: Optional[str]
    :returns: Normalized join date.
    :rtype: str
    :raises ValueError: If validation fails.
    """
    joined = (joined or "").strip()

    if not joined:
        logger.debug("[FORM|VALIDATION] Join date not provided (optional).")
        return ""

    if not is_valid_join_date(joined):
        raise ValueError("Join date cannot be in the future.")

    logger.debug("[FORM|VALIDATION] Validated join date: '%s'.", joined)
    return joined


def validate_chat_form(data: dict) -> Tuple[dict, dict]:
    """
    Validate entire chat form and collect errors.

    :param data: Raw form input.
    :type data: dict
    :returns: (fields, errors) - cleaned values and error messages.
    :rtype: Tuple[dict, dict]
    """
    fields = {}
    errors = {}

    try:
        fields["name"] = validate_name(data.get("name", ""))
    except ValueError as e:
        errors["name"] = str(e)

    try:
        fields["chat_id"] = validate_chat_id(data.get("chat_id", ""))
    except ValueError as e:
        errors["chat_id"] = str(e)

    try:
        fields["link"] = validate_link(data.get("link", ""))
    except ValueError as e:
        errors["link"] = str(e)

    try:
        fields["joined"] = validate_join_date(data.get("joined", ""))
    except ValueError as e:
        errors["joined"] = str(e)

    return fields, errors
