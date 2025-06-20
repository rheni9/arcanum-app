"""
Chat service operations for the Arcanum application.

Provides logic for retrieving, creating, updating, and deleting chats.
Handles input validation, duplicate checks, and delegates all low-level
operations to the DAO layer.
"""

import logging
from sqlite3 import IntegrityError

from app.models.chat import Chat
from app.services.dao.chats_dao import (
    fetch_chats, fetch_chat_by_slug,
    fetch_chat_by_id, insert_chat_record,
    update_chat_record, delete_chat_record,
    check_slug_exists, check_chat_id_exists,
    fetch_global_chat_stats
)

logger = logging.getLogger(__name__)


def get_chats(sort_by: str, order: str) -> list[dict]:
    """
    Return all chats with message counts and last message timestamps.

    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of chat row dictionaries with aggregate statistics.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chats sorted by '%s' (%s).",
                 sort_by, order)
    return fetch_chats(sort_by, order)


def get_chat_by_slug(slug: str) -> Chat | None:
    """
    Retrieve a chat by its slug.

    :param slug: Chat slug.
    :return: Chat instance if found, otherwise None.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
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
    :return: Chat instance if found, otherwise None.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chat ID=%d.", pk)
    chat = fetch_chat_by_id(pk)
    if not chat:
        logger.warning("[CHATS|SERVICE] No chat found with ID=%d.", pk)
        return None
    return chat


def insert_chat(chat: Chat) -> int:
    """
    Insert a new chat into the database.

    Checks for uniqueness of slug and Telegram chat ID (if present).
    Delegates insertion to the DAO layer.

    :param chat: Chat instance to insert.
    :return: Primary key ID of the inserted chat.
    :raises IntegrityError: If the slug or Telegram ID already exists.
    :raises DatabaseError: If the DAO operation fails.
    """
    if check_slug_exists(chat.slug):
        logger.warning("[CHATS|SERVICE] Slug '%s' already exists.", chat.slug)
        raise IntegrityError(f"Chat with slug '{chat.slug}' already exists.")
    if chat.chat_id is not None and check_chat_id_exists(chat.chat_id):
        logger.warning(
            "[CHATS|SERVICE] Telegram chat ID '%d' already exists.",
            chat.chat_id
        )
        raise IntegrityError(
            f"Chat with Telegram ID '{chat.chat_id}' already exists."
        )
    pk = insert_chat_record(chat)
    logger.info("[CHATS|SERVICE] Chat '%s' created (slug='%s', ID=%d).",
                chat.name, chat.slug, pk)
    return pk


def update_chat(chat: Chat) -> None:
    """
    Update an existing chat.

    Verifies ID presence, checks for conflicts in slug or Telegram ID,
    and performs update via the DAO layer.

    :param chat: Chat instance with updated values (must have ID).
    :raises ValueError: If the ID is missing or the chat does not exist.
    :raises IntegrityError: If the slug or Telegram ID already exists.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
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
    if (chat.chat_id is not None and existing.chat_id != chat.chat_id
            and check_chat_id_exists(chat.chat_id)):
        logger.warning(
            "[CHATS|SERVICE] Telegram chat ID update rejected: %s -> %s "
            "(duplicate).",
            existing.chat_id, chat.chat_id
        )
        raise IntegrityError("Chat with this Telegram ID already exists.")

    update_chat_record(chat)
    logger.info("[CHATS|SERVICE] Chat '%s' updated (slug='%s', ID=%d).",
                chat.name, chat.slug, chat.id)


def delete_chat_and_messages(slug: str) -> None:
    """
    Delete a chat and its related messages by slug.

    :param slug: Chat slug.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        logger.warning(
            "[CHATS|SERVICE] Delete skipped: no chat for slug '%s'.", slug
        )
        return

    # Messages deleted via ON DELETE CASCADE constraint.
    delete_chat_record(chat.id)
    logger.info("[CHATS|SERVICE] Chat '%s' deleted (ID=%d, slug='%s').",
                chat.name, chat.id, chat.slug)


def slug_exists(slug: str) -> bool:
    """
    Check whether the given chat slug exists.

    :param slug: Chat slug.
    :return: True if the slug exists, otherwise False.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
    """
    result = check_slug_exists(slug)
    logger.debug("[CHATS|SERVICE] Slug '%s' exists: %s", slug, result)
    return result


def get_global_stats() -> dict:
    """
    Retrieve global chat statistics.

    :return: Dictionary with total chats, messages, media count, etc.
    :raises sqlite3.DatabaseError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving global chat statistics.")
    return fetch_global_chat_stats()
