"""
Message filter database access for the Arcanum application.

Handles low-level database operations for retrieving messages using
text, tag, and date filters. Supports global and chat-specific scopes,
with ordering and structured result sets.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.models.filters import MessageFilters
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import OrderConfig, build_order_clause
from app.utils.filters_utils import build_sql_clause

logger = logging.getLogger(__name__)


def fetch_filtered_messages(
    filters: MessageFilters,
    sort_by: str = "timestamp",
    order: str = "desc"
) -> list[dict]:
    """
    Retrieve messages matching the search query, tag, or date filters.

    Supports both global and chat-specific scopes, with configurable
    sorting and structured result rows.

    :param filters: Filter parameters to apply.
    :param sort_by: Field to sort by ('msg_id' or 'timestamp').
    :param order: Sort direction ('asc' or 'desc').
    :return: List of message row dictionaries matching the filter criteria.
    :raises SQLAlchemyError: If the query fails.
    """
    config = OrderConfig(
        allowed_fields={"msg_id", "timestamp"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    where_clause, params = build_sql_clause(filters, filters.chat_slug)
    order_clause = build_order_clause(sort_by, order, config)

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
        session = get_connection_lazy()
        result_proxy = session.execute(text(query), params)
        rows = result_proxy.mappings().all()
        result = [dict(row) for row in rows]
        _log_filter_result(filters, len(result))
        return result

    except SQLAlchemyError as e:
        logger.error("[FILTERS|DAO] Query failed: %s", e)
        raise


def _log_filter_result(filters: MessageFilters, count: int) -> None:
    """
    Log a summary of the filter query result.

    Displays the action type (search, tag, or date), number of matches,
    chat scope, and filter value.

    :param filters: Filters used for the query.
    :param count: Number of matched messages.
    :raises ValueError: If the action is unknown.
    """
    chat = filters.chat_slug or "<all>"

    if filters.action == "search":
        logger.debug(
            "[FILTERS|DAO] Retrieved %d message(s) | action=search | "
            "chat='%s' | query='%s'",
            count, chat, filters.query or filters.tag or "<none>"
        )
    elif filters.action == "tag":
        logger.debug(
            "[FILTERS|DAO] Retrieved %d message(s) | action=tag | "
            "chat='%s' | tag='%s'",
            count, chat, filters.tag or "<none>"
        )
    elif filters.action == "filter":
        msg = (
            f"[FILTERS|DAO] Retrieved {count} message(s) | action=filter | "
            f"chat='{chat}' | mode={filters.date_mode or '<none>'} | "
            f"start={filters.start_date or '-'}"
        )
        if filters.date_mode == "between":
            msg += f" | end={filters.end_date or '-'}"
        logger.debug(msg)
    else:
        logger.error("[FILTERS|DAO] Unknown action: '%s'", filters.action)
        raise ValueError(f"Unknown filter action: {filters.action}")
