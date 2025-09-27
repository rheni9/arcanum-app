"""
SQLite Data Access Object (DAO) for chat operations
in the Arcanum application.

Implements BaseChatDAO using the sqlite3 DB-API and translates
integrity errors into domain-specific exceptions.
"""

import logging
import sqlite3

from app.models.chat import Chat
from app.utils.db_utils import get_connection_lazy
from app.errors import DuplicateSlugError, DuplicateChatIDError
from .chats_dao_base import BaseChatDAO

logger = logging.getLogger(__name__)


class SQLiteChatDAO(BaseChatDAO):
    """
    SQLite Data Access Object for chat operations.

    Uses raw sqlite3 connections/cursors and commits per statement.
    """

    # ---------- Backend typing / error classes ----------

    @property
    def db_error_class(self) -> type[Exception]:
        """SQLite base database error class."""
        return sqlite3.DatabaseError

    @property
    def integrity_error_class(self) -> type[Exception]:
        """SQLite integrity error class."""
        return sqlite3.IntegrityError

    # ---------- BaseChatDAO specifics ----------

    def stats_query_filename(self) -> str:
        """Return filename of the global stats SQL for SQLite."""
        return "fetch_global_chat_stats.sqlite.sql"

    # ---------- Execution primitives ----------

    def _select_all(
        self,
        query: str,
        params: dict | None = None,
    ) -> list[dict]:
        """Execute a SELECT and return all rows."""
        conn = get_connection_lazy()
        cursor = conn.execute(query, params or {})
        try:
            rows = cursor.fetchall()
            data = [dict(r) for r in rows]
            logger.debug(
                "[SQLITE|CHATS|DAO] _select_all -> %d row(s).",
                len(data),
            )
            return data
        except sqlite3.DatabaseError as exc:
            logger.error("[SQLITE|CHATS|DAO] _select_all failed: %s", exc)
            raise
        finally:
            cursor.close()

    def _select_one(
        self,
        query: str,
        params: dict | None = None,
    ) -> dict | None:
        """Execute a SELECT and return a single row."""
        conn = get_connection_lazy()
        cursor = conn.execute(query, params or {})
        try:
            row = cursor.fetchone()
            data = dict(row) if row else None
            logger.debug(
                "[SQLITE|CHATS|DAO] _select_one -> %s",
                "hit" if data else "none",
            )
            return data
        except sqlite3.DatabaseError as exc:
            logger.error("[SQLITE|CHATS|DAO] _select_one failed: %s", exc)
            raise
        finally:
            cursor.close()

    def _execute_dml(
        self,
        query: str,
        params: dict | None = None,
    ) -> int:
        """Execute INSERT/UPDATE/DELETE and commit."""
        conn = get_connection_lazy()
        cursor = conn.execute(query, params or {})
        try:
            conn.commit()
            logger.debug(
                "[SQLITE|CHATS|DAO] _execute_dml committed. rowcount=%s",
                cursor.rowcount,
            )
            return int(cursor.rowcount or 0)
        except sqlite3.IntegrityError as exc:
            logger.debug(
                "[SQLITE|CHATS|DAO] Integrity error in _execute_dml: %s",
                exc,
            )
            raise
        except sqlite3.DatabaseError as exc:
            logger.error("[SQLITE|CHATS|DAO] _execute_dml failed: %s", exc)
            raise
        finally:
            cursor.close()

    def _execute_insert(
        self,
        query: str,
        params: dict,
    ) -> tuple[object, sqlite3.Cursor | None]:
        """
        Execute INSERT using sqlite3 and return the raw cursor.

        The cursor is returned so that ``lastrowid`` can be retrieved.
        """
        conn = get_connection_lazy()
        cursor = conn.execute(query, params)
        try:
            conn.commit()
            logger.debug("[SQLITE|CHATS|DAO] _execute_insert committed.")
            return None, cursor
        except sqlite3.IntegrityError as exc:
            logger.debug(
                "[SQLITE|CHATS|DAO] Integrity error in _execute_insert: %s",
                exc,
            )
            raise
        except sqlite3.DatabaseError as exc:
            logger.error("[SQLITE|CHATS|DAO] _execute_insert failed: %s", exc)
            raise

    def get_last_inserted_id(
        self,
        result: object,
        cursor: sqlite3.Cursor | None = None,
    ) -> int | None:
        """
        Extract primary key from SQLite INSERT cursor.

        :param result: Unused for SQLite.
        :param cursor: DB-API cursor from the INSERT execution.
        :return: Inserted primary key or ``None``.
        """
        return cursor.lastrowid if cursor else None

    def handle_integrity_error(
        self,
        exc: sqlite3.IntegrityError,
        chat: Chat,
    ) -> None:
        """
        Map sqlite IntegrityError to domain-specific exceptions.

        :param exc: sqlite3.IntegrityError raised by the backend.
        :param chat: Chat instance involved in the operation.
        :raises DuplicateSlugError: If unique on slug fails.
        :raises DuplicateChatIDError: If unique on chat_id fails.
        """
        text = exc.args[0] if exc.args else ""
        if "UNIQUE constraint failed" in text:
            if "chats.slug" in text:
                raise DuplicateSlugError(slug=chat.slug) from exc
            if "chats.chat_id" in text:
                raise DuplicateChatIDError(chat_id=chat.chat_id) from exc
        raise exc
