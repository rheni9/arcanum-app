"""
Datetime utilities: parse, normalize, and format UTC-aware date/time values.

Includes tools for:
- parsing flexible date/time input formats into ISO 8601 UTC strings,
- converting between time zones,
- rendering date/time for display in templates,
- structured logging of errors and fallbacks.
"""

import logging
from datetime import datetime, time, timezone as dt_timezone
from dateutil import parser as dateutil_parser
from dateutil.parser import isoparse
from pytz import timezone

DEFAULT_TZ = timezone("Europe/Kyiv")

logger = logging.getLogger(__name__)


def to_utc_iso(dt: datetime) -> str:
    """
    Convert a datetime object to ISO 8601 format in UTC.

    :param dt: A timezone-aware datetime object.
    :type dt: datetime
    :return: UTC datetime as ISO 8601 string (with trailing 'Z').
    :rtype: str
    """
    if dt.tzinfo is None:
        logger.warning(
            "[TIME] Naive datetime received in to_utc_iso. "
            "Defaulting to DEFAULT_TZ."
        )
        dt = DEFAULT_TZ.localize(dt)
    return dt.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')


def from_utc_iso(utc_str: str, target_tz: str = "Europe/Kyiv") -> datetime:
    """
    Convert UTC ISO string into a datetime localized to the target timezone.

    :param utc_str: ISO-formatted datetime string in UTC
                    (e.g. "2025-05-07T14:00:00Z").
    :type utc_str: str
    :param target_tz: Name of the timezone to localize to
                      (default is "Europe/Kyiv").
    :type target_tz: str
    :return: Localized datetime object.
    :rtype: datetime
    :raises ValueError: If input is not timezone-aware.
    """
    utc_dt = isoparse(utc_str)
    if utc_dt.tzinfo is None:
        logger.error(
            "[TIME] Received naive datetime string '%s' in from_utc_iso.",
            utc_str
        )
        raise ValueError("Input datetime must be timezone-aware (UTC).")
    return utc_dt.astimezone(timezone(target_tz))


def parse_datetime(
    text: str,
    default_tz=DEFAULT_TZ,
    day_first: bool = True,
) -> str | None:
    """
    Parse a date/time string into a UTC ISO 8601 string.

    Accepts flexible formats (ISO 8601, natural language, etc.).
    Assumes `00:00` as default time if none is provided.

    :param text: Input date/time string.
    :type text: str
    :param default_tz: Timezone to assume for naive inputs.
    :type default_tz: pytz.timezone
    :param day_first: Whether to interpret ambiguous dates as day-first
                      (e.g., 31/05/2025).
    :type day_first: bool
    :return: UTC datetime as ISO 8601 string, or None if parsing fails.
    :rtype: str | None
    """
    text = text.strip()

    try:
        dt = isoparse(text)
        if dt.tzinfo is None:
            dt = default_tz.localize(dt)
        return to_utc_iso(dt)
    except ValueError:
        # Not ISO format - fall back to flexible parsing
        pass

    try:
        dt = dateutil_parser.parse(text, dayfirst=day_first)

        if dt.time() == time(0, 0):
            return f"{dt.date().isoformat()}T00:00:00Z"

        if dt.tzinfo is None:
            dt = default_tz.localize(dt)
        return to_utc_iso(dt)

    except ValueError as e:
        logger.warning(
            "[TIME] Failed to parse datetime string '%s': %s", text, e
        )
        return None


def parse_date(text: str) -> str | None:
    """
    Parse a date string in 'YYYY-MM-DD' format and return ISO date string.

    :param text: Date string (e.g., "2025-05-07").
    :type text: str
    :return: ISO date string, or None if input is invalid.
    :rtype: str | None
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(
            "[DATE] Failed to parse date string '%s': %s", text, e
        )
        return None


def datetimeformat(
    value: str, format_type: str = "datetime", tz: str = "Europe/Kyiv"
) -> str:
    """
    Format a UTC ISO datetime string for human-readable template display.

    :param value: ISO 8601 UTC datetime string (e.g., "2025-05-07T14:00:00Z").
    :type value: str
    :param format_type: Format style: "datetime", "long_date", or "time".
    :type format_type: str
    :param tz: Timezone name to convert to (default is "Europe/Kyiv").
    :type tz: str
    :return: Formatted datetime string.
             Falls back to ISO if format_type is unknown.
    :rtype: str
    """
    try:
        dt = from_utc_iso(value, tz)
    except (ValueError, TypeError):
        return value  # Return original if parsing fails

    if format_type not in {"datetime", "long_date", "time"}:
        logger.warning(
            "[TIME] Unknown format_type '%s' in datetimeformat.", format_type
        )
        return dt.isoformat()

    if format_type == "long_date":
        return dt.strftime("%d %B %Y")
    if format_type == "time":
        return dt.strftime("%H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")


def dateonlyformat(value: str, format_type: str = "long_date") -> str:
    """
    Format a date string (YYYY-MM-DD) for localized display in templates.

    :param value: Date string in "YYYY-MM-DD" format.
    :type value: str
    :param format_type: "long_date" for full month name (e.g., "7 May 2025"),
                        or "short" for "dd.mm.yyyy".
    :type format_type: str
    :return: Formatted date string.
    :rtype: str
    """
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        return value

    if format_type not in {"long_date", "short"}:
        logger.warning(
            "[DATE] Unknown format_type '%s' in dateonlyformat.", format_type
        )
        return dt.isoformat()

    if format_type == "long_date":
        return dt.strftime("%-d %B %Y")
    if format_type == "short":
        return dt.strftime("%d.%m.%Y")
    return dt.isoformat()
