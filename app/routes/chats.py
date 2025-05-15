"""
Chat routes for the Arcanum application.

Provides endpoints to list, create, edit, view, and delete chats.
Supports AJAX updates, sorting, message filtering, and conflict handling.
"""

import logging
from sqlite3 import DatabaseError
from typing import Tuple
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, Response, g
)

from app.models.filters import MessageFilters
from app.services.chats_service import (
    get_chats, insert_chat, update_chat,
    delete_chat_and_messages, slug_exists
)
from app.services.filters_service import resolve_search_action
from app.services.messages_service import get_chat_data
from app.services.chats_service import get_chat_by_slug
from app.utils.chat_form_validators import validate_chat_form
from app.utils.chats_utils import build_chat_object
from app.utils.form_utils import clean_form
from app.utils.slugify_utils import slugify, generate_unique_slug
from app.utils.sort_utils import get_sort_order
from app.utils.decorators import catch_not_found

chats_bp = Blueprint("chats", __name__, url_prefix="/chats")
logger = logging.getLogger(__name__)


def _log_list_view(
    sort_by: str,
    order: str,
    is_ajax: bool,
    slug: str | None = None
) -> None:
    """
    Log chat list or message list view rendering.

    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :param is_ajax: True if AJAX request.
    :type is_ajax: bool
    :param slug: Chat slug if viewing a single chat.
    :type slug: str | None
    """
    context = (
        "chats list" if slug is None
        else f"messages for chat '{slug}'"
    )
    action = "AJAX" if is_ajax else "FULL"
    logger.debug(
        "[CHATS|%s] Displayed %s sorted by %s %s.",
        action, context, sort_by, order
    )


def _fetch_chat_messages(
    slug: str,
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> Tuple[list[dict], str | None, MessageFilters]:
    """
    Retrieve messages for a chat with applied filters.

    :param slug: Chat slug identifier.
    :type slug: str
    :param filters: Applied search/filter parameters.
    :type filters: MessageFilters
    :param sort_by: Field used for sorting.
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :returns: Tuple of messages, info message, and normalized filters.
    :rtype: Tuple[list[dict], str | None, MessageFilters]
    """
    if filters.action:
        return resolve_search_action(
            filters=filters,
            sort_by=sort_by,
            order=order,
            chat_slug=slug
        )

    count, messages = get_chat_data(slug, sort_by, order)
    g.chat.message_count = count

    return messages, None, filters


@chats_bp.route("/")
def list_chats() -> str:
    """
    List all chats with optional sorting and AJAX updates.

    :returns: Rendered chat list page or table fragment.
    :rtype: str
    :raises DatabaseError: On retrieval failure.
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
        _log_list_view(sort_by, order, is_ajax)

        return render_template(
            template, chats=chats, sort_by=sort_by, order=order
        )
    except DatabaseError as e:
        logger.error("[DATABASE|CHATS] Failed to retrieve chats: %s", e)
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/new")
def new_chat() -> str:
    """
    Render form for creating a new chat.

    :returns: Rendered empty chat form.
    :rtype: str
    """
    return render_template("chats/form.html", chat=None, is_edit=False)


@chats_bp.route("/<slug>/edit")
@catch_not_found
def edit_chat(_slug: str) -> str:
    """
    Render form for editing an existing chat.

    :param _slug: Chat slug identifier.
    :type _slug: str
    :returns: Rendered form with chat data.
    :rtype: str
    """
    return render_template("chats/form.html", chat=g.chat, is_edit=True)


@chats_bp.route("/save", methods=["POST"])
def save_chat() -> Response:
    """
    Save chat data (create or update).

    Validates form data, updates slug if name changes,
    persists changes, and handles conflicts.

    :returns: Redirect or rendered form with errors.
    :rtype: Response
    :raises ValueError: On invalid data.
    :raises DatabaseError: On persistence failure.
    """
    data = clean_form(request.form.to_dict())
    original_slug = data.get("original_slug")
    is_edit = bool(original_slug)

    # Validate form fields
    fields, errors = validate_chat_form(data)
    if errors:
        logger.info("[CHATS|FORM] Validation errors: %s", errors)
        return render_template(
            "chats/form.html",
            chat=data,
            errors=errors,
            original_slug=original_slug,
            is_edit=is_edit
        )

    chat_ref_id = None
    existing_chat = None

    if is_edit:
        existing_chat = get_chat_by_slug(original_slug)
        if existing_chat:
            chat_ref_id = existing_chat.id
            # Only update slug if name was changed
            if data["name"] != existing_chat.name:
                slug = slugify(data["name"])
            else:
                slug = existing_chat.slug
        else:
            raise ValueError(f"Chat with slug '{original_slug}' not found.")
    else:
        slug = slugify(data["name"])
        if slug_exists(slug):
            slug = generate_unique_slug(slug, data.get("link") or "")

    # Build chat object with new slug and fields
    chat = build_chat_object({**data, **fields}, slug, chat_ref_id=chat_ref_id)

    try:
        if is_edit:
            update_chat(chat)
            logger.info("[CHATS|UPDATE] Chat '%s' updated.", chat.slug)
            flash(f"Chat '{chat.name}' updated successfully.", "success")
        else:
            insert_chat(chat)
            logger.info("[CHATS|CREATE] Chat '%s' created.", chat.slug)
            flash(f"Chat '{chat.name}' created successfully.", "success")

        return redirect(url_for("chats.view_chat", slug=chat.slug))

    except (ValueError, DatabaseError) as e:
        logger.error("[DATABASE|CHATS] Failed to save chat '%s': %s",
                     chat.slug, e)
        flash(f"Failed to save chat: {e}", "error")
        return render_template("chats/form.html", chat=chat, is_edit=is_edit)


@chats_bp.route("/<slug>")
@catch_not_found
def view_chat(slug: str) -> str:
    """
    View chat details and messages with filters and sorting.

    :param slug: Chat slug identifier.
    :type slug: str
    :returns: Rendered chat view page or table fragment.
    :rtype: str
    :raises DatabaseError: On retrieval failure.
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
        messages, info_msg, filters = _fetch_chat_messages(
            slug, filters, sort_by, order
        )
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        template = "chats/_msg_table.html" if is_ajax else "chats/view.html"
        _log_list_view(sort_by, order, is_ajax, slug)

        return render_template(
            template,
            chat=g.chat,
            messages=messages,
            sort_by=sort_by,
            order=order,
            query=filters.query,
            date_mode=filters.date_mode,
            start_date=filters.start_date,
            end_date=filters.end_date,
            has_filters=filters.has_active(),
            info_message=info_msg
        )
    except DatabaseError as e:
        logger.error("[DATABASE|CHATS] Failed loading messages for '%s': %s",
                     slug, e)
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/<slug>/delete", methods=["POST"])
@catch_not_found
def delete_chat(slug: str) -> Response:
    """
    Delete a chat and its messages.

    :param slug: Chat slug identifier.
    :type slug: str
    :returns: Redirect to chat list after deletion.
    :rtype: Response
    :raises DatabaseError: On deletion failure.
    """
    try:
        delete_chat_and_messages(slug)
        logger.info("[CHATS|DELETE] Chat '%s' deleted.", slug)
        flash(f"Chat '{g.chat.name}' deleted successfully.", "success")
    except DatabaseError as e:
        logger.error("[DATABASE|CHATS] Failed to delete chat '%s': %s",
                     slug, e)
        flash(f"Failed to delete chat: {e}", "error")

    return redirect(url_for("chats.list_chats"))
