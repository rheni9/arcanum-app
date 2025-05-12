"""
Message utilities for grouping and organizing messages.

Includes:
- grouping messages by chat for search result display.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def group_messages_by_chat(messages: List[dict]) -> dict[str, List[dict]]:
    """
    Group a flat list of messages by chat slug.

    Used to organize search results or chat views where messages
    need to be grouped by their originating chat.

    :param messages: List of message dictionaries.
    :type messages: List[dict]
    :return: Dictionary mapping chat slugs to lists of messages.
    :rtype: dict[str, List[dict]]
    """
    grouped = {}
    for msg in messages:
        slug = msg.get("chat_slug")
        if not slug:
            continue
        grouped.setdefault(slug, []).append(msg)

    logger.debug(
        "[GROUP] Grouped %d message(s) into %d chat(s).",
        len(messages), len(grouped)
    )
    return grouped
