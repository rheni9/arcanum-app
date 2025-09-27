"""
Base Data Access Object (DAO) for chat-related database operations
in the Arcanum application.

Defines business logic helpers for chat operations and delegates
backend-specific execution to concrete subclasses (SQLite, PostgreSQL).

SQL queries:
    - Multi-line / complex statements (INSERT/UPDATE/stats) live in the
      co-located ``sql/`` directory and are loaded via ``load_sql()``.
    - Simple one-liners (lookup, existence checks, delete-by-id) stay
      inline for readability.

All methods rely on subclasses for connection handling, SQL execution,
and integrity-error mapping (unique violations, etc.).
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.models.chat import Chat
from app.utils.sql_utils import OrderConfig, build_order_clause
from app.errors import ChatNotFoundError

logger = logging.getLogger(__name__)

# Directory with backend-agnostic SQL files.
SQL_DIR = Path(__file__).resolve().parent / "sql"


def load_sql(filename: str) -> str:
    """
    Load an SQL statement from this module's ``sql/`` directory.

    :param filename: File name inside the ``sql/`` directory.
    :return: SQL query string.
    :raises FileNotFoundError: If the file does not exist.
    :raises PermissionError: If the file cannot be accessed.
    :raises UnicodeDecodeError: If the file cannot be decoded.
    """
    path = SQL_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as exc:
        logger.error(
            "[CHATS|DAO] Failed to load SQL file '%s': %s",
            path,
            exc,
        )
        raise


class BaseChatDAO(ABC):
    """
    Abstract base class for chat database access.

    Subclasses must provide:
      - Connection / execution primitives.
      - Transaction handling (commit/rollback where applicable).
      - Integrity-error mapping to domain errors.
    """

    # ---------- Backend typing / error classes ----------

    @property
    @abstractmethod
    def db_error_class(self) -> type[Exception]:
        """
        Base database exception type for the backend.

        :return: Exception class for general DB errors.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def integrity_error_class(self) -> type[Exception]:
        """
        Backend-specific integrity error (unique violation, etc.).

        :return: Exception class for integrity errors.
        """
        raise NotImplementedError

    # ---------- Execution primitives ----------

    @abstractmethod
    def stats_query_filename(self) -> str:
        """
        Return the backend-specific filename for the global stats query.

        :return: Query file name (e.g., sqlite or postgres variant).
        """
        raise NotImplementedError

    @abstractmethod
    def _select_all(
        self,
        query: str,
        params: dict | None = None,
    ) -> list[dict]:
        """
        Execute a SELECT that returns many rows.

        :param query: SQL query string.
        :param params: Bound parameters (optional).
        :return: List of result rows as dictionaries (empty if no matches).
        """
        raise NotImplementedError

    @abstractmethod
    def _select_one(
        self,
        query: str,
        params: dict | None = None,
    ) -> dict | None:
        """
        Execute a SELECT that returns a single row.

        :param query: SQL query string.
        :param params: Bound parameters (optional).
        :return: Row as a dictionary, or ``None`` if not found.
        """
        raise NotImplementedError

    @abstractmethod
    def _execute_dml(
        self,
        query: str,
        params: dict | None = None,
    ) -> int:
        """
        Execute an INSERT/UPDATE/DELETE and commit.

        :param query: SQL statement.
        :param params: Bound parameters (optional).
        :return: Number of affected rows.
        """
        raise NotImplementedError

    @abstractmethod
    def _execute_insert(
        self,
        query: str,
        params: dict,
    ) -> tuple[object, object | None]:
        """
        Execute an INSERT and return backend-specific handles.

        :param query: SQL INSERT statement.
        :param params: Bound parameters.
        :return: Tuple (result, cursor) – result object and optional cursor.
        """
        raise NotImplementedError

    @abstractmethod
    def get_last_inserted_id(
        self,
        result: object,
        cursor: object | None = None,
    ) -> int | None:
        """
        Extract the primary key of the last inserted row.

        Notes:
          - PostgreSQL: retrieved from ``result.mappings().fetchone()``
          - SQLite: retrieved from ``cursor.lastrowid``

        :param result: Backend result object (e.g., SQLAlchemy Result).
        :param cursor: Optional DB-API cursor (e.g., SQLite).
        :return: Inserted row primary key, or ``None`` if unavailable.
        """
        raise NotImplementedError

    @abstractmethod
    def handle_integrity_error(self, exc: Exception, chat: Chat) -> None:
        """
        Map backend integrity errors into domain-specific ones.

        :param exc: Original backend exception.
        :param chat: Chat instance involved in the operation.
        :raises DuplicateSlugError: If the slug already exists.
        :raises DuplicateChatIDError: If the Telegram chat ID exists.
        """
        raise NotImplementedError

    # ---------- Backend-agnostic helpers built on primitives ----------

    def fetch_chats(
        self,
        sort_by: str = "last_message",
        order: str = "desc",
    ) -> list[dict]:
        """
        Retrieve chats with message count and last message timestamp.

        :param sort_by: Field to sort by.
        :param order: Sort direction (``'asc'`` or ``'desc'``).
        :return: Chat rows (dicts) with aggregate statistics.
        """
        config = OrderConfig(
            allowed_fields={"name", "message_count", "last_message"},
            default_field="last_message",
            default_order="desc",
            prefix="",
        )
        order_clause = build_order_clause(sort_by, order, config)
        query = load_sql("fetch_chats.sql").format(order_clause=order_clause)
        rows = self._select_all(query)
        logger.debug("[CHATS|DAO] Retrieved %d chat(s).", len(rows))
        return rows

    def fetch_chat_by_slug(self, slug: str) -> dict | None:
        """
        Retrieve a single chat by its slug.

        :param slug: Unique chat slug.
        :return: Row as dict if found, otherwise ``None``.
        """
        query = "SELECT * FROM chats WHERE slug = :slug;"
        row = self._select_one(query, {"slug": slug})
        if not row:
            logger.debug("[CHATS|DAO] No match for slug '%s'.", slug)
            return None
        return row

    def fetch_chat_by_id(self, pk: int) -> dict | None:
        """
        Retrieve a single chat by its primary key.

        :param pk: Chat primary key.
        :return: Row as dict if found, otherwise ``None``.
        """
        query = "SELECT * FROM chats WHERE id = :id;"
        row = self._select_one(query, {"id": pk})
        if not row:
            logger.debug("[CHATS|DAO] No match for ID=%d.", pk)
            return None
        return row

    def insert_chat_record(self, chat: Chat) -> int:
        """
        Insert a new chat record.

        :param chat: Chat instance to insert.
        :return: Primary key of the inserted chat.
        :raises DuplicateSlugError: If the slug already exists.
        :raises DuplicateChatIDError: If the Telegram chat ID already exists.
        :raises db_error_class: On any other database error.
        """
        query = load_sql("insert_chat.sql")
        try:
            result, cursor = self._execute_insert(
                query,
                chat.prepare_for_db(),
            )
            pk = self.get_last_inserted_id(result, cursor)
            if pk is None:
                logger.error(
                    "[CHATS|DAO] Insert returned no primary key (slug='%s').",
                    chat.slug,
                )
                raise self.db_error_class("Insert returned no primary key")
            logger.debug(
                "[CHATS|DAO] Inserted chat ID=%d (slug='%s').",
                pk,
                chat.slug,
            )
            return pk
        except self.integrity_error_class as exc:
            logger.debug(
                "[CHATS|DAO] Integrity error during insert (slug='%s'): %s",
                chat.slug,
                exc,
            )
            self.handle_integrity_error(exc, chat)
        except self.db_error_class as exc:
            logger.error(
                "[CHATS|DAO] Database error during insert (slug='%s'): %s",
                chat.slug,
                exc,
            )
            raise

    def update_chat_record(self, chat: Chat) -> None:
        """
        Update an existing chat record.

        :param chat: Chat instance with updated values (must have ``id``).
        :raises ChatNotFoundError: If the chat to update does not exist.
        :raises DuplicateSlugError: If the slug already exists.
        :raises DuplicateChatIDError: If the Telegram chat ID already exists.
        :raises db_error_class: On any other database error.
        """
        query = load_sql("update_chat.sql")
        try:
            params = chat.prepare_for_db()
            params["id"] = chat.id
            rowcount = self._execute_dml(query, params)
            if rowcount == 0:
                logger.warning(
                    "[CHATS|DAO] No rows updated for ID=%d.",
                    chat.id,
                )
                raise ChatNotFoundError(chat_id=chat.id)
            logger.debug(
                "[CHATS|DAO] Updated chat ID=%d (slug='%s').",
                chat.id,
                chat.slug,
            )
        except self.integrity_error_class as exc:
            logger.debug(
                "[CHATS|DAO] Integrity error during update (slug='%s'): %s",
                chat.slug,
                exc,
            )
            self.handle_integrity_error(exc, chat)
        except self.db_error_class as exc:
            logger.error(
                "[CHATS|DAO] Database error during update (slug='%s'): %s",
                chat.slug,
                exc,
            )
            raise

    def delete_chat_record(self, pk: int) -> None:
        """
        Delete a chat record by its primary key.

        :param pk: Chat primary key.
        :raises ChatNotFoundError: If no chat exists with the given key.
        """
        query = "DELETE FROM chats WHERE id = :id;"
        rowcount = self._execute_dml(query, {"id": pk})
        if rowcount == 0:
            logger.warning(
                "[CHATS|DAO] No chat found to delete with ID=%d.",
                pk,
            )
            raise ChatNotFoundError(chat_id=pk)
        logger.debug("[CHATS|DAO] Deleted chat ID=%d.", pk)

    def check_slug_exists(
        self,
        slug: str,
        exclude_id: int | None = None,
    ) -> bool:
        """
        Check whether a chat slug already exists.

        :param slug: Chat slug to check.
        :param exclude_id: Optional chat primary key to exclude.
        :return: ``True`` if the slug exists, otherwise ``False``.
        """
        query = "SELECT 1 FROM chats WHERE slug = :slug"
        params = {"slug": slug}
        if exclude_id is not None:
            query += " AND id != :id"
            params["id"] = exclude_id
        query += " LIMIT 1;"
        row = self._select_one(query, params)
        return row is not None

    def check_chat_id_exists(
        self,
        chat_id: int,
        exclude_id: int | None = None,
    ) -> bool:
        """
        Check whether a Telegram chat ID already exists.

        :param chat_id: Telegram chat ID to check.
        :param exclude_id: Optional chat primary key to exclude.
        :return: ``True`` if the Telegram chat ID exists, ``False`` otherwise.
        """
        query = "SELECT 1 FROM chats WHERE chat_id = :chat_id"
        params = {"chat_id": chat_id}
        if exclude_id is not None:
            query += " AND id != :id"
            params["id"] = exclude_id
        query += " LIMIT 1;"
        row = self._select_one(query, params)
        return row is not None

    def fetch_global_chat_stats(self) -> dict:
        """
        Retrieve global aggregate statistics for all chats.

        Includes total chats and messages, media message count, the most
        active chat by message count, and attributes of the last message.

        :return: Aggregated statistics (empty dict if unavailable).
        """
        query = load_sql(self.stats_query_filename())
        row = self._select_one(query)
        logger.debug("[CHATS|DAO] Retrieved global chat statistics.")
        return row or {}
