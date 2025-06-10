"""
Message routes for the Arcanum application.

Provides endpoints for viewing, creating, editing, and deleting messages.
All operations are linked to chats via chat_ref_id.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, Response
)

from app.models.message import Message
from app.models.filters import MessageFilters
from app.forms.message_form import MessageForm
from app.services.messages_service import (
    get_message_by_id, insert_message,
    update_message, delete_message
)
from app.services.chats_service import get_chat_by_slug
from app.logs.messages_logs import log_message_view, log_message_action

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
logger = logging.getLogger(__name__)


@messages_bp.route("/<chat_slug>/<int:pk>")
def view_message(chat_slug: str, pk: int) -> str:
    """
    Display details for a single message.

    :param chat_slug: Slug of the chat.
    :param pk: Internal database id of the message.
    :return: Rendered message details page.
    :raises DatabaseError: On retrieval failure.
    """
    try:
        chat = get_chat_by_slug(chat_slug)
        message = get_message_by_id(pk)
        if not chat or not message or message.chat_ref_id != chat.id:
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        log_message_view(
            message.id, chat.slug, message.timestamp,
            message.get_short_text(10)
        )

        filters = MessageFilters.from_request(request)

        from_search = bool(request.args.get("from_search"))
        from_chats = bool(request.args.get("from_chats"))

        if from_search:
            back_url = url_for(
                "search.global_search", **filters.to_query_args()
            )
        elif from_chats:
            back_url = url_for("chats.list_chats")
        else:
            back_url = url_for(
                "chats.view_chat", slug=chat.slug, **filters.to_query_args()
            )

        context = {
            "message": message,
            "chat": chat,
            "from_chats": bool(request.args.get("from_chats")),
            "from_search": bool(request.args.get("from_search")),
            "filters": filters,
            "back_url": back_url,
        }

        return render_template("messages/view.html", **context)
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to retrieve message id=%d: %s", pk, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@messages_bp.route("/<chat_slug>/new", methods=["GET", "POST"])
def add_message(chat_slug: str) -> Response | str:
    """
    Add a new message to a chat.

    :param chat_slug: Slug of the target chat.
    :return: Redirect on success or render form on GET/error.
    :raises DatabaseError: On insertion failure.
    """
    chat = get_chat_by_slug(chat_slug)
    if not chat:
        flash("Chat not found.", "error")
        return redirect(url_for("chats.list_chats"))

    form = MessageForm()
    form.chat_ref_id.data = chat.id

    if form.validate_on_submit():
        data = form.to_model_dict()
        message = Message.from_dict(data)
        try:
            pk = insert_message(message)
            message.id = pk
            flash("Message added successfully.", "success")
            log_message_action("create", message.id, chat.slug)
            return redirect(
                url_for("messages.view_message",
                        chat_slug=chat.slug,
                        pk=message.id)
            )
        except DatabaseError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to add message to '%s': %s",
                chat_slug, e
            )
            flash(f"Failed to add message: {e}", "error")
    return render_template(
        "messages/form.html",
        form=form,
        is_edit=False,
        message=None,
        chat=chat,
        chat_slug=chat_slug
    )


@messages_bp.route("/<chat_slug>/<int:pk>/edit", methods=["GET", "POST"])
def edit_message(chat_slug: str, pk: int) -> Response | str:
    """
    Edit an existing message.

    :param chat_slug: Slug of the chat.
    :param pk: Database id of the message.
    :return: Redirect on success or rendered form on GET/error.
    :raises DatabaseError: On update failure.
    """
    chat = get_chat_by_slug(chat_slug)
    message = get_message_by_id(pk)
    if not chat or not message or message.chat_ref_id != chat.id:
        flash("Message not found in this chat.", "error")
        return redirect(url_for("chats.view_chat", slug=chat_slug))

    form = MessageForm()

    if request.method == "GET":
        form.populate_from_model(message)

    if form.validate_on_submit():
        data = form.to_model_dict()
        data["id"] = message.id
        data["chat_ref_id"] = chat.id
        updated_message = Message.from_dict(data)
        try:
            update_message(updated_message)
            flash("Message updated successfully.", "success")
            log_message_action("update", message.id, chat.slug)
            return redirect(
                url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
            )
        except DatabaseError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to update message id=%d: %s",
                pk, e
            )
            flash(f"Failed to update message: {e}", "error")

    return render_template(
        "messages/form.html",
        form=form,
        is_edit=True,
        message=message,
        chat=chat,
        chat_slug=chat_slug
    )


@messages_bp.route("/<chat_slug>/<int:pk>/delete", methods=["POST"])
def delete_message_route(chat_slug: str, pk: int) -> Response:
    """
    Delete a message by its database id.

    :param chat_slug: Slug of the chat.
    :param pk: Database id of the message.
    :return: Redirect to chat view after deletion.
    :raises DatabaseError: On deletion failure.
    """
    try:
        chat = get_chat_by_slug(chat_slug)
        message = get_message_by_id(pk)
        if not chat or not message or message.chat_ref_id != chat.id:
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        delete_message(pk)
        log_message_action("delete", pk, chat_slug)
        flash("Message deleted successfully.", "success")
        return redirect(url_for("chats.view_chat", slug=chat_slug))
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to delete message id=%d: %s", pk, e
        )
        flash(f"Failed to delete message: {e}", "error")
        return redirect(request.referrer or url_for("dashboard.dashboard"))
