"""
Message routes for the Arcanum application.

Provides endpoints for viewing, creating, editing, and deleting messages.
All operations are linked to chats via chat_ref_id.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response
)

from app.models.message import Message
from app.forms.message_form import MessageForm
from app.services.messages_service import (
    get_message_by_id, insert_message,
    update_message, delete_message as delete_message_by_id
)
from app.services.chats_service import get_chat_by_slug
from app.utils.messages_utils import render_message_view
from app.logs.messages_logs import log_message_action

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
logger = logging.getLogger(__name__)


@messages_bp.route("/<chat_slug>/<int:pk>")
def view_message(chat_slug: str, pk: int) -> str:
    """
    Display details for a single message within a chat.

    :param chat_slug: Slug identifier of the chat.
    :param pk: Internal database id of the message.
    :return: Rendered message details page.
    :raises DatabaseError: On retrieval failure.
    """
    try:
        chat = get_chat_by_slug(chat_slug)
        message = get_message_by_id(pk)

        if not chat or not message or message.chat_ref_id != chat.id:
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.list_chats"))

        return render_message_view(chat_slug, pk)
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to retrieve message id=%d: %s", pk, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@messages_bp.route("/<chat_slug>/new", methods=["GET", "POST"])
def add_message(chat_slug: str) -> Response | str:
    """
    Render and process form for creating a new message in a chat.

    :param chat_slug: Slug of the target chat.
    :return: Redirect on success or rendered form on GET/error.
    :raises IntegrityError: If msg_id is not unique within the chat.
    :raises DatabaseError: On insertion failure.
    """
    chat = get_chat_by_slug(chat_slug)
    if not chat:
        flash("Chat not found.", "error")
        return redirect(url_for("chats.list_chats"))

    form = MessageForm(chat_slug=chat_slug)
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
        except IntegrityError as e:
            logger.warning(
                "[DATABASE|MESSAGES] Integrity error in '%s': %s", chat_slug, e
            )
            flash("Duplicate msg_id in this chat.", "error")
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
    )


@messages_bp.route("/<chat_slug>/<int:pk>/edit", methods=["GET", "POST"])
def edit_message(chat_slug: str, pk: int) -> Response | str:
    """
    Render and process form for editing an existing message.

    :param chat_slug: Slug of the chat.
    :param pk: Database ID of the message.
    :return: Redirect on success or rendered form on GET/error.
    :raises IntegrityError: If msg_id is not unique within the chat.
    :raises DatabaseError: On update failure.
    """
    chat = get_chat_by_slug(chat_slug)
    message = get_message_by_id(pk)

    if not chat or not message or message.chat_ref_id != chat.id:
        flash("Message not found in this chat.", "error")
        return redirect(url_for("chats.view_chat", slug=chat_slug))

    form = MessageForm(chat_slug=chat_slug)

    if request.method == "GET":
        form.populate_from_model(message)

    if form.validate_on_submit():
        data = form.to_model_dict(
            existing_media=message.media,
            existing_screenshot=message.screenshot
        )
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
        except IntegrityError as e:
            logger.warning(
                "[DATABASE|MESSAGES] Integrity error in '%s': %s",
                chat_slug, e
            )
            flash("Duplicate msg_id in this chat.", "error")
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
def delete_message(chat_slug: str, pk: int) -> Response:
    """
    Delete a message from a chat by its ID.

    :param chat_slug: Slug of the chat.
    :param pk: Database ID of the message.
    :return: Redirect to chat view after deletion.
    :raises DatabaseError: On deletion failure.
    """
    try:
        chat = get_chat_by_slug(chat_slug)
        message = get_message_by_id(pk)
        if not chat or not message or message.chat_ref_id != chat.id:
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        delete_message_by_id(pk)
        log_message_action("delete", pk, chat_slug)
        flash("Message deleted successfully.", "success")
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to delete message id=%d: %s", pk, e
        )
        flash(f"Failed to delete message: {e}", "error")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    return redirect(url_for("chats.view_chat", slug=chat_slug))
