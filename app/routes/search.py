"""
Search/filter routes for the Arcanum application.

Provides endpoints for global and per-chat message search.
Supports filtering by text, tags, and date ranges, with full-page
or AJAX rendering of grouped results.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request, redirect, flash, url_for
)
from flask_babel import _

from app.models.filters import MessageFilters
from app.services.filters_service import resolve_message_query
from app.logs.search_logs import log_search_outcome

search_bp = Blueprint("search", __name__, url_prefix="/search")
logger = logging.getLogger(__name__)


@search_bp.route("/", methods=["GET"])
def global_search() -> str:
    """
    Handle global or per-chat message search/filter request.

    Processes filters from query parameters, executes the resolved
    query, and renders the result (AJAX or full page).

    :return: Rendered HTML response.
    """
    logger.debug("[FILTERS|DEBUG] Args received: %s", dict(request.args))
    filters = MessageFilters.from_request(request)
    sort_by = request.args.get("sort", "timestamp")
    order = request.args.get("order", "desc")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    try:
        status, context = resolve_message_query(filters, sort_by, order)
    except DatabaseError as e:
        logger.error("[SEARCH|DATABASE] Query failed: %s", e)
        flash(_("Database error occurred. Please try again."), "error")
        return render_template(
            "error.html", message=_("Database error: %(err)s", err=e)
        )

    if request.args.get("action") == "search" and filters.action == "tag":
        new_args = request.args.to_dict(flat=True)
        new_args.pop("query", None)
        new_args["action"] = "tag"
        new_args["tag"] = filters.tag
        return redirect(url_for("search.global_search", **new_args))

    if "tag" in request.args and not filters.tag:
        clean_args = request.args.to_dict(flat=True)
        clean_args.pop("tag", None)
        return redirect(url_for("search.global_search", **clean_args))

    log_search_outcome(status, filters, context)

    if is_ajax:
        return _render_ajax_response(
            filters.chat_slug, context, sort_by, order
        )

    context.update({
        "filters": filters,
        "sort_by": sort_by,
        "order": order,
        "has_filters": filters.has_active(),
        "search_action": url_for("search.global_search"),
        "clear_url": url_for("search.global_search"),
        "chat_slug": None,
    })

    return render_template("search/results.html", **context)


def _render_ajax_response(
    chat_slug: str | None,
    context: dict,
    sort_by: str,
    order: str
) -> str:
    """
    Render a grouped message result table for AJAX requests.

    If a specific chat slug is provided, renders only its message table.
    Otherwise, renders all grouped results across chats.

    :param chat_slug: Optional slug of a single chat to render.
    :param context: Dictionary with grouped message data and filters.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: Rendered HTML fragment with table content.
    """
    grouped = context["grouped"]
    filters = context["filters"]

    if chat_slug:
        chat_data = grouped.get(chat_slug)
        if not chat_data:
            logger.warning("[SEARCH|AJAX] No data for chat '%s'.", chat_slug)
            return render_template(
                "search/_grouped_msg_table.html",
                slug=chat_slug,
                messages=[],
                chat_name=_("Unknown"),
                sort_by=sort_by,
                order=order,
                filters=filters,
            )
        return render_template(
            "search/_grouped_msg_table.html",
            slug=chat_slug,
            messages=chat_data["messages"],
            chat_name=chat_data["chat_name"],
            sort_by=sort_by,
            order=order,
            filters=filters,
        )
    return render_template(
        "search/_results_table.html",
        grouped=grouped,
        sort_by=sort_by,
        order=order,
        filters=filters,
    )
