"""
Filtering utilities for message search in Arcanum application.

Handles:
- normalization of raw request parameters into MessageFilters,
- validation of filter combinations and logical consistency,
- structured logging for debugging and diagnostics.
"""

import logging
from typing import Optional, Tuple

from app.utils.time_utils import parse_date
from app.models.filters import MessageFilters

logger = logging.getLogger(__name__)


def normalize_filters(
    action: Optional[str],
    query: Optional[str],
    mode: Optional[str],
    start: Optional[str],
    end: Optional[str]
) -> MessageFilters:
    """
    Create and normalize a MessageFilters object from raw input.

    Performs trimming, blank-to-None coercion, and applies defaults.
    Logs the normalized values for diagnostics.

    :param action: Requested action ('search' or 'filter').
    :type action: Optional[str]
    :param query: Search query string.
    :type query: Optional[str]
    :param mode: Date filter mode ('on', 'before', 'after', 'between').
    :type mode: Optional[str]
    :param start: Start date (YYYY-MM-DD).
    :type start: Optional[str]
    :param end: End date (YYYY-MM-DD).
    :type end: Optional[str]
    :return: Normalized MessageFilters instance.
    :rtype: MessageFilters
    """
    filters = MessageFilters(
        action=action,
        query=query,
        date_mode=mode or "on",
        start_date=start,
        end_date=end
    )
    filters.normalize(verbose=True)
    return filters


def _validate_search_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a search query string.

    :param query: Search query string.
    :type query: str
    :return: Tuple (is_valid, error_message).
    :rtype: Tuple[bool, Optional[str]]
    """
    if not query:
        message = "Please enter a search query or select a date filter."
        logger.warning("[FILTERS|VALIDATE] Search failed: %s", message)
        return False, message

    logger.debug("[FILTERS|VALIDATE] Search passed | query='%s'.", query)
    return True, None


def _validate_filter_dates(
    mode: str,
    start: str,
    end: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate date-based filtering parameters.

    Checks for required start/end dates, logical date ranges,
    and correct formats.

    :param mode: Date filter mode ('on', 'before', 'after', 'between').
    :type mode: str
    :param start: Start date string (YYYY-MM-DD).
    :type start: str
    :param end: End date string (YYYY-MM-DD).
    :type end: str
    :return: Tuple (is_valid, error_message).
    :rtype: Tuple[bool, Optional[str]]
    """
    if not start and not end:
        message = "Please provide a valid start date."
        logger.warning("[FILTERS|VALIDATE] Filter failed: %s", message)
        return False, message

    message = None

    if mode == "between":
        if not start and not end:
            message = "Please provide both start and end dates."
        elif not start:
            message = "Start date is required."
        elif not end:
            message = "End date is required."
        elif parse_date(start) and parse_date(end):
            if start > end:
                message = "Start date must be before or equal to end date."
        else:
            message = "Invalid date format provided."
    else:
        if not start:
            message = "Please provide a valid start date."
        elif not parse_date(start):
            message = "Invalid start date format."

    is_valid = message is None

    if is_valid:
        logger.debug(
            "[FILTERS|VALIDATE] Filter passed | mode=%s | start=%s | end=%s",
            mode, start, end
        )
    else:
        logger.warning("[FILTERS|VALIDATE] Filter failed: %s", message)

    return is_valid, message


def validate_search_filters(
    filters: MessageFilters
) -> Tuple[bool, Optional[str]]:
    """
    Validate a MessageFilters instance for logical consistency.

    Ensures that required fields are present based on the selected action
    and date_mode. Returns a boolean flag and optional error message.

    :param filters: Normalized MessageFilters instance.
    :type filters: MessageFilters
    :return: Tuple (is_valid, error_message).
    :rtype: Tuple[bool, Optional[str]]
    """
    if not filters.action:
        logger.debug(
            "[FILTERS|VALIDATE] No action specified, skipping validation."
        )
        return True, None

    if filters.action == "search":
        return _validate_search_query(filters.query)

    if filters.action == "filter":
        return _validate_filter_dates(
            filters.date_mode, filters.start_date or "", filters.end_date or ""
        )

    logger.warning("[FILTERS|VALIDATE] Unknown action '%s'.", filters.action)
    return False, "Please enter a search query or select a date filter."
