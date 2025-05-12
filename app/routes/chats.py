"""
Chat management routes for the Arcanum application.

Provides functionality to list, create, edit, delete, and view chats,
including their messages. Supports AJAX table updates, sorting,
message filtering by query or date, and conflict resolution on save.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, Response, g
)

from app.models.models import Chat
from app.models.filters import MessageFilters
from app.services.chats_service import (
    get_chats, insert_chat, update_chat,
    delete_chat_and_messages, slug_exists
)
from app.services.filters_service import resolve_search_action
from app.services.messages_service import get_chat_data
from app.utils.chats_utils import build_chat_object, validate_chat_form
from app.utils.form_utils import clean_form
from app.utils.slugify_utils import slugify, generate_unique_slug
from app.utils.sort_utils import get_sort_order
from app.utils.decorators import catch_not_found

chats_bp = Blueprint("chats", __name__, url_prefix="/chats")
logger = logging.getLogger(__name__)


@chats_bp.route("/")
def list_chats() -> str:
    """
    Display the list of all chats with optional sorting.

    Handles both full-page and AJAX requests.

    :returns: Rendered HTML of chat list or AJAX table.
    :rtype: str
    :raises DatabaseError: If an error occurs during chat retrieval.
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"name", "message_count", "last_message_at"},
        default_field="last_message_at",
        default_order="desc"
    )

    try:
        chats = get_chats(sort_by, order)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        template = "chats/_chats_table.html" if is_ajax else "chats/index.html"
        log_prefix = "[AJAX]" if is_ajax else "[FULL]"
        logger.info("%s Displayed chat list view sorted by %s %s.",
                    log_prefix, sort_by, order)
        return render_template(
            template, chats=chats, sort_by=sort_by, order=order
        )
    except DatabaseError as e:
        logger.error("[DB] Failed to retrieve chats: %s", e)
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/new")
def new_chat() -> str:
    """
    Render the form for creating a new chat.

    :returns: Rendered HTML of the chat creation form.
    :rtype: str
    """
    return render_template("chats/form.html", chat=None, is_editing=False)


@chats_bp.route("/<slug>/edit")
@catch_not_found
def edit_chat(_slug: str) -> str:
    """
    Render the form for editing an existing chat.

    :param slug: Unique identifier of the chat.
    :type slug: str
    :returns: Rendered HTML of the chat edit form.
    :rtype: str
    """
    return render_template("chats/form.html", chat=g.chat, is_editing=True)


@chats_bp.route("/save", methods=["POST"])
def save_chat() -> Response:
    """
    Save a chat (create or update) based on submitted form data.

    Handles form validation, conflict resolution, and persistence.

    :returns: Redirect on success or rendered form with errors.
    :rtype: Response
    :raises ValueError: If data processing fails.
    :raises DatabaseError: If a database operation fails.
    """
    data = clean_form(request.form.to_dict())

    original_slug = data.get("original_slug")
    action = data.get("action")
    is_editing = bool(original_slug)
    slug = original_slug if is_editing else slugify(data["name"])

    if action == "create_copy":
        slug = generate_unique_slug(
            slug, data["name"] + (data.get("link") or "")
        )
        is_editing = False
    elif action == "overwrite":
        slug = original_slug
        is_editing = True

    validated_fields, errors = validate_chat_form(data)

    if errors:
        return render_template(
            "chats/form.html",
            chat=data,
            errors=errors,
            original_slug=original_slug,
            is_editing=is_editing
        )

    if not is_editing and slug_exists(slug) and not action:
        logger.warning("[CONFLICT] Chat slug already exists: '%s'", slug)
        conflict_chat = build_chat_object(data, slug)
        return render_template(
            "chats/form.html",
            chat=conflict_chat,
            conflict=True,
            is_editing=False
        )

    chat = build_chat_object({**data, **validated_fields}, slug)

    try:
        if is_editing:
            update_chat(chat)
            logger.info("[UPDATE] Chat '%s' has been updated.", chat.slug)
            flash(
                f"Chat '{chat.name}' has been updated successfully.", "success"
            )
        else:
            insert_chat(chat)
            logger.info("[INSERT] New chat '%s' has been created.", chat.slug)
            flash(
                f"New chat '{chat.name}' has been created successfully.",
                "success"
            )
        return redirect(url_for("chats.view_chat", slug=chat.slug))

    except (ValueError, DatabaseError) as e:
        logger.error("[DB] Failed to save chat '%s': %s", chat.slug, e)
        flash(f"Failed to save chat: {e}", "error")
        return render_template(
            "chats/form.html", chat=chat, is_editing=is_editing
        )


def _get_chat_messages_with_filters(
    chat_slug: str,
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> tuple[list[dict], str | None, MessageFilters]:
    """
    Retrieve filtered messages for a given chat and log the results.

    :param chat_slug: Unique slug of the chat.
    :type chat_slug: str
    :param filters: Filters object containing query and date options.
    :type filters: MessageFilters
    :param sort_by: Field to sort messages by ('timestamp', 'msg_id', 'text').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str

    :returns: Tuple of (messages list, info message, normalized filters).
    :rtype: tuple[list[dict], str | None, MessageFilters]
    """
    messages, info_message, filters = resolve_search_action(
        filters=filters,
        sort_by=sort_by,
        order=order,
        chat_slug=chat_slug
    )

    if filters.action == "search":
        logger.info(
            "[SEARCH] Displayed %d search result(s) for query '%s' "
            "in chat '%s'.", len(messages), filters.query, chat_slug
        )
    elif filters.action == "filter":
        date_range = (
            f"{filters.start_date} to {filters.end_date}"
            if filters.date_mode == "between" and filters.end_date
            else filters.start_date
        )
        logger.info(
            "[FILTER] Displayed %d filtered message(s) in chat '%s' "
            "| mode=%s (%s).",
            len(messages), chat_slug, filters.date_mode, date_range
        )

    return messages, info_message, filters


def _log_view_chat(
    chat_slug: str, sort_by: str, order: str, is_ajax: bool
) -> None:
    """
    Log the rendering of a chat view (full page or AJAX update).

    :param chat_slug: Slug of the chat being displayed.
    :type chat_slug: str
    :param sort_by: Field used for sorting ('timestamp', 'msg_id', etc.).
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :param is_ajax: Whether the request is an AJAX request.
    :type is_ajax: bool
    """
    log_prefix = "[AJAX]" if is_ajax else "[FULL]"
    action = "Updated" if is_ajax else "Displayed"
    logger.info("%s %s chat '%s' view, sorted by %s %s.",
                log_prefix, action, chat_slug, sort_by, order)


@chats_bp.route("/<slug>")
@catch_not_found
def view_chat(_slug: str) -> str:
    """
    Display details and messages of a chat, with optional filters and sorting.

    :param slug: Unique identifier of the chat.
    :type slug: str
    :returns: Rendered chat page or AJAX message table.
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

    chat: Chat = g.chat

    try:
        if filters.action:
            messages, info_message, filters = _get_chat_messages_with_filters(
                chat.slug, filters, sort_by, order
            )
        else:
            chat.message_count, messages = get_chat_data(chat.slug,
                                                         sort_by,
                                                         order)
            info_message = None

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        template = "chats/_msg_table.html" if is_ajax else "chats/view.html"
        _log_view_chat(chat.slug, sort_by, order, is_ajax)

        context = {
            "chat": chat,
            "messages": messages,
            "sort_by": sort_by,
            "order": order,
            "query": filters.query,
            "date_mode": filters.date_mode,
            "start_date": filters.start_date,
            "end_date": filters.end_date,
            "has_filters": filters.has_active(),
            "info_message": info_message,
        }

        return render_template(template, **context)

    except DatabaseError as e:
        logger.error(
            "[DB] Failed loading messages for chat '%s': %s",
            chat.slug, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/<slug>/delete", methods=["POST"])
@catch_not_found
def delete_chat(_slug: str) -> Response:
    """
    Delete a chat and all of its messages.

    :param slug: Unique identifier of the chat.
    :type slug: str
    :returns: Redirect to the chat list view.
    :rtype: Response
    :raises DatabaseError: If deletion from database fails.
    """
    try:
        delete_chat_and_messages(g.chat.slug)
        logger.info("[DELETE] Chat '%s' has been deleted.", g.chat.slug)
        flash(
            f"Chat '{g.chat.name}' and all its messages have been deleted.",
            "success"
        )
    except DatabaseError as e:
        logger.error(
            "[DB] Failed to delete chat '%s': %s", g.chat.slug, e
        )
        flash(f"Failed to delete chat: {e}", "error")

    return redirect(url_for("chats.list_chats"))
