"""
Chat utilities for constructing chat objects.

This module provides a helper for preparing chat dictionaries
for database operations.
"""

import logging

from app.models.models import Chat

logger = logging.getLogger(__name__)


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
