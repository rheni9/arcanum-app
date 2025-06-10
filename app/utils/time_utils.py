"""
Provides datetime utilities for the Arcanum application.

Supports parsing user-provided dates and times to UTC ISO strings,
converting timezones for chat messages, formatting timestamps for UI
display, and consistent logging of fallbacks and parse issues.
"""

import logging
from datetime import datetime, time, date, timezone as dt_timezone
from dateutil import parser as dateutil_parser
from dateutil.parser import isoparse
from pytz import timezone as PytzTimeZone
from pytz.tzinfo import BaseTzInfo

DEFAULT_TZ = PytzTimeZone("Europe/Kyiv")

logger = logging.getLogger(__name__)


def to_utc_iso(dt: datetime) -> str:
    """
    Convert the datetime object to UTC ISO 8601 string.

    :param dt: Timezone-aware datetime object.
    :type dt: datetime
    :return: ISO 8601 string in UTC.
    :rtype: str
    """
    if dt.tzinfo is None:
        logger.warning(
            "[TIME|CONVERT] Naive datetime received; localized to '%s'.",
            DEFAULT_TZ.zone
        )
        dt = DEFAULT_TZ.localize(dt)
    return dt.astimezone(dt_timezone.utc).isoformat().replace('+00:00', 'Z')


def from_utc_iso(
    utc_str: str,
    target_tz: str | BaseTzInfo = DEFAULT_TZ
) -> datetime:
    """
    Convert the UTC ISO 8601 string into a localized datetime object.

    :param utc_str: UTC ISO datetime string.
    :type utc_str: str
    :param target_tz: Target timezone (name or timezone object).
    :type target_tz: str | BaseTzInfo
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
) -> str | None:
    """
    Parse the flexible datetime input into UTC ISO 8601 string.

    :param text: User-provided datetime string.
    :type text: str
    :param default_tz: Default timezone for naive inputs.
    :type default_tz: BaseTzInfo
    :param day_first: Interpret ambiguous dates as DD/MM/YYYY.
    :type day_first: bool
    :return: UTC ISO string or None if parsing fails.
    :rtype: str | None
    """
    text = text.strip()

    try:
        dt = isoparse(text)
        if dt.tzinfo is None:
            dt = default_tz.localize(dt)
        return to_utc_iso(dt)
    except ValueError:
        pass  # Fallback to flexible parsing

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


def parse_date(text: str) -> str | None:
    """
    Parse the 'YYYY-MM-DD' string into ISO date.

    :param text: Date string.
    :type text: str
    :return: ISO date string or None if invalid.
    :rtype: str | None
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date().isoformat()
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning("[DATE|PARSE] Failed to parse '%s': %s", text, e)
        return None


def parse_date_to_dateobject(text: str) -> date | None:
    """
    Parse 'YYYY-MM-DD' string to a datetime.date object.

    :param text: Date string.
    :type text: str
    :return: datetime.date or None if invalid.
    :rtype: date | None
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning("[DATE|PARSE] Failed to parse '%s': %s", text, e)
        return None


def datetimeformat(
    value: str | datetime | date | None,
    format_type: str = "datetime",
    tz: str | BaseTzInfo = DEFAULT_TZ
) -> str:
    """
    Format a datetime/date/string for UI display.

    :param value: Datetime/date/string to format.
    :type value: str | datetime | date | None
    :param format_type: Format style (e.g., "long_date_time").
    :type format_type: str
    :param tz: Target timezone (name or tz object).
    :type tz: str | ZoneInfo
    :return: Human-readable string.
    :rtype: str
    """
    if not value:
        return ""
    dt = None
    # If already datetime
    if isinstance(value, datetime):
        dt = value
    # If date, make it into datetime (midnight)
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    # If string, try to parse as ISO (uses time_utils)
    elif isinstance(value, str):
        try:
            dt = from_utc_iso(value, tz)
        except (ValueError, TypeError):
            # Try fallback to "YYYY-MM-DD"
            try:
                d = datetime.strptime(value, "%Y-%m-%d")
                dt = datetime.combine(d.date(), time.min)
            except (ValueError, TypeError):
                return value
    else:
        return str(value)

    # Ensure dt is in the right timezone
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = DEFAULT_TZ.localize(dt)
        else:
            dt = dt.astimezone(DEFAULT_TZ)

    if format_type == "datetime":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if format_type == "long_date":
        return dt.strftime("%d %B %Y")
    if format_type == "long_date_time":
        return dt.strftime("%d %B %Y %H:%M:%S")
    if format_type == "time":
        return dt.strftime("%H:%M:%S")

    logger.warning("[TIME|FORMAT] Unknown format type '%s'.", format_type)
    return dt.isoformat()


def dateonlyformat(
    value: str | date | datetime,
    format_type: str = "long_date"
) -> str:
    """
    Format a date (string, date, or datetime) for UI display.

    :param value: Date string or date/datetime object.
    :type value: str | date | datetime
    :param format_type: Format style: "long_date" or "short_date".
    :type format_type: str
    :return: Formatted date string.
    :rtype: str
    """
    if not value:
        return ""
    dt = None
    if isinstance(value, date) and not isinstance(value, datetime):
        dt = value
    elif isinstance(value, datetime):
        dt = value.date()
    elif isinstance(value, str):
        try:
            dt = datetime.strptime(value, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return value
    else:
        return str(value)

    if format_type == "long_date":
        return dt.strftime("%-d %B %Y")
    if format_type == "short_date":
        return dt.strftime("%d.%m.%Y")

    logger.warning("[DATE|FORMAT] Unknown format type '%s'.", format_type)
    return dt.isoformat()
