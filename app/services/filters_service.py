"""
Message filtering and search service operations for the Arcanum application.

Provides logic for searching and filtering messages globally or within
a specific chat. Validates filter input, prepares queries, structures
results, and delegates database operations to the DAO layer.
"""

import logging
from sqlite3 import DatabaseError

from app.models.filters import MessageFilters
from app.utils.i18n_utils import TranslatableMsg
from app.services.dao.filters_dao import fetch_filtered_messages
from app.utils.filters_utils import (
    normalize_filter_action,
    validate_search_filters
)
from app.utils.messages_utils import group_messages_by_chat

logger = logging.getLogger(__name__)


def resolve_message_query(
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> tuple[str, dict]:
    """
    Retrieve messages based on normalized filters.

    Executes global or chat-local query and groups results by chat.
    Returns structured output including status and user message.

    :param filters: Validated message filters.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: Result tuple with status and metadata.
    :raises DatabaseError: If the DAO operation fails.
    """
    status, msg = preprocess_filters(filters)

    if status == "cleared":
        logger.info(
            "[FILTERS|SERVICE] No filters to apply — skipping execution."
        )
        return _result_cleared(filters)

    if status == "invalid":
        logger.warning("[FILTERS|SERVICE] Invalid filters.")
        return _result_invalid(filters, msg)

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


def preprocess_filters(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Normalize and validate message filters.

    Distinguishes between 'search', 'tag', and 'filter' modes.
    Returns a status and optional localized message.

    :param filters: Filter parameters to process.
    :return: Tuple of validation status and message (if any).
    """
    normalize_filter_action(filters)
    status, msg = _route_validation(filters)

    logger.debug(
        "[FILTERS|PRE] status=%s | chat=%s | has_active=%s | action=%s "
        "| query=%r | tag=%r | mode=%r | start=%r | end=%r",
        status,
        filters.chat_slug or "<all>",
        filters.has_active(),
        filters.action,
        filters.query,
        filters.tag,
        filters.date_mode,
        filters.start_date,
        filters.end_date,
    )

    return status, msg


def _route_validation(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Route filters to appropriate validation logic based on action type.

    :param filters: Filter parameters.
    :return: Tuple with status and optional validation message.
    """
    if filters.action == "search":
        return _validate_search_query(filters)
    if filters.action == "tag":
        return _validate_tag_search(filters)
    if filters.action == "filter":
        return _validate_date_filter(filters)
    if not filters.has_active() and not filters.action:
        return "cleared", None

    # Fallback: delegate to utilities to decide exact error message.
    valid, msg = validate_search_filters(filters)
    return ("valid", None) if valid else ("invalid", msg)


def _validate_search_query(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Validate standard text search query or convert to tag search if the
    query is prefixed with '#'.

    :param filters: Filter parameters.
    :return: Tuple with status and optional validation message.
    """

    # Convert '#tag' into tag search
    if filters.query and filters.query.strip().startswith("#"):
        filters.tag = filters.query.strip().lstrip("#")
        filters.query = None
        filters.action = "tag"
        return _validate_tag_search(filters)

    valid, msg = validate_search_filters(filters)
    return ("valid", None) if valid else ("invalid", msg)


def _validate_tag_search(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Validate tag-based search.

    :param filters: Filter parameters.
    :return: Tuple with status and optional validation message.
    """
    valid, msg = validate_search_filters(filters)
    return ("valid", None) if valid else ("invalid", msg)


def _validate_date_filter(filters: MessageFilters) -> tuple[str, str | None]:
    """
    Validate date-based filter.

    :param filters: Filter parameters.
    :return: Tuple with status and optional validation message.
    """
    valid, msg = validate_search_filters(filters)
    return ("valid", None) if valid else ("invalid", msg)


def _result_valid(
    filters: MessageFilters,
    messages: list[dict],
    grouped: dict,
    count: int
) -> tuple[str, dict]:
    """
    Return the result of a successful message query.

    Includes message list, count, grouping, and filter metadata.

    :param filters: Filters used in the query.
    :param messages: Flat list of message dictionaries.
    :param grouped: Messages grouped by chat.
    :param count: Total number of matched messages.
    :return: Result tuple with 'valid' status and metadata.
    """
    return "valid", {
        "messages": messages,
        "count": count,
        "grouped": grouped,
        "info_message": None,
        "filters": filters,
        "cleared": False,
    }


def _result_invalid(filters: MessageFilters, msg: str) -> tuple[str, dict]:
    """
    Return an empty result for invalid filters.

    Includes the validation error message for user feedback.

    :param filters: Filters that failed validation.
    :param msg: Error message to display.
    :return: Result tuple with 'invalid' status and metadata.
    """
    return "invalid", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": msg,
        "filters": filters,
        "cleared": False,
    }


def _result_cleared(filters: MessageFilters) -> tuple[str, dict]:
    """
    Return an empty result for cleared filters.

    Indicates no input was provided by the user.

    :param filters: Filters that were cleared.
    :return: Result tuple with 'cleared' status and metadata.
    """
    msg = TranslatableMsg(
        "Use the search bar or date filters above to find messages."
    ).ui
    return "cleared", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": msg,
        "filters": filters,
        "cleared": True,
    }


def _result_error(
    filters: MessageFilters,
    error: Exception
) -> tuple[str, dict]:
    """
    Return an error result when database query fails.

    Includes the error message for display.

    :param filters: Filters used in the failed query.
    :param error: Exception raised during execution.
    :return: Result tuple with 'error' status and metadata.
    """
    msg = TranslatableMsg(f"Database error: {error}").ui
    return "error", {
        "messages": [],
        "count": 0,
        "grouped": {},
        "info_message": msg,
        "filters": filters,
        "cleared": False,
    }
