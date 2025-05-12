"""
Utilities for processing and validating message search/filter input.

Includes:
- normalization of raw query parameters (stripping, coercing to None)
- validation of combinations (e.g. start before end, required fields)
"""

import logging
from typing import Optional
from app.utils.time_utils import parse_date

logger = logging.getLogger(__name__)


def normalize_filters(
    query: Optional[str],
    date_mode: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> dict[str, Optional[str]]:
    """
    Normalize filter inputs: strip whitespace and convert blanks to None.

    :param query: Raw search query string.
    :type query: str
    :param date_mode: Selected date filter mode.
    :type date_mode: str
    :param start_date: Start date (YYYY-MM-DD).
    :type start_date: str
    :param end_date: End date (YYYY-MM-DD).
    :type end_date: str
    :return: Normalized dictionary of filters.
    :rtype: dict[str, Optional[str]]
    """
    return {
        "query": query.strip() or None if query else None,
        "date_mode": date_mode or "on",
        "start_date": start_date.strip() or None if start_date else None,
        "end_date": end_date.strip() or None if end_date else None,
    }


def validate_search_filters(
    action: Optional[str],
    query: Optional[str],
    mode: Optional[str],
    start: Optional[str],
    end: Optional[str]
) -> tuple[bool, Optional[str]]:
    """
    Validate search/filter input parameters.

    Ensures required values are present and logically consistent,
    depending on the selected action and filter mode.

    :param action: Requested action ("search" or "filter").
    :type action: Optional[str]
    :param query: Full-text query string.
    :type query: Optional[str]
    :param mode: Date mode ("on", "before", "after", "between").
    :type mode: Optional[str]
    :param start: Start date in YYYY-MM-DD format.
    :type start: Optional[str]
    :param end: End date in YYYY-MM-DD format.
    :type end: Optional[str]
    :return: Tuple of (is_valid, error_message).
    :rtype: tuple[bool, Optional[str]]
    """
    query = (query or "").strip()
    mode = (mode or "").strip()
    start = (start or "").strip()
    end = (end or "").strip()

    message = None

    if action == "search":
        if not query:
            message = "Please enter a search query or select a date filter."

    elif action == "filter":
        if not start and not end:
            message = "Please provide a valid start date."
        elif mode == "between":
            if not start and not end:
                message = "Please provide both start and end dates."
            elif not start:
                message = "Start date is required."
            elif not end:
                message = "End date is required."
            elif parse_date(start) and parse_date(end):
                if start > end:
                    message = (
                        "Start date must be before or equal to end date."
                    )
            else:
                message = "Invalid date format provided."

    else:
        message = "Please enter a search query or select a date filter."

    is_valid = message is None

    if is_valid:
        logger.info(
            "[FILTERS] Validation passed | action=%s | mode=%s "
            "| start=%s | end=%s",
            action, mode, start, end
        )
    else:
        logger.warning("[FILTERS] Validation failed: %s", message)

    return is_valid, message
