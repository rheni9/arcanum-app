"""
Filters service module for the Arcanum application.

Provides high-level search and filtering logic for messages.
Handles validation, normalization, and query dispatching.
"""

import logging
from typing import Optional, List, Tuple
from sqlite3 import DatabaseError

from app.models.filters import MessageFilters
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import build_order_clause, OrderConfig
from app.utils.filters_utils import validate_search_filters
from app.services.chats_service import get_chat_id_by_slug

logger = logging.getLogger(__name__)


def search_messages_by_text(
    filters: MessageFilters,
    sort_by: str = "timestamp",
    order: str = "desc",
    chat_slug: Optional[str] = None
) -> List[dict]:
    """
    Search messages by query string.

    :param filters: MessageFilters instance with query.
    :type filters: MessageFilters
    :param sort_by: Sort field ('timestamp', 'msg_id').
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional chat slug.
    :type chat_slug: Optional[str]
    :returns: List of matching message dicts.
    :rtype: List[dict]
    :raises DatabaseError: On search failure.
    """
    filters.normalize()
    if not filters.query:
        return []

    sql = """
        SELECT m.*, c.name AS chat_name
        FROM messages m
        JOIN chats c ON m.chat_ref_id = c.id
        WHERE m.text LIKE ?
    """
    params = [f"%{filters.query}%"]

    if chat_slug:
        chat_ref_id = get_chat_id_by_slug(chat_slug)
        sql += " AND m.chat_ref_id = ?"
        params.append(chat_ref_id)

    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    sql += build_order_clause(sort_by, order, config)

    try:
        conn = get_connection_lazy()
        results = conn.execute(sql, params).fetchall()
    except DatabaseError as e:
        logger.error("[DB|MESSAGES] Search query failed: %s", e)
        raise

    logger.debug(
        "[FILTERS|SERVICE] Found %d message(s) matching query '%s'%s.",
        len(results), filters.query,
        f" in chat '{chat_slug}'" if chat_slug else ""
    )

    return [dict(row) for row in results]


def filter_messages(
    filters: MessageFilters,
    sort_by: str = "timestamp",
    order: str = "desc",
    chat_slug: Optional[str] = None
) -> List[dict]:
    """
    Filter messages by date mode.

    :param filters: MessageFilters instance.
    :type filters: MessageFilters
    :param sort_by: Sort field ('timestamp', 'msg_id').
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional chat slug.
    :type chat_slug: Optional[str]
    :returns: List of filtered message dicts.
    :rtype: List[dict]
    :raises DatabaseError: On query failure.
    """
    filters.normalize()

    sql = """
        SELECT m.*, c.name AS chat_name
        FROM messages m
        JOIN chats c ON m.chat_ref_id = c.id
        WHERE 1 = 1
    """
    params = []

    if chat_slug:
        chat_ref_id = get_chat_id_by_slug(chat_slug)
        sql += " AND m.chat_ref_id = ?"
        params.append(chat_ref_id)

    valid_filter = False

    if filters.date_mode == "on" and filters.start_date:
        sql += " AND DATE(m.timestamp) = DATE(?)"
        params.append(filters.start_date)
        valid_filter = True
    elif filters.date_mode == "before" and filters.start_date:
        sql += " AND DATE(m.timestamp) < DATE(?)"
        params.append(filters.start_date)
        valid_filter = True
    elif filters.date_mode == "after" and filters.start_date:
        sql += " AND DATE(m.timestamp) > DATE(?)"
        params.append(filters.start_date)
        valid_filter = True
    elif filters.date_mode == "between" and filters.end_date:
        sql += " AND DATE(m.timestamp) BETWEEN DATE(?) AND DATE(?)"
        params.extend([filters.start_date, filters.end_date])
        valid_filter = True

    if not valid_filter:
        logger.warning(
            "[FILTERS|SERVICE] Invalid or incomplete filter: %s", filters
        )

    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    sql += build_order_clause(sort_by, order, config)

    try:
        conn = get_connection_lazy()
        results = conn.execute(sql, params).fetchall()
    except DatabaseError as e:
        logger.error("[DB|MESSAGES] Filter query failed: %s", e)
        raise

    logger.debug(
        "[FILTERS|SERVICE] Found %d message(s) for chat '%s' "
        "| mode=%s | start=%s%s.",
        len(results), chat_slug or "<all>",
        filters.date_mode, filters.start_date,
        f", end={filters.end_date}" if filters.date_mode == "between" else ""
    )

    return [dict(row) for row in results]


def resolve_search_action(
    filters: MessageFilters,
    sort_by: str,
    order: str,
    chat_slug: Optional[str] = None
) -> Tuple[List[dict], Optional[str], MessageFilters]:
    """
    Resolve search or filter action based on filters.

    :param filters: MessageFilters instance.
    :type filters: MessageFilters
    :param sort_by: Sort field ('timestamp', 'msg_id').
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :param chat_slug: Optional chat slug.
    :type chat_slug: Optional[str]
    :returns: Tuple of (messages, optional info message, normalized filters).
    :rtype: Tuple[List[dict], Optional[str], MessageFilters]
    """
    filters.normalize()

    is_valid, info_message = validate_search_filters(filters)

    if not is_valid:
        if filters.is_empty():
            logger.info("[FILTERS|SERVICE] No filters or query provided.")
            info_message = "No filters or search query applied."
        else:
            logger.warning(
                "[FILTERS|SERVICE] Invalid parameters: %s", filters
            )
        return [], info_message, filters

    if filters.action == "search" and filters.query:
        logger.debug(
            "[FILTERS|SERVICE] Search action | query='%s' | chat='%s'",
            filters.query, chat_slug or "<all>"
        )
        results = search_messages_by_text(filters, sort_by, order, chat_slug)
        return results, None, filters

    if filters.action == "filter" and filters.start_date:
        logger.debug(
            "[FILTERS|SERVICE] Filter action | mode=%s | start=%s | end=%s "
            "| chat='%s'",
            filters.date_mode, filters.start_date, filters.end_date,
            chat_slug or "<all>"
        )
        results = filter_messages(filters, sort_by, order, chat_slug)
        return results, None, filters

    logger.info("[FILTERS|SERVICE] No valid action resolved.")
    return [], info_message, filters
