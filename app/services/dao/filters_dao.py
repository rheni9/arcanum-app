"""
Message filter database access for the Arcanum application.

Handles low-level operations for message filtering by text or date,
with optional chat restriction. Supports sorting and chat metadata.
"""

import logging
from sqlite3 import DatabaseError

from app.models.filters import MessageFilters
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import OrderConfig, build_order_clause
from app.utils.filters_utils import build_sql_clause

logger = logging.getLogger(__name__)


def fetch_filtered_messages(
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> list[dict]:
    """
    Retrieve messages using search or date filtering logic.

    Applies full-text search ("search" action) or timestamp-based
    filtering ("filter" action). Results may be limited to a
    specific chat via filters.chat_slug.

    :param filters: MessageFilters instance with normalized fields.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of matching message row dicts.
    :raises DatabaseError: If the query fails.
    """
    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    order_clause = build_order_clause(sort_by, order, config)
    where_clause, params = build_sql_clause(filters, filters.chat_slug)

    query = (
        "SELECT m.id, m.chat_ref_id, m.msg_id, m.timestamp,"
        "m.link, m.text, m.media, m.screenshot, m.tags, m.notes,"
        "c.name AS chat_name, c.slug AS chat_slug "
        "FROM messages m "
        "JOIN chats c ON m.chat_ref_id = c.id "
        f"{where_clause} "
        f"ORDER BY {order_clause};"
    )

    try:
        conn = get_connection_lazy()
        rows = conn.execute(query, params).fetchall()
        _log_filter_result(filters, len(rows))
        return [dict(row) for row in rows]

    except DatabaseError as e:
        logger.error("[FILTERS|DAO] Query failed: %s", e)
        raise


def _log_filter_result(filters: MessageFilters, count: int) -> None:
    """
    Log a structured message summarizing the filter results.

    :param filters: Filters that were applied.
    :param count: Number of messages returned.
    :raises ValueError: If an unknown action type is provided.
    """
    action_loggers = {
        "search": lambda: logger.debug(
            "[FILTERS|DAO] Retrieved %d message(s) | action=search | "
            "chat='%s' | query='%s'",
            count, filters.chat_slug or "<all>",
            filters.query or filters.tag or "<none>"
        ),
        "tag": lambda: logger.debug(
            "[FILTERS|DAO] Retrieved %d message(s) | action=tag | "
            "chat='%s' | tag='%s'",
            count, filters.chat_slug or "<all>",
            filters.tag or "<none>"
        ),
        "filter": lambda: logger.debug(
            "[FILTERS|DAO] Retrieved %d message(s) | action=filter | "
            "chat='%s' | mode=%s | start=%s%s",
            count,
            filters.chat_slug or "<all>",
            filters.date_mode or "<none>",
            filters.start_date or "<none>",
            f" | end={filters.end_date}"
            if filters.date_mode == "between" else ""
        )
    }

    if filters.action not in action_loggers:
        logger.debug(
            "[FILTERS|DAO] Unknown filter action: '%s'", filters.action
        )
        raise ValueError(f"Unknown filter action: {filters.action}")

    action_loggers[filters.action]()
