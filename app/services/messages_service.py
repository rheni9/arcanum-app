"""
Message service operations for the Arcanum application.

Provides business logic for managing messages:
- Listing messages for a chat with ordering.
- Retrieving messages by primary key.
- Navigating to previous/next message in a chat.
- Creating messages with uniqueness validation.
- Updating messages with duplicate checks.
- Deleting messages by ID.
- Existence check and per-chat count.

This class is backend-agnostic. The actual DAO implementation
(PostgreSQL or SQLite) is selected elsewhere and injected here.
"""

import logging
from datetime import datetime

from app.models.message import Message
from app.services.dao.messages.messages_dao_base import BaseMessageDAO
from app.errors import DuplicateMessageError, MessageNotFoundError

logger = logging.getLogger(__name__)


class MessageService:
    """
    Service layer for message operations.

    Encapsulates business rules (uniqueness/existence checks) and
    delegates persistence to the selected DAO backend.
    """

    def __init__(self, dao: BaseMessageDAO) -> None:
        """
        Initialize the service with a given DAO.

        :param dao: Concrete message DAO (Postgres or SQLite).
        """
        self.dao = dao

    # ---------- Read operations ----------

    def get_messages_by_chat_slug(
        self,
        chat_slug: str,
        sort_by: str,
        order: str,
    ) -> list[dict]:
        """
        Retrieve all messages for a chat with sorting.

        :param chat_slug: Chat slug.
        :param sort_by: Field to sort by (e.g., ``timestamp`` or ``msg_id``).
        :param order: Sort direction (``'asc'`` or ``'desc'``).
        :return: List of message row dictionaries.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug(
            "[MESSAGES|SERVICE] Retrieving messages for chat '%s' "
            "sorted by '%s' (%s).",
            chat_slug,
            sort_by,
            order,
        )
        try:
            return self.dao.fetch_messages_by_chat(chat_slug, sort_by, order)
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to retrieve messages: %s",
                exc,
            )
            raise

    def get_message_by_id(self, pk: int) -> Message | None:
        """
        Retrieve a message by its primary key.

        :param pk: Message primary key.
        :return: Message instance if found, otherwise ``None``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug("[MESSAGES|SERVICE] Retrieving message ID=%d.", pk)
        try:
            row = self.dao.fetch_message_by_id(pk)
            if not row:
                logger.warning(
                    "[MESSAGES|SERVICE] No message found with ID=%d.",
                    pk,
                )
                return None
            return Message.from_row(row)
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to retrieve message by ID: %s",
                exc,
            )
            raise

    def get_previous_message(
        self,
        chat_ref_id: int,
        current_ts: datetime,
    ) -> Message | None:
        """
        Retrieve the message sent before the given timestamp in the same chat.

        :param chat_ref_id: ID of the chat (foreign key).
        :param current_ts: Timestamp of the current message (exclusive).
        :return: Previous message as ``Message`` if found, otherwise ``None``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug(
            "[MESSAGES|SERVICE] Fetching previous message before %s "
            "in chat_ref_id=%d.",
            current_ts,
            chat_ref_id,
        )
        try:
            row = self.dao.fetch_previous_message(chat_ref_id, current_ts)
            return Message.from_row(row) if row else None
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to fetch previous message: %s",
                exc,
            )
            raise

    def get_next_message(
        self,
        chat_ref_id: int,
        current_ts: datetime,
    ) -> Message | None:
        """
        Retrieve the message sent after the given timestamp in the same chat.

        :param chat_ref_id: ID of the chat (foreign key).
        :param current_ts: Timestamp of the current message (exclusive).
        :return: Next message as ``Message`` if found, otherwise ``None``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug(
            "[MESSAGES|SERVICE] Fetching next message after %s "
            "in chat_ref_id=%d.",
            current_ts,
            chat_ref_id,
        )
        try:
            row = self.dao.fetch_next_message(chat_ref_id, current_ts)
            return Message.from_row(row) if row else None
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to fetch next message: %s",
                exc,
            )
            raise

    # ---------- Write operations ----------

    def insert_message(self, message: Message) -> int:
        """
        Insert a new message.

        Performs pre-insert uniqueness check for the (chat_ref_id, msg_id)
        pair when ``msg_id`` is provided.

        :param message: Message instance to insert.
        :return: Primary key ID of the inserted message.
        :raises DuplicateMessageError: If ``msg_id`` already exists
                                       within the chat.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            if message.msg_id is not None:
                if self.dao.check_message_exists(
                    message.chat_ref_id,
                    message.msg_id,
                ):
                    logger.warning(
                        "[MESSAGES|SERVICE] msg_id=%d already exists in "
                        "chat_ref_id=%d.",
                        message.msg_id,
                        message.chat_ref_id,
                    )
                    raise DuplicateMessageError(
                        chat_ref_id=message.chat_ref_id,
                        msg_id=message.msg_id,
                    )
            pk = self.dao.insert_message_record(message)
            logger.info(
                "[MESSAGES|SERVICE] Message created (ID=%d, chat_ref_id=%d).",
                pk,
                message.chat_ref_id,
            )
            return pk
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to insert message: %s",
                exc,
            )
            raise

    def update_message(self, message: Message) -> None:
        """
        Update an existing message.

        Validates presence of the message primary key (``id``), checks for
        duplicate (chat_ref_id, msg_id) when updating ``msg_id``, and
        performs the update via the DAO layer.

        :param message: Message instance with updated values
                        (must have ``id``).
        :raises ValueError: If the message primary key is missing.
        :raises DuplicateMessageError: If ``msg_id`` already exists
                                       within the chat.
        :raises MessageNotFoundError: If the message does not exist.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        if not message.id:
            logger.error("[MESSAGES|SERVICE] Update failed: no primary key.")
            raise ValueError(
                "Message ID (primary key) is required for update.",
            )

        try:
            if message.msg_id is not None:
                if self.dao.check_message_exists(
                    message.chat_ref_id,
                    message.msg_id,
                    exclude_id=message.id,
                ):
                    logger.warning(
                        "[MESSAGES|SERVICE] msg_id update rejected "
                        "(duplicate in chat_ref_id=%d): %d.",
                        message.chat_ref_id,
                        message.msg_id,
                    )
                    raise DuplicateMessageError(
                        chat_ref_id=message.chat_ref_id,
                        msg_id=message.msg_id,
                    )

            self.dao.update_message_record(message)
            logger.info(
                "[MESSAGES|SERVICE] Message updated (ID=%d, chat_ref_id=%d).",
                message.id,
                message.chat_ref_id,
            )
        except MessageNotFoundError:
            logger.warning(
                "[MESSAGES|SERVICE] Message with ID=%d not found.",
                message.id,
            )
            raise
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to update message: %s",
                exc,
            )
            raise

    def delete_message_by_id(self, pk: int) -> None:
        """
        Delete a message by its primary key.

        :param pk: Message primary key.
        :raises MessageNotFoundError: If the message does not exist.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            self.dao.delete_message_record(pk)
            logger.info("[MESSAGES|SERVICE] Message deleted (ID=%d).", pk)
        except MessageNotFoundError:
            logger.warning(
                "[MESSAGES|SERVICE] Message with ID=%d not found.",
                pk,
            )
            raise
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to delete message: %s",
                exc,
            )
            raise

    # ---------- Convenience wrappers ----------

    def message_exists(self, chat_ref_id: int, msg_id: int) -> bool:
        """
        Check whether a given (chat_ref_id, msg_id) pair already exists.

        This pair uniquely identifies a Telegram message ID within
        a single chat.

        :param chat_ref_id: Chat primary key (foreign key).
        :param msg_id: Telegram message ID (unique per chat).
        :return: ``True`` if such a message ID exists in the chat,
                 otherwise ``False``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            result = self.dao.check_message_exists(chat_ref_id, msg_id)
            logger.debug(
                "[MESSAGES|SERVICE] msg_id=%d exists in chat_ref_id=%d: %s",
                msg_id,
                chat_ref_id,
                result,
            )
            return result
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to check message existence: %s",
                exc,
            )
            raise

    def count_messages_in_chat(self, chat_ref_id: int) -> int:
        """
        Count the number of messages linked to a specific chat.

        :param chat_ref_id: ID of the related chat (foreign key).
        :return: Total number of messages in the chat.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            count = self.dao.count_messages_for_chat(chat_ref_id)
            logger.debug(
                "[MESSAGES|SERVICE] Counted total %d message(s) in "
                "chat_ref_id=%d.",
                count,
                chat_ref_id,
            )
            return count
        except self.dao.db_error_class as exc:
            logger.error(
                "[MESSAGES|SERVICE] Failed to count messages: %s",
                exc,
            )
            raise
