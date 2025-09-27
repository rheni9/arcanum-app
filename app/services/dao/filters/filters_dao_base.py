"""
Base Data Access Object (DAO) for message filter operations
in the Arcanum application.

Defines backend-agnostic logic for applying filters (search, tag,
date ranges) and delegates execution to backend-specific subclasses
(SQLite, PostgreSQL).

SQL queries:
    - Multi-line / complex statements (JOIN, filtering, ordering)
      live in the co-located ``sql/`` directory and are loaded via
      ``load_sql()``.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from app.models.filters import MessageFilters
from app.utils.sql_utils import OrderConfig, build_order_clause

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


class BaseFiltersDAO(ABC):
    """
    Abstract base class for message filter database access.

    Subclasses must provide:
      - Connection / execution primitives.
      - Backend-specific error handling.
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

    # ---------- Execution primitives ----------

    @abstractmethod
    def _build_where_clause(
        self,
        filters: MessageFilters,
    ) -> tuple[str, dict]:
        """
        Build backend-specific WHERE clause and params.

        :param filters: MessageFilters instance.
        :return: Tuple (WHERE clause, params).
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

    # ---------- Backend-agnostic filter helpers ----------

    def fetch_filtered_messages(
        self,
        filters: MessageFilters,
        sort_by: str = "timestamp",
        order: str = "desc",
    ) -> list[dict]:
        """
        Retrieve messages matching the search query, tag, or date filters.

        Supports both global and chat-specific scopes, with configurable
        sorting and structured result rows.

        :param filters: Filter parameters to apply.
        :param sort_by: Field to sort by ('msg_id' or 'timestamp').
        :param order: Sort direction ('asc' or 'desc').
        :return: List of message row dictionaries.
        :raises db_error_class: If the query fails.
        """
        config = OrderConfig(
            allowed_fields={"msg_id", "timestamp"},
            default_field="timestamp",
            default_order="desc",
            prefix="m.",
        )
        where_clause, params = self._build_where_clause(filters)
        order_clause = build_order_clause(sort_by, order, config)

        query = load_sql("fetch_filtered_messages.sql").format(
            where_clause=where_clause,
            order_clause=order_clause,
        )

        rows = self._select_all(query, params)
        self._log_filter_result(filters, len(rows))
        return rows

    # ---------- Logging helpers ----------

    def _log_filter_result(
        self,
        filters: MessageFilters,
        count: int,
    ) -> None:
        """
        Log a summary of the filter query result.

        Displays the action type (search, tag, or date),
        number of matches, chat scope, and filter value.

        :param filters: Filters used for the query.
        :param count: Number of matched messages.
        :raises ValueError: If the action is unknown.
        """
        chat = filters.chat_slug or "<all>"

        if filters.action == "search":
            logger.debug(
                "[FILTERS|DAO] Retrieved %d message(s) | action=search | "
                "chat='%s' | query='%s'",
                count,
                chat,
                filters.query or filters.tag or "<none>",
            )
        elif filters.action == "tag":
            logger.debug(
                "[FILTERS|DAO] Retrieved %d message(s) | action=tag | "
                "chat='%s' | tag='%s'",
                count,
                chat,
                filters.tag or "<none>",
            )
        elif filters.action == "filter":
            msg = (
                f"[FILTERS|DAO] Retrieved {count} message(s) | action=filter "
                f"| chat='{chat}' | mode={filters.date_mode or '<none>'} | "
                f"start={filters.start_date or '-'}"
            )
            if filters.date_mode == "between":
                msg += f" | end={filters.end_date or '-'}"
            logger.debug(msg)
        else:
            logger.error("[FILTERS|DAO] Unknown action: '%s'", filters.action)
            raise ValueError(f"Unknown filter action: {filters.action}")
