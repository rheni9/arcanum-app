"""
Datetime utilities for the Arcanum App (chat data context).

Handles:
- parsing user-provided dates/times to UTC ISO strings,
- timezone conversions for chat messages,
- formatting timestamps for display,
- consistent logging of fallbacks and parse issues.
"""

import logging
from typing import Union, Optional
from datetime import datetime, time, timezone as dt_timezone
from dateutil import parser as dateutil_parser
from dateutil.parser import isoparse
from pytz import timezone as PytzTimeZone
from pytz.tzinfo import BaseTzInfo

DEFAULT_TZ = PytzTimeZone("Europe/Kyiv")

logger = logging.getLogger(__name__)


def to_utc_iso(dt: datetime) -> str:
    """
    Convert a datetime object to UTC ISO 8601 string.

    :param dt: A timezone-aware datetime object.
    :type dt: datetime
    :return: ISO 8601 string in UTC (e.g., '2025-05-07T14:00:00Z').
    :rtype: str
    """
    if dt.tzinfo is None:
        logger.warning(
            "[TIME|CONVERT] Naive datetime received; localized to DEFAULT_TZ."
        )
        dt = DEFAULT_TZ.localize(dt)
    return dt.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')


def from_utc_iso(
    utc_str: str,
    target_tz: Union[str, BaseTzInfo] = DEFAULT_TZ
) -> datetime:
    """
    Convert a UTC ISO 8601 string into a localized datetime object.

    :param utc_str: ISO 8601 UTC datetime string.
    :type utc_str: str
    :param target_tz: Target timezone (name or timezone object).
    :type target_tz: Union[str, pytz.BaseTzInfo]
    :return: Localized datetime object.
    :rtype: datetime
    :raises ValueError: If input is naive (no timezone info).
    """
    utc_dt = isoparse(utc_str)
    if utc_dt.tzinfo is None:
        logger.error(
            "[TIME|PARSE] Naive datetime string '%s' in from_utc_iso.",
            utc_str
        )
        raise ValueError("UTC datetime string must be timezone-aware.")
    if isinstance(target_tz, str):
        target_tz = PytzTimeZone(target_tz)

    return utc_dt.astimezone(target_tz)


def parse_datetime(
    text: str,
    default_tz: BaseTzInfo = DEFAULT_TZ,
    day_first: bool = True,
) -> Optional[str]:
    """
    Parse flexible datetime input into UTC ISO 8601 string.

    Accepts ISO, natural language, ambiguous formats.
    Defaults time to 00:00 if not provided.

    :param text: User-provided datetime string.
    :type text: str
    :param default_tz: Default timezone for naive inputs.
    :type default_tz: pytz.BaseTzInfo
    :param day_first: Interpret ambiguous dates as DD/MM/YYYY.
    :type day_first: bool
    :return: UTC ISO 8601 string or None if parsing fails.
    :rtype: Optional[str]
    """
    text = text.strip()

    try:
        dt = isoparse(text)
        if dt.tzinfo is None:
            dt = default_tz.localize(dt)
        return to_utc_iso(dt)
    except ValueError:
        pass  # Not ISO format - fallback to flexible parsing

    try:
        dt = dateutil_parser.parse(text, dayfirst=day_first)
        if dt.tzinfo is None:
            dt = default_tz.localize(dt)
        if dt.time() == time(0, 0):
            return f"{dt.date().isoformat()}T00:00:00Z"
        return to_utc_iso(dt)
    except ValueError as e:
        logger.warning("[TIME|PARSE] Failed to parse '%s': %s", text, e)
        return None


def parse_date(text: str) -> Optional[str]:
    """
    Parse 'YYYY-MM-DD' string into ISO date.

    :param text: Date string.
    :type text: str
    :return: ISO date string or None if invalid.
    :rtype: Optional[str]
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning("[DATE|PARSE] Failed to parse '%s': %s", text, e)
        return None


def datetimeformat(
    value: str,
    format_type: str = "datetime",
    tz: Union[str, BaseTzInfo] = DEFAULT_TZ
) -> str:
    """
    Format a UTC ISO datetime string for UI display.

    :param value: UTC ISO 8601 datetime string.
    :type value: str
    :param format_type: Format style: "datetime", "long_date", or "time".
    :type format_type: str
    :param tz: Target timezone (name or tz object).
    :type tz: Union[str, pytz.BaseTzInfo]
    :return: Human-readable string.
    :rtype: str
    """
    try:
        dt = from_utc_iso(value, tz)
    except (ValueError, TypeError):
        return value  # Return original if parsing fails

    if format_type == "datetime":
        return dt.strftime("%Y-%m-%d %H:%M")
    if format_type == "long_date":
        return dt.strftime("%d %B %Y")
    if format_type == "time":
        return dt.strftime("%H:%M")

    logger.warning("[TIME|FORMAT] Unknown format type '%s'.", format_type)
    return dt.isoformat()


def dateonlyformat(
    value: str,
    format_type: str = "long_date"
) -> str:
    """
    Format a 'YYYY-MM-DD' date string for UI display.

    :param value: Date string.
    :type value: str
    :param format_type: Format style: "long_date" or "short_date".
    :type format_type: str
    :return: Formatted date string.
    :rtype: str
    """
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return value

    if format_type == "long_date":
        return dt.strftime("%-d %B %Y")
    if format_type == "short_date":
        return dt.strftime("%d.%m.%Y")

    logger.warning("[DATE|FORMAT] Unknown format type '%s'.", format_type)
    return dt.isoformat()
