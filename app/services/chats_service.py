"""
Chat service operations for the Arcanum application.

Provides logic for retrieving, creating, updating, and deleting chats.
Handles input validation, duplicate checks, and delegates all low-level
operations to the DAO layer.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError

from app.models.chat import Chat
from app.services.dao.chats_dao import (
    fetch_chats, fetch_chat_by_slug,
    fetch_chat_by_id, insert_chat_record,
    update_chat_record, delete_chat_record,
    check_slug_exists, check_chat_id_exists,
    fetch_global_chat_stats
)
from app.errors import (
    DuplicateChatIDError, DuplicateSlugError, ChatNotFoundError
)

logger = logging.getLogger(__name__)


def get_chats(sort_by: str, order: str) -> list[dict]:
    """
    Return all chats with message counts and last message timestamps.

    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of chat row dictionaries with aggregate statistics.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug(
        "[CHATS|SERVICE] Retrieving chats sorted by '%s' (%s).",
        sort_by, order
    )
    try:
        return fetch_chats(sort_by, order)
    except SQLAlchemyError as exc:
        logger.error("[CHATS|SERVICE] Failed to retrieve chats: %s", exc)
        raise


def get_chat_by_slug(slug: str) -> Chat | None:
    """
    Retrieve a chat by its slug.

    :param slug: Chat slug.
    :return: Chat instance if found, otherwise None.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chat by slug '%s'.", slug)
    try:
        chat = fetch_chat_by_slug(slug)
        if not chat:
            logger.warning(
                "[CHATS|SERVICE] No chat found with slug '%s'.",
                slug
            )
            return None
        return chat
    except SQLAlchemyError as exc:
        logger.error(
            "[CHATS|SERVICE] Failed to retrieve chat by slug: %s",
            exc
        )
        raise


def get_chat_by_id(pk: int) -> Chat | None:
    """
    Retrieve a chat by its primary key ID.

    :param pk: Chat ID.
    :return: Chat instance if found, otherwise None.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving chat ID=%d.", pk)
    try:
        chat = fetch_chat_by_id(pk)
        if not chat:
            logger.warning("[CHATS|SERVICE] No chat found with ID=%d.", pk)
            return None
        return chat
    except SQLAlchemyError as exc:
        logger.error("[CHATS|SERVICE] Failed to retrieve chat by ID: %s", exc)
        raise


def insert_chat(chat: Chat) -> int:
    """
    Insert a new chat into the database.

    Checks for uniqueness of slug and Telegram chat ID (if present).
    Delegates insertion to the DAO layer.

    :param chat: Chat instance to insert.
    :return: Primary key ID of the inserted chat.
    :raises DuplicateSlugError: If the slug already exists.
    :raises DuplicateChatIDError: If the Telegram chat ID already exists.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    try:
        if check_slug_exists(chat.slug):
            logger.warning(
                "[CHATS|SERVICE] Slug '%s' already exists.",
                chat.slug
            )
            raise DuplicateSlugError(slug=chat.slug)
        if chat.chat_id is not None and check_chat_id_exists(chat.chat_id):
            logger.warning(
                "[CHATS|SERVICE] Telegram chat ID '%d' already exists.",
                chat.chat_id
            )
            raise DuplicateChatIDError(chat_id=chat.chat_id)
        pk = insert_chat_record(chat)
        logger.info(
            "[CHATS|SERVICE] Chat '%s' created (slug='%s', ID=%d).",
            chat.name, chat.slug, pk
        )
        return pk
    except SQLAlchemyError as exc:
        logger.error("[CHATS|SERVICE] Failed to insert chat: %s", exc)
        raise


def update_chat(chat: Chat) -> None:
    """
    Update an existing chat.

    Verifies ID presence, checks for conflicts in slug or Telegram ID,
    and performs update via the DAO layer.

    :param chat: Chat instance with updated values (must have ID).
    :raises ValueError: If the ID is missing before update.
    :raises DuplicateSlugError: If the slug already exists.
    :raises DuplicateChatIDError: If the Telegram chat ID already exists.
    :raises ChatNotFoundError: If the chat to update does not exist.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    if not chat.id:
        logger.error("[CHATS|SERVICE] Update failed: no ID.")
        raise ValueError("Chat ID is required for update.")
    try:
        if check_slug_exists(chat.slug, exclude_id=chat.id):
            logger.warning(
                "[CHATS|SERVICE] Slug update rejected (duplicate): %s.",
                chat.slug
            )
            raise DuplicateSlugError(slug=chat.slug)
        if (
            chat.chat_id is not None
            and check_chat_id_exists(chat.chat_id, exclude_id=chat.id)
        ):
            logger.warning(
                "[CHATS|SERVICE] Telegram chat ID update rejected "
                "(duplicate): %s.",
                chat.chat_id
            )
            raise DuplicateChatIDError(chat_id=chat.chat_id)

        update_chat_record(chat)
        logger.info(
            "[CHATS|SERVICE] Chat '%s' updated (slug='%s', ID=%d).",
            chat.name, chat.slug, chat.id
        )
    except ChatNotFoundError:
        logger.warning("[CHATS|SERVICE] Chat with ID=%d not found.", chat.id)
        raise
    except SQLAlchemyError as exc:
        logger.error("[CHATS|SERVICE] Failed to update chat: %s", exc)
        raise


def delete_chat_and_messages(slug: str) -> None:
    """
    Delete a chat and its related messages by slug.

    :param slug: Chat slug.
    :raises ChatNotFoundError: If the chat to delete does not exist.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    try:
        chat = get_chat_by_slug(slug)
        if not chat:
            logger.warning(
                "[CHATS|SERVICE] Delete skipped: no chat for slug '%s'.",
                slug
            )
            return

        # Messages deleted via ON DELETE CASCADE constraint.
        delete_chat_record(chat.id)
        logger.info(
            "[CHATS|SERVICE] Chat '%s' deleted (ID=%d, slug='%s').",
            chat.name, chat.id, chat.slug
        )
    except SQLAlchemyError as exc:
        logger.error("[CHATS|SERVICE] Failed to delete chat: %s", exc)
        raise


def slug_exists(slug: str) -> bool:
    """
    Check whether the given chat slug exists.

    :param slug: Chat slug.
    :return: True if the slug exists, otherwise False.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    try:
        result = check_slug_exists(slug)
        logger.debug("[CHATS|SERVICE] Slug '%s' exists: %s", slug, result)
        return result
    except SQLAlchemyError as exc:
        logger.error(
            "[CHATS|SERVICE] Failed to check slug existence: %s",
            exc
        )
        raise


def get_global_stats() -> dict:
    """
    Retrieve global chat statistics.

    :return: Dictionary with total chats, messages, media count, etc.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug("[CHATS|SERVICE] Retrieving global chat statistics.")
    try:
        return fetch_global_chat_stats()
    except SQLAlchemyError as exc:
        logger.error(
            "[CHATS|SERVICE] Failed to retrieve global stats: %s",
            exc
        )
        raise
