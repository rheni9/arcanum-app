"""
Model utilities for the Arcanum application.

Provides reusable helpers for data normalization and conversion,
shared by model classes for chat and message entities.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def empty_to_none(val: Any) -> Any | None:
    """
    Convert empty string to None.

    Returns None if the input is None or an empty string;
    otherwise, returns the original value.

    :param val: Value to check.
    :return: Normalized value (None or original).
    """
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    return val


def to_int_or_none(val: Any) -> int | None:
    """
    Convert a value to integer, or return None on failure.

    Accepts strings, numbers, or None. Strips whitespace
    before conversion and handles invalid values gracefully.

    :param val: Value to convert.
    :return: Integer value or None.
    """
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        logger.warning("[MODEL|UTIL] Failed to convert to int: %s", val)
        return None
