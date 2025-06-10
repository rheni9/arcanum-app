"""
Search routes for the Arcanum application.

Handles global and per-chat search and filter for messages.
Supports AJAX updates and grouped results for UI.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request, redirect, flash, url_for
)
from app.models.filters import MessageFilters
from app.services.filters_service import resolve_message_query

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
        flash("Database error occurred. Please try again.", "error")
        return render_template("error.html", message=str(e))

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

    _log_search_outcome(status, filters, context)

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


def _log_search_outcome(
    status: str,
    filters: MessageFilters,
    context: dict
) -> None:
    if status == "cleared":
        logger.info(
            "[SEARCH|ROUTER] Filters cleared — no operation performed."
        )
    elif status == "invalid":
        logger.warning(
            "[SEARCH|ROUTER] Invalid filter input — no search performed."
        )
    elif status == "error":
        logger.error(
            "[SEARCH|ROUTER] Query failed: %s", context.get("info_message")
        )
    elif status == "valid":
        scope = (
            f"Chat '{filters.chat_slug}', " if filters.chat_slug else "Global "
        )
        logger.info(
            "[SEARCH|ROUTER] %ssearch: %d message(s), filters: %s",
            scope, context["count"], filters.to_dict()
        )


def _render_ajax_response(
    chat_slug: str | None,
    context: dict,
    sort_by: str,
    order: str
) -> str:
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
                chat_name="Unknown",
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
