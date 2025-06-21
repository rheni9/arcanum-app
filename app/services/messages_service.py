"""
Message service operations for the Arcanum application.

Provides logic for retrieving, creating, updating, and deleting
messages. Handles input validation, conflict checks, and delegates
low-level operations to the DAO layer.
"""

import logging

from app.models.message import Message
from app.services.dao.messages_dao import (
    fetch_message_by_id, fetch_messages_by_chat,
    insert_message_record, update_message_record,
    delete_message_record, check_message_exists,
    count_messages_for_chat
)
from app.errors import DuplicateMessageError, MessageNotFoundError

logger = logging.getLogger(__name__)


def get_message_by_id(pk: int) -> Message | None:
    """
    Retrieve a message by its primary key ID.

    :param pk: Message ID.
    :return: Message instance if found, otherwise None.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug("[MESSAGES|SERVICE] Retrieving message ID=%d.", pk)
    message = fetch_message_by_id(pk)
    if not message:
        logger.warning("[MESSAGES|SERVICE] No message found with ID=%d.", pk)
        return None
    return message


def get_messages_by_chat_slug(
    chat_slug: str,
    sort_by: str,
    order: str
) -> list[dict]:
    """
    Retrieve all messages for a chat with sorting.

    :param chat_slug: Chat slug.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of message row dictionaries.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    logger.debug(
        "[MESSAGES|SERVICE] Retrieving messages for chat '%s' "
        "sorted by '%s' (%s).", chat_slug, sort_by, order
    )
    return fetch_messages_by_chat(chat_slug, sort_by, order)


def insert_message(message: Message) -> int:
    """
    Insert a new message.

    :param message: Message instance.
    :return: New message ID.
    :raises DuplicateMessageError: If msg_id already exists within the chat.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    if message.msg_id is not None:
        if check_message_exists(message.chat_ref_id, message.msg_id):
            logger.warning(
                "[MESSAGES|SERVICE] msg_id=%s already exists "
                "in chat_ref_id=%d.",
                str(message.msg_id), message.chat_ref_id
            )
            raise DuplicateMessageError("Duplicate msg_id in this chat.")

    pk = insert_message_record(message)
    logger.info(
        "[MESSAGES|SERVICE] Message created (ID=%d, chat_ref_id=%d).",
        pk, message.chat_ref_id
    )
    return pk


def update_message(message: Message) -> None:
    """
    Update an existing message.

    :param message: Message instance with updated data (must have ID).
    :raises ValueError: If ID is missing.
    :raises MessageNotFoundError: If the message to update does not exist.
    :raises DuplicateMessageError: If msg_id already exists within the chat.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    if not message.id:
        logger.error("[MESSAGES|SERVICE] Update failed: no ID.")
        raise ValueError("Message ID is required for update.")
    if message.msg_id is not None:
        existing = fetch_message_by_id(message.id)
        if not existing:
            logger.warning(
                "[MESSAGES|SERVICE] Message with ID=%d not found.", message.id
            )
            raise MessageNotFoundError("Message not found for update.")
        if (
            existing.msg_id != message.msg_id and
            check_message_exists(message.chat_ref_id, message.msg_id)
        ):
            logger.warning(
                "[MESSAGES|SERVICE] msg_id update rejected (%s -> %s): "
                "duplicate in chat_ref_id=%d.",
                str(existing.msg_id), str(message.msg_id),
                message.chat_ref_id
            )
            raise DuplicateMessageError(
                "Message with this msg_id already exists in the chat.",
            )
    else:
        logger.debug(
            "[MESSAGES|SERVICE] msg_id is None — skipping conflict check."
        )
    update_message_record(message)
    logger.info("[MESSAGES|SERVICE] Message updated (ID=%d).", message.id)


def delete_message(pk: int) -> None:
    """
    Delete a message by its primary key ID.

    :param pk: Message ID.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    delete_message_record(pk)
    logger.info("[MESSAGES|SERVICE] Message deleted (ID=%d).", pk)


def message_exists(chat_ref_id: int, msg_id: int) -> bool:
    """
    Check if a message with the given Telegram ID exists within the chat.

    :param chat_ref_id: ID of the chat (foreign key in messages table).
    :param msg_id: Telegram message ID (unique within the given chat).
    :return: True if such a message exists within the chat, otherwise False.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    result = check_message_exists(chat_ref_id, msg_id)
    logger.debug(
        "[MESSAGES|SERVICE] msg_id=%s exists in chat_ref_id=%d: %s",
        str(msg_id), chat_ref_id, result
    )
    return result


def count_messages_in_chat(chat_ref_id: int) -> int:
    """
    Count the number of messages linked to a specific chat.

    :param chat_ref_id: ID of the related chat (foreign key).
    :return: Total number of messages in the chat.
    :raises SQLAlchemyError: If the DAO operation fails.
    """
    count = count_messages_for_chat(chat_ref_id)
    logger.debug(
        "[MESSAGES|SERVICE] Counted total %d message(s) in chat_ref_id=%d.",
        count, chat_ref_id
    )
    return count
