"""
Provides centralized logging functions for chat-related events.

Handles logging for listing, viewing, creating, updating, and deleting chats.
Ensures unified log formatting across chat routes and services.
"""

import logging

logger = logging.getLogger("app.chats")


def log_list_view(chats_count: int, sort_by: str, order: str) -> None:
    """
    Log the chat list page rendering.

    :param chats_count: Number of chats displayed.
    :type chats_count: int
    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort order ('asc' or 'desc').
    :type order: str
    """
    logger.info(
        "[CHATS|LIST] %s chat(s) displayed | sorted by %s %s.",
        chats_count,
        sort_by,
        order
    )


def log_list_ajax(chats_count: int, sort_by: str, order: str) -> None:
    """
    Log the AJAX chat table rendering.

    :param chats_count: Number of chats displayed.
    :type chats_count: int
    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort order ('asc' or 'desc').
    :type order: str
    """
    logger.info(
        "[CHATS|LIST|AJAX] %s chat(s) loaded | sorted by %s %s.",
        chats_count,
        sort_by,
        order
    )


def log_chat_view(chat_slug: str, messages_count: int, filters: dict) -> None:
    """
    Log the chat view rendering.

    :param chat_slug: Chat slug identifier.
    :type chat_slug: str
    :param messages_count: Number of messages retrieved.
    :type messages_count: int
    :param filters: Applied filters.
    :type filters: dict
    """
    logger.info(
        "[CHATS|VIEW] Chat '%s' displayed | %s message(s) | filters: %s.",
        chat_slug,
        messages_count,
        filters
    )


def log_chat_view_ajax(
    chat_slug: str,
    messages_count: int,
    filters: dict
) -> None:
    """
    Log the AJAX message table rendering for a chat.

    :param chat_slug: Chat slug identifier.
    :type chat_slug: str
    :param messages_count: Number of messages retrieved.
    :type messages_count: int
    :param filters: Applied filters.
    :type filters: dict
    """
    logger.info(
        "[CHATS|VIEW|AJAX] Chat '%s' table loaded | %s message(s) "
        "| filters: %s.",
        chat_slug,
        messages_count,
        filters
    )


def log_chat_action(action: str, chat_slug: str) -> None:
    """
    Log a chat action in a unified style.

    :param action: Action string (CREATE, UPDATE, DELETE).
    :param chat_slug: Chat slug.
    """
    logger.info("[CHATS|%s] Chat '%s'.", action.upper(), chat_slug)
