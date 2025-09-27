"""
Filter utilities for the Arcanum application.

Validates and transforms MessageFilters used in search and filtering.
Provides normalization, SQL clause construction, and logging support.
"""

import logging

from app.models.filters import MessageFilters
from app.utils.i18n_utils import TranslatableMsg
from app.utils.time_utils import parse_flexible_date

logger = logging.getLogger(__name__)


def _is_valid_date_mode(mode: str | None) -> bool:
    """
    Check whether the given date mode is valid.

    :param mode: Mode string to check.
    :return: True if mode is one of the allowed date modes.
    """
    return mode in {"on", "before", "after", "between"}


def normalize_filter_action(filters: MessageFilters) -> None:
    """
    Normalize the action field based on the query and date fields.

    Modifies the filters object in-place to ensure consistent behavior
    for search, tag, and date filters.

    :param filters: MessageFilters instance to normalize.
    """

    # Respect explicitly provided action from the client.
    if filters.action in {"search", "tag", "filter"}:
        return

    if filters.is_tag_search():
        filters.action = "tag"
        filters.query = filters.tag
        filters.date_mode = None
        filters.start_date = None
        filters.end_date = None
    elif filters.query:
        filters.action = "search"
        filters.date_mode = None
        filters.start_date = None
        filters.end_date = None
    elif _is_valid_date_mode(filters.date_mode):
        filters.action = "filter"
        filters.query = None
        filters.tag = None
    else:
        filters.action = None


def validate_search_filters(
    filters: MessageFilters
) -> tuple[bool, str | None]:
    """
    Validate the given filters for search and date-based filtering.

    Produces localized user-facing messages via TranslatableMsg.
    All logging remains in English by using the `.log` form.

    :param filters: Normalized MessageFilters instance.
    :return: Tuple of (is_valid, error_message).
    """
    filters.normalize()

    def _validate_search() -> tuple[bool, str | None]:
        # Explicit search mode with an empty query (route-enforced case).
        if (filters.action == "search") and not (
            filters.query and filters.query.strip()
        ):
            msg = TranslatableMsg("Please enter a search query.")
            logger.warning("[FILTERS|VALIDATE] Search failed: %s", msg.log)
            return False, msg.ui

        # Generic case: neither query nor tag present.
        if not (filters.query or filters.tag):
            msg = TranslatableMsg("Please enter a search query or tag.")
            logger.warning("[FILTERS|VALIDATE] Search failed: %s", msg.log)
            return False, msg.ui

        logger.debug(
            "[FILTERS|VALIDATE] Search passed | query='%s'.",
            filters.query
        )
        return True, None

    def _validate_tag() -> tuple[bool, str | None]:
        if not filters.tag:
            msg = TranslatableMsg("Please enter a tag after #.")
            logger.warning("[FILTERS|VALIDATE] Tag search failed: %s", msg.log)
            return False, msg.ui
        logger.debug(
            "[FILTERS|VALIDATE] Tag search passed | tag='%s'.",
            filters.tag
        )
        return True, None

    def _validate_simple_date() -> tuple[bool, str | None]:
        if not filters.start_date:
            msg = TranslatableMsg("Please provide a valid date.")
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg.log)
            return False, msg.ui

        valid, error_msg, date_norm = normalize_date(filters.start_date)
        if not valid:
            msg = TranslatableMsg(
                f"Invalid date: {error_msg or 'Invalid format.'}"
            )
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg.log)
            return False, msg.ui

        filters.start_date = date_norm
        logger.debug(
            "[FILTERS|VALIDATE] Filter passed | mode=%s | start=%s.",
            filters.date_mode, filters.start_date
        )
        return True, None

    def _validate_between_dates() -> tuple[bool, str | None]:
        start = filters.start_date
        end = filters.end_date
        errors: list[TranslatableMsg] = []

        # Presence checks
        if not start and not end:
            errors.append(
                TranslatableMsg("Please provide both start and end dates.")
            )
        elif not start:
            errors.append(TranslatableMsg("Start date is required."))
        elif not end:
            errors.append(TranslatableMsg("End date is required."))

        def _validate_date(
            date_str: str, label: str
        ) -> tuple[bool, str | None, str | None]:
            valid, err, normalized = normalize_date(date_str)
            if not valid:
                msg = TranslatableMsg(
                    f"Invalid {label} date: {err or 'Invalid format.'}"
                )
                return False, msg, None
            return True, None, normalized

        start_norm = end_norm = None

        if not errors:
            valid_start, err_start, start_norm = _validate_date(start, "start")
            if not valid_start and err_start is not None:
                errors.append(err_start)

            valid_end, err_end, end_norm = _validate_date(end, "end")
            if not valid_end and err_end is not None:
                errors.append(err_end)

        if not errors and start_norm > end_norm:
            errors.append(
                TranslatableMsg(
                    "Start date must be before or equal to end date."
                )
            )

        if errors:
            msg_log = "; ".join(m.log for m in errors)
            msg_ui = "; ".join(m.ui for m in errors)
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg_log)
            return False, msg_ui

        filters.start_date = start_norm
        filters.end_date = end_norm

        logger.debug(
            "[FILTERS|VALIDATE] Filter passed | mode=between "
            "| start=%s | end=%s.",
            start_norm, end_norm
        )
        return True, None

    if filters.action == "search":
        return _validate_search()

    if filters.action == "tag":
        return _validate_tag()

    if filters.action == "filter":
        if not _is_valid_date_mode(filters.date_mode):
            msg = TranslatableMsg("Please select a date filter mode.")
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg.log)
            return False, msg.ui
        if filters.date_mode in {"on", "before", "after"}:
            return _validate_simple_date()
        if filters.date_mode == "between":
            return _validate_between_dates()

    # Fallback invalid
    msg = TranslatableMsg(
        "Please enter a search query, tag, or select a date filter."
    )
    logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg.log)
    return False, msg.ui


def build_sql_clause(
    filters: MessageFilters,
    chat_slug: str | None = None,
    dialect: str = "postgres",
) -> tuple[str, dict]:
    """
    Build a SQL WHERE clause and parameter dictionary for SQLAlchemy.

    Generates conditions for Postgres or SQLite depending on the dialect.

    :param filters: MessageFilters instance to extract clauses from.
    :param chat_slug: Optional slug to limit filtering to a specific chat.
    :param dialect: Database dialect (``'postgres'`` or ``'sqlite'``).
    :return: Tuple of (WHERE clause as string, dict of parameters).
    """
    clause: list[str] = []
    params: dict = {}

    def text_expr(field: str, param: str) -> str:
        """
        Generate a case-insensitive LIKE/ILIKE expression
        depending on the active dialect.
        """
        if dialect == "postgres":
            if field == "m.tags":
                return f"{field}::text ILIKE :{param}"
            return f"{field} ILIKE :{param}"
        return f"LOWER({field}) LIKE LOWER(:{param})"

    if chat_slug:
        clause.append("c.slug = :chat_slug")
        params["chat_slug"] = chat_slug

    if filters.action == "search":
        if filters.query and filters.tag:
            clause.append(
                f"({text_expr('m.text', 'query')} "
                f"OR {text_expr('m.tags', 'query')} "
                f"OR {text_expr('m.tags', 'tag')})"
            )
            params["query"] = f"%{filters.query}%"
            params["tag"] = f"%{filters.tag}%"
        elif filters.query:
            clause.append(
                f"({text_expr('m.text', 'query')} "
                f"OR {text_expr('m.tags', 'query')})"
            )
            params["query"] = f"%{filters.query}%"
        elif filters.tag:
            clause.append(text_expr("m.tags", "tag"))
            params["tag"] = f"%{filters.tag}%"

    if filters.action == "tag":
        clause.append(text_expr("m.tags", "tag"))
        params["tag"] = f"%{filters.tag}%"

    if filters.action == "filter":
        date_clause = filters.get_date_clause()
        if date_clause:
            clause.append(date_clause)
            params.update(filters.get_date_params())

    where_sql = "WHERE " + " AND ".join(clause) if clause else ""
    logger.debug(
        "[FILTERS|SQL|%s] %s | params=%s",
        dialect.upper(),
        where_sql or "<no clause>",
        params,
    )
    return where_sql, params


def normalize_date(
    date_str: str | None
) -> tuple[bool, str | None, str | None]:
    """
    Parse and normalize a date string.

    :param date_str: Date string to parse.
    :return: Tuple (is_valid, error_message, iso_date_or_None)
    """
    if not date_str:
        return False, "Empty date string", None

    dt, err = parse_flexible_date(date_str)
    if dt is None or err is not None:
        return False, err, None

    return True, None, dt.isoformat()
