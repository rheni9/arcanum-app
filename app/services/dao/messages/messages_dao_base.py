"""
Base Data Access Object (DAO) for message-related database operations
in the Arcanum application.

Defines business logic helpers for message operations and delegates
backend-specific execution to concrete subclasses (SQLite, PostgreSQL).

SQL queries:
    - Multi-line / complex statements (INSERT/UPDATE/fetch) live in the
      co-located ``sql/`` directory and are loaded via ``load_sql()``.
    - Simple one-liners (lookup, existence checks, delete-by-id) stay
      inline for readability.

All methods rely on subclasses for connection handling, SQL execution,
and integrity-error mapping (unique violations, etc.).
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from app.models.message import Message
from app.utils.sql_utils import OrderConfig, build_order_clause
from app.errors import MessageNotFoundError

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
            "[MESSAGES|DAO] Failed to load SQL file '%s': %s",
            path,
            exc,
        )
        raise


class BaseMessageDAO(ABC):
    """
    Abstract base class for message database access.

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
    def handle_integrity_error(self, exc: Exception, msg: Message) -> None:
        """
        Map backend integrity errors into domain-specific ones.

        :param exc: Original backend exception.
        :param msg: Message instance involved in the operation.
        :raises DuplicateMessageError: If (chat_ref_id, msg_id) is not unique.
        """
        raise NotImplementedError

    # ---------- Backend-specific SQL helpers ----------

    @abstractmethod
    def _get_ts_expressions(self) -> tuple[str, str]:
        """
        Return backend-specific SQL expressions for timestamp comparison.

        Returns:
            tuple[str, str]: A pair `(ts_expr, ts_param)` where:
                - ts_expr: SQL expression for the timestamp column.
                - ts_param: SQL placeholder for the bound parameter.

        Example:
            SQLite   -> ("datetime(timestamp)", "datetime(:current_ts)")
            Postgres -> ("timestamp", ":current_ts")
        """
        raise NotImplementedError

    # ---------- Backend-agnostic helpers built on primitives ----------

    def fetch_messages_by_chat(
        self,
        chat_slug: str,
        sort_by: str = "timestamp",
        order: str = "desc",
    ) -> list[dict]:
        """
        Retrieve messages for a specific chat with sorting.

        :param chat_slug: Slug of the target chat.
        :param sort_by: Field to sort by (``timestamp`` or ``msg_id``).
        :param order: Sort direction (``'asc'`` or ``'desc'``).
        :return: Message rows (dicts).
        """
        config = OrderConfig(
            allowed_fields={"timestamp", "msg_id"},
            default_field="timestamp",
            default_order="desc",
            prefix="m.",
        )
        order_clause = build_order_clause(sort_by, order, config)
        query = load_sql("fetch_messages_by_chat.sql").format(
            order_clause=order_clause,
        )
        rows = self._select_all(query, {"slug": chat_slug})
        logger.debug(
            "[MESSAGES|DAO] Retrieved %d message(s) for chat '%s'.",
            len(rows),
            chat_slug,
        )
        return rows

    def fetch_message_by_id(self, pk: int) -> dict | None:
        """
        Retrieve a single message by its primary key.

        :param pk: Message primary key.
        :return: Row as dict if found, otherwise ``None``.
        """
        query = "SELECT * FROM messages WHERE id = :id;"
        row = self._select_one(query, {"id": pk})
        if not row:
            logger.debug("[MESSAGES|DAO] No match for ID=%d.", pk)
            return None
        return row

    def _fetch_adjacent_message(
        self,
        chat_ref_id: int,
        current_ts: datetime,
        direction: str,
    ) -> dict | None:
        """
        Retrieve the adjacent message (previous or next) within the same chat.

        :param chat_ref_id: Chat primary key (foreign key in messages table).
        :param current_ts: Timestamp of the reference message (exclusive).
        :param direction: Either "previous" or "next".
        :return: Row as a dict if found, otherwise ``None``.
        :raises ValueError: If ``direction`` is not ``"previous"``
                            or ``"next"``.
        """
        if direction == "previous":
            comparator, order = "<", "DESC"
        elif direction == "next":
            comparator, order = ">", "ASC"
        else:
            raise ValueError("Direction must be 'previous' or 'next'")

        ts_expr, ts_param = self._get_ts_expressions()

        query = load_sql("fetch_adjacent_message.sql").format(
            ts_expr=ts_expr,
            ts_param=ts_param,
            comparator=comparator,
            order=order,
        )
        return self._select_one(
            query,
            {"chat_ref_id": chat_ref_id, "current_ts": current_ts},
        )

    def fetch_previous_message(
        self,
        chat_ref_id: int,
        current_ts: datetime,
    ) -> dict | None:
        """
        Retrieve the message before the given timestamp within the same chat.
        """
        return self._fetch_adjacent_message(
            chat_ref_id, current_ts, "previous"
        )

    def fetch_next_message(
        self,
        chat_ref_id: int,
        current_ts: datetime,
    ) -> dict | None:
        """
        Retrieve the message after the given timestamp within the same chat.
        """
        return self._fetch_adjacent_message(chat_ref_id, current_ts, "next")

    def insert_message_record(self, message: Message) -> int:
        """
        Insert a new message record.

        :param message: Message instance to insert.
        :return: Primary key of the inserted message.
        :raises DuplicateMessageError: If (chat_ref_id, msg_id) is not unique.
        :raises db_error_class: On any other database error.
        """
        query = load_sql("insert_message.sql")
        try:
            result, cursor = self._execute_insert(
                query,
                message.prepare_for_db(),
            )
            pk = self.get_last_inserted_id(result, cursor)
            if pk is None:
                logger.error(
                    "[MESSAGES|DAO] Insert returned no primary key "
                    "(chat_ref_id=%d, msg_id=%d).",
                    message.chat_ref_id,
                    message.msg_id,
                )
                raise self.db_error_class("Insert returned no primary key")
            logger.debug(
                "[MESSAGES|DAO] Inserted message ID=%d (chat_ref_id=%d).",
                pk,
                message.chat_ref_id,
            )
            return pk
        except self.integrity_error_class as exc:
            logger.debug(
                "[MESSAGES|DAO] Integrity error during insert "
                "(chat_ref_id=%d, msg_id=%d): %s",
                message.chat_ref_id,
                message.msg_id,
                exc,
            )
            self.handle_integrity_error(exc, message)
        except self.db_error_class as exc:
            logger.error(
                "[MESSAGES|DAO] Database error during insert "
                "(chat_ref_id=%d, msg_id=%d): %s",
                message.chat_ref_id,
                message.msg_id,
                exc,
            )
            raise

    def update_message_record(self, message: Message) -> None:
        """
        Update an existing message record.

        :param message: Message instance with updated values
                        (must have ``id``).
        :raises MessageNotFoundError: If the message to update does not exist.
        :raises DuplicateMessageError: If (chat_ref_id, msg_id) is not unique.
        :raises db_error_class: On any other database error.
        """
        query = load_sql("update_message.sql")
        try:
            params = message.prepare_for_db()
            params["id"] = message.id
            rowcount = self._execute_dml(query, params)
            if rowcount == 0:
                logger.warning(
                    "[MESSAGES|DAO] No rows updated for ID=%d.",
                    message.id,
                )
                raise MessageNotFoundError(message_id=message.id)
            logger.debug(
                "[MESSAGES|DAO] Updated message ID=%d (chat_ref_id=%d).",
                message.id,
                message.chat_ref_id,
            )
        except self.integrity_error_class as exc:
            logger.debug(
                "[MESSAGES|DAO] Integrity error during update "
                "(chat_ref_id=%d, msg_id=%d): %s",
                message.chat_ref_id,
                message.msg_id,
                exc,
            )
            self.handle_integrity_error(exc, message)
        except self.db_error_class as exc:
            logger.error(
                "[MESSAGES|DAO] Database error during update "
                "(chat_ref_id=%d, msg_id=%d): %s",
                message.chat_ref_id,
                message.msg_id,
                exc,
            )
            raise

    def delete_message_record(self, pk: int) -> None:
        """
        Delete a message record by its primary key.

        :param pk: Message primary key.
        :raises MessageNotFoundError: If no message exists with the given key.
        """
        query = "DELETE FROM messages WHERE id = :id;"
        rowcount = self._execute_dml(query, {"id": pk})
        if rowcount == 0:
            logger.warning(
                "[MESSAGES|DAO] No message found to delete with ID=%d.",
                pk,
            )
            raise MessageNotFoundError(message_id=pk)
        logger.debug("[MESSAGES|DAO] Deleted message ID=%d.", pk)

    def check_message_exists(
        self,
        chat_ref_id: int,
        msg_id: int,
        exclude_id: int | None = None,
    ) -> bool:
        """
        Check whether a given (chat_ref_id, msg_id) pair already exists.

        This pair uniquely identifies a Telegram message ID
        within a single chat.

        :param chat_ref_id: Chat primary key (foreign key).
        :param msg_id: Telegram message ID (unique per chat).
        :param exclude_id: Optional message primary key to exclude.
        :return: ``True`` if such a message ID exists in the chat,
                 otherwise ``False``.
        """
        query = (
            "SELECT 1 FROM messages "
            "WHERE chat_ref_id = :chat_ref_id AND msg_id = :msg_id"
        )
        params = {"chat_ref_id": chat_ref_id, "msg_id": msg_id}
        if exclude_id is not None:
            query += " AND id != :id"
            params["id"] = exclude_id
        query += " LIMIT 1;"
        row = self._select_one(query, params)
        return row is not None

    def count_messages_for_chat(self, chat_ref_id: int) -> int:
        """
        Count the number of messages in a given chat.

        :param chat_ref_id: ID of the related chat (foreign key).
        :return: Total number of messages in the chat.
        """
        query = (
            "SELECT COUNT(*) AS cnt "
            "FROM messages "
            "WHERE chat_ref_id = :chat_ref_id;"
        )
        row = self._select_one(query, {"chat_ref_id": chat_ref_id})
        total = int(row["cnt"]) if row else 0
        logger.debug(
            "[MESSAGES|DAO] Counted %d message(s) for chat_ref_id=%d.",
            total,
            chat_ref_id,
        )
        return total
