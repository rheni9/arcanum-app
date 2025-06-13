"""
Centralized logging for chat-related events in the Arcanum application.

Handles logging of chat listing, viewing, filtering, and actions such as
creation, updating, and deletion. Ensures consistent log formatting across
routes and services.
"""

import logging

from app.models.filters import MessageFilters

logger = logging.getLogger("app.chats")


def log_chat_list(
    chats_count: int,
    sort_by: str,
    order: str,
    is_ajax: bool
) -> None:
    """
    Log the rendering of the chat list (full page or AJAX).

    :param chats_count: Number of chats displayed.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :param is_ajax: Whether the request was triggered via AJAX.
    """
    if is_ajax:
        _log_chat_list_ajax(chats_count, sort_by, order)
    else:
        _log_chat_list_full(chats_count, sort_by, order)


def log_chat_view(
    slug: str,
    filters: MessageFilters,
    count: int,
    is_ajax: bool
) -> None:
    """
    Log a filtered or sorted chat view (full page or AJAX).

    :param slug: Chat slug identifier.
    :param filters: Applied message filters.
    :param count: Number of messages retrieved.
    :param is_ajax: Whether the request was triggered via AJAX.
    """
    if filters.action:
        payload = filters.to_dict()
        if is_ajax:
            _log_chat_view_ajax(slug, count, payload)
        else:
            _log_chat_view_full(slug, count, payload)
    elif filters.has_active():
        logger.warning(
            "[CHATS|VIEW] Invalid filter input — no search performed."
        )


def log_chat_action(action: str, chat_slug: str) -> None:
    """
    Log a chat-level action (create, update, delete).

    :param action: Action type ('create', 'update', 'delete').
    :param chat_slug: Chat slug identifier.
    """
    logger.info("[CHATS|%s] Chat '%s'.", action.upper(), chat_slug)


def _log_chat_list_full(chats_count: int, sort_by: str, order: str) -> None:
    """
    Log the rendering of the full chat list page.

    :param chats_count: Number of chats displayed.
    :param sort_by: Field to sort by.
    :param order: Sort order ('asc' or 'desc').
    """
    logger.info(
        "[CHATS|LIST] %s chat(s) displayed | sorted by %s (%s).",
        chats_count, sort_by, order
    )


def _log_chat_list_ajax(chats_count: int, sort_by: str, order: str) -> None:
    """
    Log the rendering of the chat list via AJAX.

    :param chats_count: Number of chats displayed.
    :param sort_by: Field to sort by.
    :param order: Sort order ('asc' or 'desc').
    """
    logger.info(
        "[CHATS|LIST|AJAX] %s chat(s) loaded | sorted by %s (%s).",
        chats_count, sort_by, order
    )


def _log_chat_view_full(
    chat_slug: str,
    messages_count: int,
    payload: dict[str, str | None]
) -> None:
    """
    Log the rendering of a filtered chat view.

    :param chat_slug: Chat slug identifier.
    :param messages_count: Number of messages retrieved.
    :param payload: Dictionary of applied filters.
    """
    logger.info(
        "[CHATS|VIEW] Chat '%s' displayed | %s message(s) | filters: %s.",
        chat_slug, messages_count, payload
    )


def _log_chat_view_ajax(
    chat_slug: str,
    messages_count: int,
    payload: dict[str, str | None]
) -> None:
    """
    Log the rendering of a filtered chat table via AJAX.

    :param chat_slug: Chat slug identifier.
    :param messages_count: Number of messages retrieved.
    :param filters: Dictionary of applied filters.
    """
    logger.info(
        "[CHATS|VIEW|AJAX] Chat '%s' table loaded | %s message(s) "
        "| filters: %s.",
        chat_slug, messages_count, payload
    )
