"""
Time utilities for the Arcanum application.

Provides conversion between naive and timezone-aware datetime formats,
parsing flexible user input to UTC ISO strings, and formatting
timestamps and dates for UI display with consistent error handling.
"""

import logging
from datetime import datetime, time, date, timezone as dt_timezone
from dateutil import parser as dateutil_parser
from dateutil.parser import isoparse
from pytz import timezone as PytzTimeZone
from pytz.tzinfo import BaseTzInfo

DEFAULT_TZ = PytzTimeZone("Europe/Kyiv")  # Default UI timezone

logger = logging.getLogger(__name__)


def _format_day(dt: date) -> str:
    """
    Format a date without leading zero in the day.

    :param dt: Date to format.
    :return: Formatted string.
    """
    return f"{dt.day} {dt.strftime('%B %Y')}"


def _format_datetime(dt: datetime, format_type: str) -> str:
    """
    Format datetime object into a UI string based on format_type.

    :param dt: Datetime object to format.
    :param format_type: Format style keyword.
    :return: Formatted string.
    """
    format_map = {
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "long_date": _format_day(dt.date()),
        "long_date_time": (
            f"{_format_day(dt.date())} {dt.strftime('%H:%M:%S')}"
        ),
        "time": dt.strftime("%H:%M:%S")
    }
    if format_type not in format_map:
        logger.warning("[TIME|FORMAT] Unknown format type '%s'.", format_type)
        return dt.isoformat()
    return format_map[format_type]


def _parse_ymd_string(text: str) -> date | None:
    """
    Parse 'YYYY-MM-DD' string to a date object.

    :param text: Date string.
    :return: Parsed date or None.
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(
            "[DATE|PARSE] Failed to parse YMD string '%s': %s", text, e
        )
        return None


def to_utc_iso(dt: datetime) -> str:
    """
    Convert the datetime object to UTC ISO 8601 string.

    :param dt: Timezone-aware datetime object.
    :return: ISO 8601 string in UTC.
    """
    if dt.tzinfo is None:
        logger.warning(
            "[TIME|CONVERT] Naive datetime received; localized to '%s'.",
            DEFAULT_TZ.zone
        )
        dt = DEFAULT_TZ.localize(dt)
    dt_utc = dt.astimezone(dt_timezone.utc)
    return dt_utc.isoformat().replace('+00:00', 'Z')


def from_utc_iso(
    str_utc: str,
    target_tz: str | BaseTzInfo = DEFAULT_TZ
) -> datetime:
    """
    Convert the UTC ISO 8601 string into a localized datetime object.

    :param str_utc: UTC ISO datetime string.
    :param target_tz: Target timezone (name or timezone object).
    :return: Localized datetime object.
    :raises ValueError: If input is naive (no timezone info).
    """
    dt_utc = isoparse(str_utc)
    if dt_utc.tzinfo is None:
        logger.error(
            "[TIME|PARSE] Naive datetime string '%s' in from_utc_iso.",
            str_utc
        )
        raise ValueError("UTC datetime string must be timezone-aware.")
    if isinstance(target_tz, str):
        target_tz = PytzTimeZone(target_tz)
    return dt_utc.astimezone(target_tz)


def parse_datetime(
    text: str,
    default_tz: BaseTzInfo = DEFAULT_TZ,
    day_first: bool = True,
) -> str | None:
    """
    Parse the flexible datetime input into UTC ISO 8601 string.

    Tries to parse exact ISO format first, then falls back to
    flexible parsing. Naive inputs are localized to the provided
    default timezone.

    :param text: User-provided datetime string.
    :param default_tz: Default timezone for naive inputs.
    :param day_first: Interpret ambiguous dates as DD/MM/YYYY.
    :return: UTC ISO string or None if parsing fails.
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


def parse_flexible_date(
    text: str,
    day_first: bool = True
) -> tuple[date | None, str | None]:
    """
    Parse a user-provided date string into a valid date object.

    Accepts flexible formats like '31.04.2025' or '2025/04/30'.
    Returns a date or an error message.

    :param text: User-provided date string.
    :param day_first: Interpret ambiguous formats as DD/MM/YYYY.
    :return: Tuple (date or None, error message or None).
    """
    cleaned = text.strip().replace(".", "-").replace("/", "-")
    try:
        dt = dateutil_parser.parse(cleaned, dayfirst=day_first)
        return dt.date(), None
    except (ValueError, TypeError) as e:
        logger.warning(
            "[DATE|PARSE] Failed to parse local date '%s': %s", text, e
        )
        msg = str(e)
        if "day is out of range" in msg or "does not match format" in msg:
            return None, "This date does not exist."
        if "month must be in 1..12" in msg:
            return None, "Month must be between 1 and 12."
        if "year" in msg and "is out of range" in msg:
            return None, "Year is out of acceptable range."
        if "Unknown string format" in msg:
            return None, "Unrecognized date format."
        return None, "Invalid date."


def parse_flexible_time(text: str) -> tuple[time | None, str | None]:
    """
    Parse user-entered time string into time object.

    Accepts formats like '15:30', '3:30 PM', '23:00:00'.

    :param text: Input time string.
    :return: Tuple (parsed time or None, error message or None).
    """
    try:
        dt = dateutil_parser.parse(text)
        return dt.time(), None
    except (ValueError, TypeError) as e:
        msg = str(e)
        if (
            "hour must be in" in msg or
            "minute must be in" in msg or
            "second must be in" in msg
        ):
            return None, "Time values are out of valid range."
        return None, "Invalid time format."


def parse_date(text: str) -> str | None:
    """
    Parse a date string in 'YYYY-MM-DD' format into ISO date.

    :param text: Date string.
    :return: ISO date string or None if invalid.
    """
    dt = _parse_ymd_string(text)
    return dt.isoformat() if dt else None


def parse_to_datetime(val: str | datetime | None) -> datetime | None:
    """
    Parse a timestamp into a UTC-aware datetime object.

    Accepts a datetime or ISO 8601 string. Localizes naive input.

    :param val: Input datetime or ISO string.
    :return: UTC datetime or None.
    """
    if isinstance(val, datetime):
        return (
            val.astimezone(dt_timezone.utc)
            if val.tzinfo
            else val.replace(tzinfo=dt_timezone.utc)
        )
    if isinstance(val, str):
        val = val.strip()
        if val:
            try:
                return from_utc_iso(val, "UTC")
            except (ValueError, TypeError) as e:
                logger.warning(
                    "[TIME|PARSE] Failed to parse timestamp '%s': %s", val, e
                )
    return None


def parse_to_date(val: date | datetime | str | None) -> date | None:
    """
    Parse a date-like value to a datetime.date object.

    Accepts a date, datetime, or ISO string.
    Returns a valid date object or None if conversion fails.

    :param val: Input date, datetime, or string.
    :return: Parsed date object or None.
    """
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, str):
        val = val.strip()
        if val:
            # fallback #1: exact YMD (e.g. '2024-06-17')
            dt = _parse_ymd_string(val)
            if dt:
                return dt
            # fallback #2: ISO string with T (e.g. '2024-06-17T00:00:00Z')
            try:
                return date.fromisoformat(val.split("T")[0])
            except (ValueError, TypeError) as e:
                logger.warning(
                    "[TIME|PARSE] Failed to parse date string '%s': %s", val, e
                )
                # fallback #3: flexible parsing (e.g. '31.04.2024')
                dt, err = parse_flexible_date(val)
                if err:
                    logger.warning(
                        "[TIME|PARSE] Failed to parse date '%s': %s", val, err
                    )
                return dt if not err else None
    return None


def datetimeformat(
    value: str | datetime | date | None,
    format_type: str = "datetime",
    tz: str | BaseTzInfo = DEFAULT_TZ
) -> str:
    """
    Format a datetime/date/string for UI display.

    Tries to parse strings as ISO, localizes datetimes,
    and applies a predefined formatting style.

    :param value: Datetime, date, or ISO string to format.
    :param format_type: Format style (e.g., "long_date_time").
    :param tz: Target timezone (name or tz object).
    :return: Human-readable string.
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
            d = _parse_ymd_string(value)
            if d:
                dt = datetime.combine(d, time.min)
            else:
                return value
    else:
        return str(value)

    # Ensure dt is in the right timezone
    if dt.tzinfo is None:
        logger.warning(
            "[TIME|FORMAT] Naive datetime formatted; localized to '%s'.",
            DEFAULT_TZ.zone
        )
        dt = DEFAULT_TZ.localize(dt)
    else:
        dt = dt.astimezone(DEFAULT_TZ)

    return _format_datetime(dt, format_type)


def dateonlyformat(
    value: str | date | datetime,
    format_type: str = "long_date"
) -> str:
    """
    Format a date (string, date, or datetime) for UI display.

    Accepts multiple input types and formats accordingly.

    :param value: Date string or date/datetime object.
    :param format_type: Format style: "long_date" or "short_date".
    :return: Formatted date string.
    """
    if not value:
        return ""

    dt = None
    if isinstance(value, date) and not isinstance(value, datetime):
        dt = value
    elif isinstance(value, datetime):
        dt = value.date()
    elif isinstance(value, str):
        d = _parse_ymd_string(value)
        dt = d if d else None
        if not dt:
            return value
    else:
        return str(value)

    format_map = {
        "long_date": _format_day(dt),
        "short_date": dt.strftime("%d.%m.%Y"),
    }

    result = format_map.get(format_type)
    if result:
        return result

    logger.warning("[DATE|FORMAT] Unknown format type '%s'.", format_type)
    return dt.isoformat()
