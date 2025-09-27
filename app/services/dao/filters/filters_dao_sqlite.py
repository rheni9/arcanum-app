"""
SQLite Data Access Object (DAO) for message filter operations
in the Arcanum application.

Implements BaseFiltersDAO using the sqlite3 DB-API and provides
error translation and structured results.
"""

import logging
import sqlite3

from app.utils.db_utils import get_connection_lazy
from .filters_dao_base import BaseFiltersDAO

logger = logging.getLogger(__name__)


class SQLiteFiltersDAO(BaseFiltersDAO):
    """
    SQLite Data Access Object for message filter operations.

    Uses raw sqlite3 connections/cursors.
    """

    # ---------- Backend typing / error classes ----------

    @property
    def db_error_class(self) -> type[Exception]:
        """SQLite base database error class."""
        return sqlite3.DatabaseError

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
                "[SQLITE|FILTERS|DAO] _select_all -> %d row(s).",
                len(data),
            )
            return data
        except sqlite3.DatabaseError as exc:
            logger.error("[SQLITE|FILTERS|DAO] _select_all failed: %s", exc)
            raise
        finally:
            cursor.close()
