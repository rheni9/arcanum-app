"""
PostgreSQL Data Access Object (DAO) for message filter operations
in the Arcanum application.

Implements BaseFiltersDAO using SQLAlchemy Core, provides connection
handling, query execution, and error translation.
"""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.models.filters import MessageFilters
from app.utils.db_utils import get_connection_lazy
from app.utils.filters_utils import build_sql_clause
from .filters_dao_base import BaseFiltersDAO

logger = logging.getLogger(__name__)


class PostgresFiltersDAO(BaseFiltersDAO):
    """
    PostgreSQL Data Access Object for message filter operations.

    Uses SQLAlchemy Core for execution.
    """

    # ---------- Backend typing / error classes ----------

    @property
    def db_error_class(self) -> type[Exception]:
        """PostgreSQL base database error class."""
        return SQLAlchemyError

    # ---------- Execution primitives ----------

    def _build_where_clause(
        self, filters: MessageFilters
    ) -> tuple[str, dict]:
        """Build a WHERE clause and parameters for PostgreSQL."""
        return build_sql_clause(filters, filters.chat_slug, dialect="postgres")

    def _select_all(
        self,
        query: str,
        params: dict | None = None,
    ) -> list[dict]:
        """Execute a SELECT and return all rows."""
        conn = get_connection_lazy()
        try:
            result = conn.execute(text(query), params or {})
            rows = result.mappings().all()
            data = [dict(r) for r in rows]
            logger.debug(
                "[PG|FILTERS|DAO] _select_all -> %d row(s).",
                len(data),
            )
            return data
        except SQLAlchemyError as exc:
            logger.error("[PG|FILTERS|DAO] _select_all failed: %s", exc)
            raise
