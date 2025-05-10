"""
Message filtering and grouping utilities for chat and search views.

Includes:
- a dataclass for encapsulating message filter parameters,
- logic to resolve appropriate query function,
- detection of active filters,
- grouping messages by chat for search result display.
"""

from dataclasses import dataclass
from typing import Optional, List

from app.services.messages_service import (
    get_messages_by_chat,
    search_messages_by_text,
    filter_messages,
)


@dataclass
class MessageFilters:
    """
    Data container for message filter parameters.

    Used to encapsulate query string filters such as text search and
    date-based filtering when resolving messages for a chat.
    """
    action: Optional[str] = None
    query: Optional[str] = None
    date_mode: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def resolve_messages(
    slug: str,
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> List[dict]:
    """
    Resolve the appropriate message retrieval strategy based on filters.

    This function selects whether to run a full-text search, a date-based
    filter query, or a default fetch of all messages in the chat.

    :param slug: Chat slug to fetch messages for.
    :type slug: str
    :param filters: MessageFilters object with active user filters.
    :type filters: MessageFilters
    :param sort_by: Field to sort by (e.g., 'timestamp', 'msg_id').
    :type sort_by: str
    :param order: Sort order ('asc' or 'desc').
    :type order: str
    :return: A list of message dictionaries matching the filter.
    :rtype: List[dict]
    """
    if filters.action == "search" and filters.query:
        return search_messages_by_text(
            filters.query, chat_slug=slug, sort_by=sort_by, order=order
        )

    if filters.action == "filter" and filters.start_date:
        return filter_messages(
            mode=filters.date_mode,
            start=filters.start_date,
            end=filters.end_date,
            chat_slug=slug,
            sort_by=sort_by,
            order=order,
        )

    return get_messages_by_chat(slug, sort_by=sort_by, order=order)


def group_messages_by_chat(messages: List[dict]) -> dict[str, List[dict]]:
    """
    Group a list of messages by their associated chat slug.

    This utility is used to organize flat message lists into a structure
    where each key is a chat slug and the value is a list of messages
    belonging to that chat.

    :param messages: List of message dictionaries.
    :type messages: List[dict]
    :return: Dictionary grouping messages by chat slug.
    :rtype: dict[str, List[dict]]
    """
    grouped = {}
    for msg in messages:
        slug = msg.get("chat_slug")
        if not slug:
            continue
        grouped.setdefault(slug, []).append(msg)
    return grouped
