"""
Message utilities for the Arcanum application.

Groups messages by chat slug and prepares structured containers
for UI display. Used primarily in global search results.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def group_messages_by_chat(
    messages: list[dict]
) -> dict[str, dict[str, Any]]:
    """
    Group message dicts by chat slug.

    Each group contains the chat's name and list of corresponding messages.
    Skips messages without a valid 'chat_slug'.

    :param messages: List of message dicts with 'chat_slug' and 'chat_name'.
    :return: Mapping {slug: {"chat_name": ..., "messages": [...]}}.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for msg in messages:
        slug = msg.get("chat_slug")

        if not slug:
            logger.warning(
                "[GROUP|UTIL] Skipping message without chat_slug: id=%s",
                msg.get("id")
            )
            continue

        name = msg.get("chat_name") or slug

        if slug not in grouped:
            grouped[slug] = {
                "chat_name": name,
                "messages": [],
            }
        grouped[slug]["messages"].append(msg)

    logger.debug("[GROUP|UTIL] Grouped %d chat(s) from %d message(s)",
                 len(grouped), len(messages))
    return grouped
