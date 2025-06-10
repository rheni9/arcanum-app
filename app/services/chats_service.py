"""
Chat service operations for the Arcanum application.

Provides logic for chat retrieval, creation, updating,
and deletion. Performs validation, handles conflicts,
and delegates low-level operations to DAO.
"""

import logging
from sqlite3 import IntegrityError

from app.models.chat import Chat
from app.services.dao.chats_dao import (
    fetch_chats, fetch_chat_by_slug,
    fetch_chat_by_id, insert_chat_record,
    update_chat_record, delete_chat_record,
    check_slug_exists, fetch_global_chat_stats
)

logger = logging.getLogger(__name__)


def get_chats(sort_by: str, order: str) -> list[dict]:
    """
    Return all chats with message counts and last message timestamps.

    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of chat dicts with extra statistics.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chats sorted by '%s' (%s).",
                 sort_by, order)
    return fetch_chats(sort_by, order)


def get_chat_by_slug(slug: str) -> Chat | None:
    """
    Retrieve a chat by its slug.

    :param slug: Chat slug.
    :return: Chat instance if found, else None.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chat by slug '%s'.", slug)
    chat = fetch_chat_by_slug(slug)
    if not chat:
        logger.warning("[CHATS|SERVICE] No chat found with slug '%s'.", slug)
        return None
    return chat


def get_chat_by_id(pk: int) -> Chat | None:
    """
    Retrieve a chat by its primary key ID.

    :param pk: Chat ID.
    :return: Chat instance if found, else None.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chat ID=%d.", pk)
    chat = fetch_chat_by_id(pk)
    if not chat:
        logger.warning("[CHATS|SERVICE] No chat found with ID=%d.", pk)
        return None
    return chat


def insert_chat(chat: Chat) -> int:
    """
    Insert a new chat.

    :param chat: Chat instance.
    :return: New chat ID.
    :raises sqlite3.IntegrityError: If slug is not unique.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    if check_slug_exists(chat.slug):
        logger.warning("[CHATS|SERVICE] Slug '%s' already exists.", chat.slug)
        raise IntegrityError(f"Chat with slug '{chat.slug}' already exists.")
    pk = insert_chat_record(chat)
    logger.info("[CHATS|SERVICE] Chat '%s' created (slug='%s', ID=%d).",
                chat.name, chat.slug, pk)
    return pk


def update_chat(chat: Chat) -> None:
    """
    Update an existing chat.

    :param chat: Chat instance with updated data (must have ID).
    :raises ValueError: If ID missing.
    :raises sqlite3.IntegrityError: If slug is not unique.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    if not chat.id:
        logger.error("[CHATS|SERVICE] Update failed: no ID.")
        raise ValueError("Chat ID is required for update.")
    existing = fetch_chat_by_id(chat.id)
    if not existing:
        logger.warning("[CHATS|SERVICE] Chat with ID=%d not found.", chat.id)
        raise ValueError("Chat not found for update.")
    if existing.slug != chat.slug and check_slug_exists(chat.slug):
        logger.warning(
            "[CHATS|SERVICE] Slug update rejected (%s -> %s): duplicate.",
            existing.slug, chat.slug
        )
        raise IntegrityError("Chat with this slug already exists.")

    update_chat_record(chat)
    logger.info("[CHATS|SERVICE] Chat '%s' updated (ID=%d, slug='%s').",
                chat.name, chat.id, chat.slug)


def delete_chat_and_messages(slug: str) -> None:
    """
    Delete a chat and related messages by slug.

    :param slug: Chat slug.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        logger.warning(
            "[CHATS|SERVICE] Delete skipped: no chat for slug '%s'.", slug
        )
        return
    delete_chat_record(chat.id)
    logger.info("[CHATS|SERVICE] Chat '%s' deleted (ID=%d, slug='%s').",
                chat.name, chat.id, chat.slug)


def slug_exists(slug: str) -> bool:
    """
    Check if a chat with the given slug exists.

    :param slug: Chat slug.
    :return: True if exists, else False.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    result = check_slug_exists(slug)
    logger.debug("[CHATS|SERVICE] Slug '%s' exists: %s", slug, result)
    return result


def get_global_stats() -> dict:
    """
    Retrieve global chat statistics for the dashboard.

    :return: Dictionary with total chats, messages, media count, etc.
    :raises sqlite3.DatabaseError: If DAO fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving global chat statistics.")
    return fetch_global_chat_stats()
