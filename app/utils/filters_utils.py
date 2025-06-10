"""
Filter and search utilities for the Arcanum application.

Centralizes validation and SQL clause construction. Ensures consistent
usage and logging across search and filter entrypoints.
"""

import logging
from typing import Any

from app.models.filters import MessageFilters
from app.utils.time_utils import parse_date

logger = logging.getLogger(__name__)


def is_valid_date_mode(mode: str | None) -> bool:
    return mode in {"on", "before", "after", "between"}


def normalize_filter_action(filters: MessageFilters) -> None:
    """
    Determine and set the appropriate action for the filters.

    Modifies filters in place:
    - Sets action to 'search' or 'filter' based on input.
    - Clears incompatible fields.
    """
    if filters.action in {"search", "tag", "filter"}:
        return

    if filters.is_tag_search():
        filters.action = "tag"
        filters.query = filters.tag
        filters.date_mode = None
        filters.start_date = None
        filters.end_date = None
    elif filters.query:
        # Text query overrides date filtering
        filters.action = "search"
        filters.date_mode = None
        filters.start_date = None
        filters.end_date = None
    elif (
        is_valid_date_mode(filters.date_mode)
        and (filters.start_date or filters.end_date)
    ):
        # Valid date mode and at least one date provided
        filters.action = "filter"
        filters.query = None
    else:
        # Neither query nor valid date filter: consider invalid
        filters.action = None


def validate_search_filters(
    filters: MessageFilters
) -> tuple[bool, str | None]:
    """
    Validate message filters for search and date-based filtering.

    :param filters: Normalized MessageFilters instance.
    :return: Tuple (is_valid, error_message).
    """
    filters.normalize()

    def _validate_search(query: str | None) -> tuple[bool, str | None]:
        if not (filters.query or filters.tag):
            msg = "Please enter a search query or tag."
            logger.warning("[FILTERS|VALIDATE] Search failed: %s", msg)
            return False, msg
        logger.debug(
            "[FILTERS|VALIDATE] Search passed | query='%s'.", query
        )
        return True, None

    def _validate_tag(tag: str | None) -> tuple[bool, str | None]:
        if not tag:
            msg = "Please specify a tag."
            logger.warning("[FILTERS|VALIDATE] Tag search failed: %s", msg)
            return False, msg
        logger.debug("[FILTERS|VALIDATE] Tag search passed | tag='%s'.", tag)
        return True, None

    def _validate_simple_date(start: str | None) -> tuple[bool, str | None]:
        if not start:
            msg = "Please provide a valid date."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        if not parse_date(start):
            msg = "Invalid start date format."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        logger.debug(
            "[FILTERS|VALIDATE] Filter passed | mode=%s | start=%s.",
            filters.date_mode, start
        )
        return True, None

    def _validate_between_dates(
        start: str | None, end: str | None
    ) -> tuple[bool, str | None]:
        if not start and not end:
            msg = "Please provide both start and end dates."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        if not start:
            msg = "Start date is required."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        if not end:
            msg = "End date is required."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        if not (parse_date(start) and parse_date(end)):
            msg = "Invalid date format provided."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        if start > end:
            msg = "Start date must be before or equal to end date."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", msg)
            return False, msg
        logger.debug(
            "[FILTERS|VALIDATE] Filter passed | mode=between | "
            "start=%s | end=%s.", start, end
        )
        return True, None

    # valid, message = False, None

    if filters.action == "search":
        return _validate_search(filters.query)

    if filters.action == "tag":
        return _validate_tag(filters.tag)

    if filters.action == "filter":
        mode = filters.date_mode
        if not is_valid_date_mode(mode):
            message = "Invalid date filter mode."
            logger.warning("[FILTERS|VALIDATE] Filter failed: %s", message)
            return False, message
        if mode in {"on", "before", "after"}:
            return _validate_simple_date(filters.start_date)
        elif mode == "between":
            return _validate_between_dates(
                filters.start_date, filters.end_date
            )
    return False, "Please enter a search query, tag, or select a date filter."


def build_sql_clause(
    filters: MessageFilters,
    chat_slug: str | None = None
) -> tuple[str, list]:
    """
    Build a SQL WHERE clause and parameters from the given filters.

    :param filters: MessageFilters instance.
    :param chat_slug: If provided, restrict to this chat_slug.
    :return: Tuple (where_clause, params).
    """
    clause = []
    params = []

    if chat_slug:
        clause.append("c.slug = ?")
        params.append(chat_slug)

    if filters.action == "search":
        if filters.query and filters.tag:
            clause.append("(m.text LIKE ? OR m.tags LIKE ? OR m.tags LIKE ?)")
            q_param = f"%{filters.query}%"
            t_param = f"%{filters.tag}%"
            params.extend([q_param, q_param, t_param])
        elif filters.query:
            clause.append("(m.text LIKE ? OR m.tags LIKE ?)")
            q_param = f"%{filters.query}%"
            params.extend([q_param, q_param])
        elif filters.tag:
            clause.append("m.tags LIKE ?")
            params.append(f"%{filters.tag}%")

    if filters.action == "tag":
        clause.append("m.tags LIKE ?")
        params.append(f"%{filters.tag}%")

    if filters.action == "filter":
        date_clause = filters.get_date_clause()
        if date_clause:
            clause.append(date_clause)
            params.extend(filters.get_date_params())

    where_sql = "WHERE " + " AND ".join(clause) if clause else ""
    logger.debug(
        "[FILTERS|SQL] %s | params: %s", where_sql or "<no clause>", params
    )
    return where_sql, params


def group_messages_by_chat(
    messages: list[dict]
) -> dict[str, dict[str, Any]]:
    """
    Group message dicts by chat_slug for global search/filter UI.

    :param messages: List of message dicts with 'chat_slug' and 'chat_name'.
    :return: Dict {chat_slug: {"messages": [...], "chat_name": ...}, ...}
    """
    grouped: dict[str, dict[str, Any]] = {}

    for msg in messages:
        slug = msg.get("chat_slug")
        if not slug:
            continue
        name = msg.get("chat_name", slug)
        if slug not in grouped:
            grouped[slug] = {
                "messages": [],
                "chat_name": name,
            }
        grouped[slug]["messages"].append(msg)

    logger.debug("[FILTERS|GROUP] Grouped %d chat(s)", len(grouped))
    return grouped
