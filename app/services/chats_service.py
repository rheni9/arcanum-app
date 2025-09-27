"""
Chat service operations for the Arcanum application.

Provides business logic for managing chats:
- Listing chats with aggregate message statistics.
- Retrieving chats by slug or primary key.
- Creating chats with uniqueness validation.
- Updating chats with duplicate checks.
- Deleting chats (messages are removed via ON DELETE CASCADE).
- Checking for slug existence.
- Retrieving global statistics.

This class is backend-agnostic. The actual DAO implementation
(PostgreSQL or SQLite) is selected via the ChatDAO facade.
"""

import logging

from app.models.chat import Chat
from app.services.dao.chats.chats_dao_base import BaseChatDAO
from app.errors import (
    DuplicateSlugError,
    DuplicateChatIDError,
    ChatNotFoundError,
)

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service layer for chat operations.

    Encapsulates business rules (uniqueness/existence checks) and
    delegates persistence to the selected DAO backend.
    """

    def __init__(self, dao: BaseChatDAO) -> None:
        """
        Initialize the service with a given DAO.

        :param dao: Concrete chat DAO (Postgres or SQLite).
        """
        self.dao = dao

    # ---------- Read operations ----------

    def get_chats(self, sort_by: str, order: str) -> list[dict]:
        """
        Retrieve all chats with message counts and last-message timestamps.

        :param sort_by: Field to sort by.
        :param order: Sort direction (``'asc'`` or ``'desc'``).
        :return: List of chat dicts with aggregated statistics.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug(
            "[CHATS|SERVICE] Retrieving chats sorted by '%s' (%s).",
            sort_by,
            order,
        )
        try:
            return self.dao.fetch_chats(sort_by, order)
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to retrieve chats: %s", exc)
            raise

    def get_chat_by_slug(self, slug: str) -> Chat | None:
        """
        Retrieve a chat by its slug.

        :param slug: Chat slug.
        :return: Chat instance if found, otherwise ``None``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug("[CHATS|SERVICE] Retrieving chat by slug '%s'.", slug)
        try:
            row = self.dao.fetch_chat_by_slug(slug)
            if not row:
                logger.warning(
                    "[CHATS|SERVICE] No chat found with slug '%s'.",
                    slug,
                )
                return None
            return Chat.from_row(row)
        except self.dao.db_error_class as exc:
            logger.error(
                "[CHATS|SERVICE] Failed to retrieve chat by slug: %s",
                exc,
            )
            raise

    def get_chat_by_id(self, pk: int) -> Chat | None:
        """
        Retrieve a chat by its primary key.

        :param pk: Chat primary key.
        :return: Chat instance if found, otherwise ``None``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug("[CHATS|SERVICE] Retrieving chat ID=%d.", pk)
        try:
            row = self.dao.fetch_chat_by_id(pk)
            if not row:
                logger.warning(
                    "[CHATS|SERVICE] No chat found with ID=%d.",
                    pk
                )
                return None
            return Chat.from_row(row)
        except self.dao.db_error_class as exc:
            logger.error(
                "[CHATS|SERVICE] Failed to retrieve chat by ID: %s",
                exc,
            )
            raise

    # ---------- Write operations ----------

    def insert_chat(self, chat: Chat) -> int:
        """
        Insert a new chat.

        Performs pre-insert uniqueness checks for slug and Telegram
        chat ID (if present).

        :param chat: Chat instance to insert.
        :return: Primary key ID of the inserted chat.
        :raises DuplicateSlugError: If the slug already exists.
        :raises DuplicateChatIDError: If the Telegram chat ID already exists.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            if self.dao.check_slug_exists(chat.slug):
                logger.warning(
                    "[CHATS|SERVICE] Slug '%s' already exists.",
                    chat.slug,
                )
                raise DuplicateSlugError(slug=chat.slug)
            if (
                chat.chat_id is not None
                and self.dao.check_chat_id_exists(chat.chat_id)
            ):
                logger.warning(
                    "[CHATS|SERVICE] Telegram chat ID '%d' already exists.",
                    chat.chat_id,
                )
                raise DuplicateChatIDError(chat_id=chat.chat_id)
            pk = self.dao.insert_chat_record(chat)
            logger.info(
                "[CHATS|SERVICE] Chat '%s' created (slug='%s', ID=%d).",
                chat.name,
                chat.slug,
                pk,
            )
            return pk
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to insert chat: %s", exc)
            raise

    def update_chat(self, chat: Chat) -> None:
        """
        Update an existing chat.

        Validates presence of the Chat primary key (``id``), checks for
        duplicate slug and Telegram chat ID (if provided), and performs
        the update via the DAO layer.

        :param chat: Chat instance with updated values (must have ``id``).
        :raises ValueError: If the Chat primary key is missing.
        :raises DuplicateSlugError: If the slug already exists.
        :raises DuplicateChatIDError: If the Telegram chat ID already exists.
        :raises ChatNotFoundError: If the chat does not exist.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        if not chat.id:
            logger.error("[CHATS|SERVICE] Update failed: no primary key.")
            raise ValueError("Chat ID (primary key) is required for update.")

        try:
            if self.dao.check_slug_exists(chat.slug, exclude_id=chat.id):
                logger.warning(
                    "[CHATS|SERVICE] Slug update rejected (duplicate): %s.",
                    chat.slug,
                )
                raise DuplicateSlugError(slug=chat.slug)
            if (
                chat.chat_id is not None
                and self.dao.check_chat_id_exists(
                    chat.chat_id,
                    exclude_id=chat.id,
                )
            ):
                logger.warning(
                    "[CHATS|SERVICE] Telegram chat ID update rejected "
                    "(duplicate): %s.",
                    chat.chat_id,
                )
                raise DuplicateChatIDError(chat_id=chat.chat_id)

            self.dao.update_chat_record(chat)
            logger.info(
                "[CHATS|SERVICE] Chat '%s' updated (slug='%s', ID=%d).",
                chat.name,
                chat.slug,
                chat.id,
            )
        except ChatNotFoundError:
            logger.warning(
                "[CHATS|SERVICE] Chat with ID=%d not found.",
                chat.id,
            )
            raise
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to update chat: %s", exc)
            raise

    def delete_chat_and_messages(self, slug: str) -> None:
        """
        Delete a chat and its related messages by slug.

        If the chat does not exist, the method logs a warning and returns
        without raising an exception.

        :param slug: Chat slug.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            chat = self.get_chat_by_slug(slug)
            if not chat:
                logger.warning(
                    "[CHATS|SERVICE] Delete skipped: no chat for slug '%s'.",
                    slug,
                )
                raise ChatNotFoundError(chat_id=slug)

            # Messages deleted via ON DELETE CASCADE constraint.
            self.dao.delete_chat_record(chat.id)
            logger.info(
                "[CHATS|SERVICE] Chat '%s' deleted (ID=%d, slug='%s').",
                chat.name,
                chat.id,
                chat.slug,
            )
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to delete chat: %s", exc)
            raise

    # ---------- Convenience wrappers ----------

    def slug_exists(self, slug: str) -> bool:
        """
        Check whether the given chat slug exists.

        :param slug: Chat slug.
        :return: ``True`` if the slug exists, otherwise ``False``.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        try:
            result = self.dao.check_slug_exists(slug)
            logger.debug("[CHATS|SERVICE] Slug '%s' exists: %s", slug, result)
            return result
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to check slug: %s", exc)
            raise

    def get_global_stats(self) -> dict:
        """
        Retrieve global chat statistics.

        Includes total chats, total messages, media count,
        and the most recent message attributes.

        :return: Aggregated statistics.
        :raises dao.db_error_class: If the DAO operation fails.
        """
        logger.debug("[CHATS|SERVICE] Retrieving global chat statistics.")
        try:
            return self.dao.fetch_global_chat_stats()
        except self.dao.db_error_class as exc:
            logger.error("[CHATS|SERVICE] Failed to retrieve stats: %s", exc)
            raise
