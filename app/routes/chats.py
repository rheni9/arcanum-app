"""
Chat routes for the Arcanum application.

Provides endpoints for listing, viewing, creating, editing, and deleting chats.
Supports AJAX updates, sorting, and message filtering for chat messages.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from app.models.chat import Chat
from app.models.filters import MessageFilters
from app.forms.chat_form import ChatForm
from app.services.chats_service import (
    get_chats, get_chat_by_slug, insert_chat, update_chat,
    delete_chat_and_messages, slug_exists, get_global_stats
)
from app.services.messages_service import (
    get_messages_by_chat_slug, count_messages_in_chat
)
from app.services.filters_service import (
    resolve_message_query, normalize_filter_action
)
from app.utils.slugify_utils import slugify, generate_unique_slug
from app.utils.sort_utils import get_sort_order
from app.logs.chats_logs import (
    log_list_view, log_list_ajax,
    log_chat_view, log_chat_view_ajax,
    log_chat_action
)

chats_bp = Blueprint("chats", __name__, url_prefix="/chats")
logger = logging.getLogger(__name__)


@chats_bp.route("/")
def list_chats() -> str:
    """
    List all chats with optional sorting and AJAX updates.

    :return: Rendered chat list page or table fragment.
    :raises DatabaseError: On retrieval failure.
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"name", "message_count", "last_message"},
        default_field="last_message",
        default_order="desc"
    )

    try:
        chats = get_chats(sort_by, order)
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        template = "chats/_chats_table.html" if is_ajax else "chats/index.html"

        if is_ajax:
            log_list_ajax(len(chats), sort_by, order)

        stats = get_global_stats()
        log_list_view(len(chats), sort_by, order)

        return render_template(
            template,
            chats=chats,
            sort_by=sort_by,
            order=order,
            stats=stats,
            from_chats=True,
            search_action=url_for("search.global_search"),
            clear_url=url_for("search.global_search"),
            chat_slug=None,
            filters=MessageFilters()
        )
    except DatabaseError as e:
        logger.error("[DATABASE|CHATS] Failed to retrieve chats: %s", e)
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/new", methods=["GET", "POST"])
def new_chat() -> Response | str:
    """
    Render and process form for creating a new chat.

    :return: Redirect on success, or rendered form with errors.
    """
    form = ChatForm()

    if form.validate_on_submit():
        slug = slugify(form.name.data)
        if slug_exists(slug):
            slug = generate_unique_slug(slug, form.link.data or "")

        chat_data = form.to_model_dict()
        chat_data["slug"] = slug
        chat = Chat.from_dict(chat_data)

        try:
            insert_chat(chat)
            log_chat_action("create", chat.slug)
            flash(f"Chat '{chat.name}' created successfully.", "success")
            return redirect(url_for("chats.view_chat", slug=chat.slug))
        except (ValueError, DatabaseError) as e:
            logger.error("[DATABASE|CHATS] Failed to create chat: %s", e)
            flash(f"Failed to create chat: {e}", "error")

    return render_template("chats/form.html", form=form, is_edit=False)


@chats_bp.route("/<slug>/edit", methods=["GET", "POST"])
def edit_chat(slug: str) -> Response | str:
    """
    Render and process form for editing an existing chat.

    :param slug: Chat slug identifier.
    :return: Redirect on success, or rendered form with errors.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        flash(f"Chat with slug '{slug}' not found.", "error")
        return redirect(url_for("chats.list_chats"))

    form = ChatForm(obj=chat)

    if form.validate_on_submit():
        new_slug = slugify(form.name.data)
        if new_slug != chat.slug and slug_exists(new_slug):
            new_slug = generate_unique_slug(new_slug, form.link.data or "")

        updated_data = form.to_model_dict()
        updated_data["slug"] = new_slug
        updated_data["id"] = chat.id
        updated_chat = Chat.from_dict(updated_data)

        try:
            update_chat(updated_chat)
            log_chat_action("update", updated_chat.slug)
            flash(
                f"Chat '{updated_chat.name}' updated successfully.", "success"
            )
            return redirect(url_for("chats.view_chat", slug=updated_chat.slug))
        except (ValueError, DatabaseError) as e:
            logger.error("[DATABASE|CHATS] Failed to update chat: %s", e)
            flash(f"Failed to update chat: {e}", "error")

    return render_template(
        "chats/form.html", form=form, is_edit=True, chat=chat
    )


@chats_bp.route("/<slug>")
def view_chat(slug: str) -> str:
    """
    View chat details and messages with filters and sorting.

    :param slug: Chat slug identifier.
    :return: Rendered chat view page or table fragment.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        flash(f"Chat with slug '{slug}' not found.", "error")
        return redirect(url_for("chats.list_chats"))

    total_count = count_messages_in_chat(chat.id)

    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"timestamp", "msg_id", "text"},
        default_field="timestamp",
        default_order="desc"
    )

    filters = MessageFilters.from_request(request)
    filters.chat_slug = slug
    normalize_filter_action(filters)

    try:
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        template = "chats/_msg_table.html" if is_ajax else "chats/view.html"

        if filters.action is None:
            messages = get_messages_by_chat_slug(slug, sort_by, order)
            message_count = len(messages)
            info_message = None
        else:
            if (
                filters.action == "search"
                and filters.query
                and filters.query.strip().startswith("#")
            ):
                tag = filters.query.strip().lstrip("#")
                return redirect(
                    url_for("chats.view_chat",
                            slug=slug, action="tag", tag=tag)
                )
            status, context = resolve_message_query(filters, sort_by, order)

            if status == "invalid":
                messages = []
                message_count = 0
                info_message = context["info_message"]
            elif status == "cleared":
                messages = get_messages_by_chat_slug(slug, sort_by, order)
                message_count = len(messages)
                info_message = context["info_message"]
            else:
                messages = context["messages"]
                message_count = context["count"]
                info_message = context["info_message"]

        is_valid_action = filters.action is not None

        if is_ajax:
            if is_valid_action:
                log_chat_view_ajax(slug, message_count, filters.to_dict())
        else:
            if is_valid_action:
                log_chat_view(slug, message_count, filters.to_dict())
            else:
                logger.warning(
                    "[CHATS|VIEW] Invalid filter input — no search performed."
                )

        args = request.args.to_dict(flat=True)
        args.pop("chat_slug", None)

        from_search = bool(request.args.get("from_search"))
        from_chats = bool(request.args.get("from_chats"))

        return render_template(
            template,
            chat=chat,
            chat_slug=chat.slug,
            messages=messages,
            message_count=message_count,
            total_count=total_count,
            sort_by=sort_by,
            order=order,
            filters=filters,
            has_filters=filters.has_active(),
            info_message=info_message,
            search_action=url_for("chats.view_chat", slug=chat.slug),
            clear_url=url_for("chats.view_chat", slug=chat.slug),
            extra_args=args,
            from_search=from_search,
            from_chats=from_chats,
        )
    except DatabaseError as e:
        logger.error(
            "[DATABASE|CHATS] Failed to load messages for '%s': %s", slug, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/<slug>/delete", methods=["POST"])
def delete_chat(slug: str) -> Response:
    """
    Delete a chat and its messages.

    :param slug: Chat slug identifier.
    :return: Redirect to chat list after deletion.
    :raises DatabaseError: On deletion failure.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        flash(f"Chat with slug '{slug}' not found.", "error")
        return redirect(url_for("chats.list_chats"))

    try:
        delete_chat_and_messages(slug)
        log_chat_action("delete", slug)
        flash(f"Chat '{chat.name}' deleted successfully.", "success")
    except DatabaseError as e:
        logger.error(
            "[DATABASE|CHATS] Failed to delete chat '%s': %s", slug, e
        )
        flash(f"Failed to delete chat: {e}", "error")

    return redirect(url_for("chats.list_chats"))
