"""
Centralized logging for chat-related events in the Arcanum application.

Handles logging of chat listing, viewing, filtering, and actions
such as creation, updating, and deletion. Ensures consistent log
formatting across routes.
"""

import logging

from app.models.filters import MessageFilters

logger = logging.getLogger(__name__)


def log_chat_list(
    chats_count: int,
    sort_by: str,
    order: str,
    is_ajax: bool
) -> None:
    """
    Log the rendering of the chat list.

    :param chats_count: Number of chats displayed.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :param is_ajax: Whether the request was triggered via AJAX.
    """
    if is_ajax:
        logger.info(
            "[CHATS|LIST|AJAX] %s chat(s) loaded | sorted by %s (%s).",
            chats_count, sort_by, order
        )
    else:
        logger.info(
            "[CHATS|LIST] %s chat(s) displayed | sorted by %s (%s).",
            chats_count, sort_by, order
        )


def log_chat_view(
    slug: str,
    filters: MessageFilters,
    count: int,
    is_ajax: bool
) -> None:
    """
    Log a filtered or sorted chat view.

    :param slug: Chat slug identifier.
    :param filters: Applied message filters.
    :param count: Number of messages retrieved.
    :param is_ajax: Whether the request was triggered via AJAX.
    """
    if filters.action:
        payload: dict[str, str | None] = filters.to_dict()
        if is_ajax:
            logger.info(
                "[CHATS|VIEW|AJAX] Chat '%s' table loaded | %s message(s) "
                "| filters: %s.",
                slug, count, payload
            )
        else:
            logger.info(
                "[CHATS|VIEW] Chat '%s' displayed | %s message(s) "
                "| filters: %s.",
                slug, count, payload
            )
    elif filters.has_active():
        logger.warning(
            "[CHATS|VIEW] Invalid filter input — no search performed."
        )


def log_chat_action(action: str, chat_slug: str) -> None:
    """
    Log a chat-level action.

    :param action: Action type ('create', 'update', 'delete').
    :param chat_slug: Chat slug identifier.
    """
    logger.info("[CHATS|%s] Chat '%s'.", action.upper(), chat_slug)
