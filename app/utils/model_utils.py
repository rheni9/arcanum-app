"""
Model utilities for the Arcanum application.

Defines reusable helpers for data normalization and conversion,
shared by model classes for chat and message entities.
"""

from typing import Any


def empty_to_none(val: Any) -> Any | None:
    """
    Convert empty string to None.

    Accepts strings, returns None if input is None or an empty string,
    otherwise returns the value as is.

    :param val: Value to check.
    :type val: Any
    :return: None if value is None or empty string, else original value.
    :rtype: Any | None
    """
    if val is None:
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val


def to_int_or_none(val: Any) -> int | None:
    """
    Convert value to integer, or None if conversion is not possible.

    Accepts strings, numbers, or None. Strips whitespace from strings
    before conversion. Returns None on failure.

    :param val: Value to convert.
    :type val: Any
    :return: Integer value or None.
    :rtype: int | None
    """
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
