"""
Message grouping utilities for the Arcanum application.

Provides:
- grouping of message results by their originating chat,
- resolving chat_ref_id into slug and name for UI rendering,
- structures for template-friendly output.
"""

import logging
from typing import List, Dict

from app.services.chats_service import get_chats_by_ids

logger = logging.getLogger(__name__)


def group_messages_by_chat(messages: List[dict]) -> Dict[str, dict]:
    """
    Group messages by their associated chat slug.

    Workflow:
    - Extract unique chat_ref_id values.
    - Resolve these IDs to chat slugs and names.
    - Group messages by slug for frontend rendering.

    :param messages: List of message dicts with 'chat_ref_id' keys.
    :type messages: List[dict]
    :return: Dictionary of grouped messages by chat slug.
    :rtype: Dict[str, dict]
    """
    chat_ref_ids = {
        msg.get("chat_ref_id") for msg in messages if msg.get("chat_ref_id")
    }
    if not chat_ref_ids:
        logger.debug(
            "[MESSAGES|GROUP] No chat_ref_id found in messages. "
            "Skipping grouping."
        )
        return {}

    chats = get_chats_by_ids(chat_ref_ids)
    chat_ref_id_map = {
        chat.id: {"slug": chat.slug, "name": chat.name}
        for chat in chats
    }

    logger.debug(
        "[MESSAGES|GROUP] Resolved %d chat(s) from %d chat_ref_id(s).",
        len(chat_ref_id_map), len(chat_ref_ids)
    )

    grouped = {}
    for msg in messages:
        chat_info = chat_ref_id_map.get(msg.get("chat_ref_id"))
        if not chat_info:
            continue

        slug = chat_info["slug"]
        if slug not in grouped:
            grouped[slug] = {
                "chat_name": chat_info["name"],
                "messages": []
            }
        grouped[slug]["messages"].append(msg)

    logger.debug(
        "[MESSAGES|GROUP] Grouped %d message(s) into %d chat(s).",
        len(messages), len(grouped)
    )

    return grouped
