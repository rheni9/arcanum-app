"""
Message filter/search service for the Arcanum application.

Provides search and filter logic for messages both globally and within a chat.
Handles input validation, logging, grouping for UI, and safe database access.
"""

import logging
from sqlite3 import DatabaseError

from app.models.filters import MessageFilters
from app.services.dao.filters_dao import fetch_filtered_messages
from app.utils.filters_utils import (
    normalize_filter_action,
    validate_search_filters,
    group_messages_by_chat
)

logger = logging.getLogger(__name__)


def preprocess_filters(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Normalize and validate the given filters.

    :param filters: Filter instance to preprocess.
    :return: Tuple (status, message).
    """
    normalize_filter_action(filters)

    if filters.action == "search":
        if filters.query and filters.query.strip().startswith("#"):
            filters.tag = filters.query.strip().lstrip("#")
            filters.query = None
            filters.action = "tag"
        else:
            filters.tag = None
            filters.date_mode = None
            filters.start_date = None
            filters.end_date = None
    elif filters.action == "tag":
        if not filters.tag:
            return "invalid", "Please specify a tag."
        filters.query = None
        filters.date_mode = None
        filters.start_date = None
        filters.end_date = None
    elif filters.action == "filter":
        filters.query = None
        filters.tag = None

    if filters.action == "filter" and not filters.date_mode:
        return "invalid", "Please select a date filter mode."

    if filters.action == "search" and not filters.query:
        return "invalid", "Please enter a search query."

    if not filters.has_active() and not filters.action:
        return "cleared", None

    if filters.action is None:
        return "invalid", "Please enter a search query or select date filters."

    valid, error_msg = validate_search_filters(filters)
    if not valid:
        return "invalid", error_msg

    logger.debug(
        "[FILTERS|PRE] action=%s | query=%s | tag=%s "
        "| date_mode=%r | has_active=%s",
        filters.action, filters.query, filters.tag,
        filters.date_mode, filters.has_active()
    )

    return "valid", None

# def preprocess_filters(filters: MessageFilters) -> tuple[str, str | None]:
#     """
#     Normalize and validate the given filters.

#     :param filters: Filter instance to preprocess.
#     :return: Tuple (status, message).
#     """
#     normalize_filter_action(filters)

#     if not filters.has_active():
#         return "cleared", None

#     valid, error_msg = validate_search_filters(filters)
#     if not valid:
#         return "invalid", error_msg

#     return "valid", None


def resolve_message_query(
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> dict:
    """
    Search or filter messages using the specified filters.

    Supports both global and chat-local modes. Returns grouped messages
    for UI, total count, applied filters, and info message for the user.

    :param filters: MessageFilters instance (normalized).
    :param sort_by: Sort field ('timestamp' or 'msg_id').
    :param order: Sort direction ('asc' or 'desc').
    :return: Result dict with keys: messages, count, grouped,
                                    info_message, filters, cleared.
    :raises DatabaseError: If the query fails.
    """
    status, message = preprocess_filters(filters)

    if status == "cleared":
        logger.info(
            "[FILTERS|SERVICE] No filters to apply — skipping execution."
        )
        return _result_cleared(filters)

    if status == "invalid":
        logger.warning("[FILTERS|SERVICE] Invalid filters: %s", message)
        return _result_invalid(filters, message)

    try:
        messages = fetch_filtered_messages(filters, sort_by, order)
        count = len(messages)
        grouped = group_messages_by_chat(messages)

        logger.info(
            "[FILTERS|SERVICE] Retrieved %d message(s) | scope=%s",
            count, "global" if filters.is_global() else filters.chat_slug
        )
        return _result_valid(filters, messages, grouped, count)

    except DatabaseError as e:
        logger.error("[FILTERS|SERVICE] Query failed: %s", e)
        return _result_error(filters, e)


def _result_cleared(filters: MessageFilters) -> tuple[str, dict]:
    """Return a result dict for cleared filters (no input provided)."""
    info_message = "Use the search bar or date filters above to find messages."
    return "cleared", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": info_message,
        "filters": filters,
        "cleared": True,
    }


def _result_invalid(filters: MessageFilters, message: str) -> tuple[str, dict]:
    """Return a result dict for structurally invalid filters."""
    return "invalid", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": message,
        "filters": filters,
        "cleared": False,
    }


def _result_valid(
    filters: MessageFilters,
    messages: list[dict],
    grouped: dict,
    count: int
) -> tuple[str, dict]:
    return "valid", {
        "messages": messages,
        "count": count,
        "grouped": grouped,
        "info_message": None,
        "filters": filters,
        "cleared": False,
    }


def _result_error(
    filters: MessageFilters,
    error: Exception
) -> tuple[str, dict]:
    """Return a result dict for database failure with error message."""
    return "error", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": f"Database error: {error}",
        "filters": filters,
        "cleared": False,
    }
