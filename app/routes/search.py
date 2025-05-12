"""
Global search and filtering routes for chat messages.

Enables full-text search and date-based filtering across all chats.
Supports grouped results, sorting, and AJAX updates for partial views.
"""

import logging
from sqlite3 import DatabaseError
from flask import Blueprint, render_template, request

from app.models.filters import MessageFilters
from app.services.filters_service import resolve_search_action
from app.utils.messages_utils import group_messages_by_chat
from app.utils.sort_utils import get_sort_order

search_bp = Blueprint("search", __name__)
logger = logging.getLogger(__name__)


def _log_search_summary(filters: MessageFilters, messages: list[dict]) -> None:
    """
    Log summary information about a search or filter action.

    :param filters: Normalized filters used in the search.
    :type filters: MessageFilters
    :param messages: List of matched messages.
    :type messages: list[dict]
    """
    if filters.action == "search":
        logger.info(
            "[SEARCH] Displayed %d search result(s) for query '%s' "
            "across all chats.", len(messages), filters.query
        )
    elif filters.action == "filter":
        date_range = (
            f"{filters.start_date} to {filters.end_date}"
            if filters.date_mode == "between" and filters.end_date
            else filters.start_date
        )
        logger.info(
            "[FILTER] Displayed %d filtered message(s) across all chats "
            "| mode=%s (%s).", len(messages), filters.date_mode, date_range
        )


def _render_ajax_response(
    chat_slug: str,
    grouped: dict[str, list[dict]],
    sort_by: str,
    order: str
) -> str:
    """
    Render the HTML response for an AJAX update of one chat block.

    :param chat_slug: Slug of the chat to render.
    :type chat_slug: str
    :param grouped: Dictionary of grouped messages per chat.
    :type grouped: dict[str, list[dict]]
    :param sort_by: Field to sort messages by.
    :type sort_by: str
    :param order: Sorting direction.
    :type order: str
    :returns: Rendered HTML of the message table for the chat.
    :rtype: str
    """
    logger.info(
        "[AJAX] Updated grouped messages for chat '%s' sorted by %s %s.",
        chat_slug, sort_by, order
    )
    return render_template(
        "search/_grouped_msg_table.html",
        slug=chat_slug,
        messages=grouped.get(chat_slug, []),
        sort_by=sort_by,
        order=order
    )


def _render_full_results_page(
    grouped: dict[str, list[dict]],
    filters: MessageFilters,
    sort_by: str,
    order: str,
    info_message: str | None
) -> str:
    """
    Render the full grouped results page from a global search or filter.

    :param grouped: Messages grouped by chat slug.
    :type grouped: dict[str, list[dict]]
    :param filters: Normalized filters used in the request.
    :type filters: MessageFilters
    :param sort_by: Sorting field.
    :type sort_by: str
    :param order: Sorting direction.
    :type order: str
    :param info_message: Optional informational banner message.
    :type info_message: str | None
    :returns: Rendered HTML of the full results page.
    :rtype: str
    """
    logger.info(
        "[FULL] Displayed global search results page, sorted by %s %s.",
        sort_by, order
    )
    return render_template("search/results.html", **{
        "results": grouped,
        "query": filters.query,
        "date_mode": filters.date_mode,
        "start_date": filters.start_date,
        "end_date": filters.end_date,
        "sort_by": sort_by,
        "order": order,
        "info_message": info_message,
    })


@search_bp.route("/search")
def search_messages() -> str:
    """
    Display global search results across all chats with optional filters.

    Handles both full-page and AJAX rendering.

    :returns: Rendered HTML page or table fragment.
    :rtype: str
    :raises DatabaseError: If message retrieval from database fails.
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"timestamp", "msg_id", "text"},
        default_field="timestamp",
        default_order="desc"
    )

    filters = MessageFilters(
        action=request.args.get("action"),
        query=request.args.get("query"),
        date_mode=request.args.get("date_mode"),
        start_date=request.args.get("start_date"),
        end_date=request.args.get("end_date")
    )

    try:
        messages, info_message, filters = resolve_search_action(
            filters=filters,
            sort_by=sort_by,
            order=order,
            chat_slug=None
        )
        _log_search_summary(filters, messages)
    except DatabaseError as e:
        logger.error("[DB] Failed to complete global search: %s", e)
        return render_template("error.html", message=f"Database error: {e}")

    grouped = group_messages_by_chat(messages)

    if (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and (chat_slug := request.args.get("chat"))
    ):
        return _render_ajax_response(chat_slug, grouped, sort_by, order)

    return _render_full_results_page(
        grouped, filters, sort_by, order, info_message
    )
