"""
Service module for managing and querying messages in the Arcanum application.

Provides utilities to:
- retrieve messages by chat,
- perform full-text search queries,
- filter messages by date.

All queries use context-managed SQLite access with consistent ordering,
validation, and structured logging for debugging and monitoring.
"""

import logging
from typing import List, Optional, Tuple
from sqlite3 import DatabaseError

from app.models.filters import MessageFilters
from app.utils.db_utils import get_connection
from app.utils.sql_utils import build_order_clause, OrderConfig

logger = logging.getLogger(__name__)


def get_chat_data(
    slug: str,
    sort_by: str = "timestamp",
    order: str = "desc"
) -> Tuple[int, List[dict]]:
    """
    Retrieve all messages for a specific chat and count them.

    Combines:
    - Counting total messages in the chat.
    - Retrieving message details (msg_id, link, text, timestamp).

    Results are sorted according to the provided field and order.

    :param slug: Slug of the chat to retrieve messages from.
    :type slug: str
    :param sort_by: Sorting field ('timestamp' or 'msg_id').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :return: Tuple with (message_count, list of messages).
    :rtype: Tuple[int, List[dict]]
    :raises DatabaseError: If retrieval fails.
    """
    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc"
    )

    query_count = "SELECT COUNT(*) FROM messages WHERE chat_slug = ?"
    query_messages = f'''
        SELECT msg_id, link, text, timestamp
        FROM messages
        WHERE chat_slug = ?
        {build_order_clause(sort_by, order, config)}
    '''

    try:
        with get_connection() as conn:
            result = conn.execute(query_count, (slug,)).fetchone()
            count = result[0] if result else 0

            rows = conn.execute(query_messages, (slug,)).fetchall()

    except DatabaseError as e:
        logger.error(
            "[DB] Failed to retrieve messages and count for chat '%s': %s",
            slug, e
        )
        raise

    logger.debug("[COUNT] Counted %d message(s) in chat '%s'.", count, slug)
    logger.info("[DB] Messages have been retrieved for chat '%s' (%d total).",
                slug, len(rows))

    return count, [dict(row) for row in rows]


def search_messages_by_text(
    filters: MessageFilters,
    sort_by: str = "timestamp",
    order: str = "desc",
    chat_slug: Optional[str] = None,
) -> List[dict]:
    """
    Perform a full-text search on message content.

    Searches all messages (or within a single chat) for those containing
    a given query string. Joins with the `chats` table to include chat names.

    :param filters: Search filter object containing the query.
    :type filters: MessageFilters
    :param sort_by: Sorting field ('timestamp' or 'msg_id').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional slug to restrict results to a single chat.
    :type chat_slug: Optional[str]
    :return: List of matched messages with metadata.
    :rtype: List[dict]
    :raises DatabaseError: If database query fails.
    """
    filters.normalize()
    if not filters.query:
        return []

    sql = """
        SELECT m.*, c.name AS chat_name
        FROM messages m
        JOIN chats c ON m.chat_slug = c.slug
        WHERE m.text LIKE ?
    """
    params = [f"%{filters.query}%"]

    if chat_slug:
        sql += " AND m.chat_slug = ?"
        params.append(chat_slug)

    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    sql += build_order_clause(sort_by=sort_by, order=order, config=config)

    try:
        with get_connection() as conn:
            results = conn.execute(sql, params).fetchall()
    except DatabaseError as e:
        logger.error("[SEARCH] Failed to execute text search: %s", e)
        raise

    logger.info("[SEARCH] Query '%s' has returned %d message(s) in chat '%s'.",
                filters.query, len(results), chat_slug or "<all>")
    return [dict(row) for row in results]


def filter_messages(
    filters: MessageFilters,
    sort_by: str = "timestamp",
    order: str = "desc",
    chat_slug: Optional[str] = None,
) -> List[dict]:
    """
    Filter messages by date according to selected mode.

    Supports filtering by:
    - specific day ('on'),
    - before or after a given date,
    - date range between two values.

    :param filters: Normalized filter parameters.
    :type filters: MessageFilters
    :param sort_by: Sorting field ('timestamp' or 'msg_id').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional slug to restrict results to a single chat.
    :type chat_slug: Optional[str]
    :return: List of filtered messages.
    :rtype: List[dict]
    :raises DatabaseError: If query execution fails.
    """
    filters.normalize()
    sql = """
        SELECT m.*, c.name AS chat_name
        FROM messages m
        JOIN chats c ON m.chat_slug = c.slug
        WHERE 1 = 1
    """
    params = []

    if chat_slug:
        sql += " AND m.chat_slug = ?"
        params.append(chat_slug)

    valid_filter = False

    if filters.date_mode == "on":
        sql += " AND m.timestamp LIKE ?"
        params.append(f"{filters.start_date}%")
        valid_filter = True
    if filters.date_mode == "before":
        sql += " AND m.timestamp < ?"
        params.append(filters.start_date)
        valid_filter = True
    if filters.date_mode == "after":
        sql += " AND m.timestamp > ?"
        params.append(filters.start_date)
        valid_filter = True
    if filters.date_mode == "between" and filters.end_date:
        sql += " AND m.timestamp BETWEEN ? AND ?"
        params.extend([filters.start_date, filters.end_date + "T23:59:59"])
        valid_filter = True

    if not valid_filter:
        logger.warning(
            "[FILTER] Invalid or incomplete filter input: %s", filters
        )

    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )

    sql += build_order_clause(sort_by=sort_by, order=order, config=config)

    try:
        with get_connection() as conn:
            results = conn.execute(sql, params).fetchall()
    except DatabaseError as e:
        logger.error("[FILTER] Failed to execute date filter: %s", e)
        raise

    logger.info(
        "[FILTER] Retrieved %d message(s) | mode=%s | start=%s%s | chat=%s",
        len(results),
        filters.date_mode,
        filters.start_date,
        f", end={filters.end_date}" if filters.date_mode == "between" else "",
        chat_slug or "<all>"
    )

    return [dict(row) for row in results]
