"""
Chat form utilities: validation and object construction.

This module provides helpers for validating input from chat forms
and preparing chat dictionaries for database operations.
"""

import logging
from typing import Tuple
from datetime import date

from app.models.models import Chat
from app.utils.time_utils import parse_date
from app.utils.form_utils import is_valid_url

logger = logging.getLogger(__name__)


def validate_chat_form(data: dict) -> Tuple[dict, dict]:
    """
    Validate and clean specific fields from the chat form.

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
    result["name"] = name or None

    chat_id = (data.get("chat_id") or "").strip()
    if chat_id and not chat_id.isdigit():
        errors["chat_id"] = "Chat ID must contain only digits."
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
        logger.warning("Rejected future join date: %s", joined)

    return result, errors


def build_chat_object(data: dict, slug: str) -> dict:
    """
    Construct a standardized chat dictionary for storage or updates.

    :param data: Validated and cleaned form data.
    :type data: dict
    :param slug: Final chat slug to assign.
    :type slug: str
    :return: Chat dictionary for persistence.
    :rtype: dict
    """
    return Chat(
        slug=slug,
        name=data.get("name"),
        chat_id=data.get("chat_id"),
        link=data.get("link"),
        type=data.get("type"),
        joined=data.get("joined"),
        is_active="is_active" in data,
        is_member="is_member" in data,
        notes=data.get("notes"),
    )
