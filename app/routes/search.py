"""
Search routes for the Arcanum application.

Provides global search and filtering of chat messages.
Supports queries, date filters, grouped results, sorting,
and AJAX updates.
"""

import logging
from sqlite3 import DatabaseError
from flask import Blueprint, render_template, request

from app.models.filters import MessageFilters
from app.services.filters_service import resolve_search_action
from app.utils.messages_utils import group_messages_by_chat
from app.utils.filters_utils import normalize_filters
from app.utils.sort_utils import get_sort_order

search_bp = Blueprint("search", __name__)
logger = logging.getLogger(__name__)


def _log_search_summary(filters: MessageFilters, total: int) -> None:
    """
    Log a summary of the search or filter operation.

    :param filters: Applied search or filter parameters.
    :type filters: MessageFilters
    :param total: Total number of retrieved messages.
    :type total: int
    """
    if filters.action == "search":
        logger.info(
            "[SEARCH|QUERY] Retrieved %d result(s) for '%s'.",
            total, filters.query
        )
    elif filters.action == "filter":
        mode = filters.date_mode
        start = filters.start_date
        end = filters.end_date
        range_desc = (
            f"from {start} to {end}" if mode == "between" and end else start
        )
        logger.info(
            "[SEARCH|FILTER] Retrieved %d result(s) | mode=%s (%s).",
            total, mode, range_desc
        )


def _render_ajax_response(
    chat_slug: str,
    grouped: dict[str, dict],
    sort_by: str,
    order: str
) -> str:
    """
    Render AJAX fragment with updated messages for a single chat.

    :param chat_slug: Target chat slug.
    :type chat_slug: str
    :param grouped: Messages grouped by chat slug.
    :type grouped: dict[str, dict]
    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :returns: Rendered HTML fragment.
    :rtype: str
    """
    chat_data = grouped.get(chat_slug)
    if not chat_data:
        logger.warning("[SEARCH|AJAX] No data found for chat '%s'.", chat_slug)
        return ""

    logger.debug(
        "[SEARCH|AJAX] Updated chat '%s' | sorted by %s %s.",
        chat_slug, sort_by, order
    )
    return render_template(
        "search/_grouped_msg_table.html",
        slug=chat_slug,
        messages=chat_data["messages"],
        chat_name=chat_data["chat_name"],
        sort_by=sort_by,
        order=order
    )


def _render_full_results_page(
    grouped: dict[str, dict],
    filters: MessageFilters,
    sort_by: str,
    order: str,
    info_message: str | None
) -> str:
    """
    Render full search/filter results page with grouped messages.

    :param grouped: Messages grouped by chat slug.
    :type grouped: dict[str, dict]
    :param filters: Applied search or filter parameters.
    :type filters: MessageFilters
    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :param info_message: Optional informational message.
    :type info_message: str | None
    :returns: Rendered results page.
    :rtype: str
    """
    total = sum(len(data["messages"]) for data in grouped.values())

    logger.info(
        "[SEARCH|RESULTS] Displayed %d message(s) sorted by %s %s.",
        total, sort_by, order
    )
    return render_template(
        "search/results.html",
        results=grouped,
        query=filters.query,
        date_mode=filters.date_mode,
        start_date=filters.start_date,
        end_date=filters.end_date,
        sort_by=sort_by,
        order=order,
        total_messages=total,
        info_message=info_message
    )


@search_bp.route("/search")
def search_messages() -> str:
    """
    Handle global search and filter requests for messages.

    Processes query parameters, retrieves matching messages,
    and returns either an AJAX fragment or a full results page.

    :returns: Rendered HTML response.
    :rtype: str
    :raises DatabaseError: On database retrieval failure.
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"timestamp", "msg_id", "text"},
        default_field="timestamp",
        default_order="desc"
    )

    filters = normalize_filters(
        action=request.args.get("action"),
        query=request.args.get("query"),
        mode=request.args.get("date_mode"),
        start=request.args.get("start_date"),
        end=request.args.get("end_date")
    )
    logger.debug(
        "[SEARCH|FILTERS] Using action='%s' | query='%s' "
        "| mode='%s' | start='%s' | end='%s'",
        filters.action, filters.query, filters.date_mode,
        filters.start_date, filters.end_date
    )

    chat_slug = request.args.get("chat")

    try:
        messages, info_message, filters = resolve_search_action(
            filters=filters,
            sort_by=sort_by,
            order=order,
            chat_slug=chat_slug
        )
    except DatabaseError as e:
        logger.error("[DATABASE|SEARCH] Retrieval failed: %s", e)
        return render_template("error.html", message=f"Database error: {e}")

    _log_search_summary(filters, len(messages))

    grouped = group_messages_by_chat(messages)
    logger.debug("[SEARCH|GROUP] Prepared %d grouped block(s).", len(grouped))

    if (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and chat_slug
    ):
        return _render_ajax_response(chat_slug, grouped, sort_by, order)

    return _render_full_results_page(
        grouped, filters, sort_by, order, info_message
    )
