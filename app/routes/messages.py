"""
Message routes for the Arcanum application.

Provides endpoints for viewing, creating, editing, and deleting messages.
All operations are linked to chats via chat_ref_id.
"""

import logging
from sqlalchemy.exc import SQLAlchemyError
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
from app.errors import DuplicateMessageError, MessageNotFoundError
from app.logs.messages_logs import (
    log_message_action, log_media_removal, log_screenshot_removal
)

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
logger = logging.getLogger(__name__)


@messages_bp.route("/<chat_slug>/<int:pk>")
def view_message(chat_slug: str, pk: int) -> str:
    """
    Display details for a single message within a chat.

    :param chat_slug: Slug identifier of the chat.
    :param pk: Internal database id of the message.
    :return: Rendered message details page.
    :raises SQLAlchemyError: On retrieval failure.
    """
    try:
        chat = get_chat_by_slug(chat_slug)
        message = get_message_by_id(pk)

        if not chat or not message or message.chat_ref_id != chat.id:
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.list_chats"))

        return render_message_view(chat_slug, pk)
    except SQLAlchemyError as e:
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
    :raises DuplicateMessageError: If msg_id is not unique within the chat.
    :raises SQLAlchemyError: On insertion failure.
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
        except DuplicateMessageError:
            logger.warning(
                "[DATABASE|MESSAGES] Duplicate msg_id in the chat '%s'",
                chat_slug
            )
            flash("Duplicate msg_id in this chat.", "error")
        except SQLAlchemyError as e:
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
    :raises MessageNotFoundError: If the message to update does not exist.
    :raises DuplicateMessageError: If msg_id is not unique within the chat.
    :raises SQLAlchemyError: On update failure.
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
        except DuplicateMessageError:
            logger.warning(
                "[MESSAGES|ROUTER] Duplicate msg_id update rejected "
                "for chat '%s'.", chat_slug
            )
            flash("Duplicate msg_id in this chat.", "error")
        except MessageNotFoundError:
            logger.warning(
                "[MESSAGES|ROUTER] Tried to update non-existent message "
                "ID=%d.", pk
            )
            flash("Message not found for update.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        except SQLAlchemyError as e:
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
    :raises SQLAlchemyError: On deletion failure.
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
    except SQLAlchemyError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to delete message id=%d: %s", pk, e
        )
        flash(f"Failed to delete message: {e}", "error")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    return redirect(url_for("chats.view_chat", slug=chat_slug))


@messages_bp.route("/<chat_slug>/<int:pk>/remove_media", methods=["POST"])
def remove_media(chat_slug: str, pk: int) -> Response:
    """
    Remove a specific media file from a message.

    :param chat_slug: Slug of the chat.
    :param pk: ID of the message.
    :return: Redirect to message view after update.
    """
    media_url = request.form.get("media_url")
    if not media_url:
        flash("Missing media URL for deletion.", "error")
        return redirect(
            url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
        )

    try:
        message = get_message_by_id(pk)
        if (
            not message
            or message.chat_ref_id != get_chat_by_slug(chat_slug).id
        ):
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        updated_media = [url for url in message.media if url != media_url]
        message.media = updated_media
        update_message(message)

        flash("Media file removed.", "success")
        log_media_removal(pk, chat_slug, media_url)
    except SQLAlchemyError as e:
        logger.error("[DATABASE|MESSAGES] Media removal failed: %s", e)
        flash("Failed to remove media file.", "error")

    return redirect(
        url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
    )


@messages_bp.route("/<chat_slug>/<int:pk>/remove_screenshot", methods=["POST"])
def remove_screenshot(chat_slug: str, pk: int) -> Response:
    """
    Remove screenshot from a message.

    :param chat_slug: Slug of the chat.
    :param pk: ID of the message.
    :return: Redirect to message view after update.
    """
    try:
        message = get_message_by_id(pk)
        if (
            not message
            or message.chat_ref_id != get_chat_by_slug(chat_slug).id
        ):
            flash("Message not found in this chat.", "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        message.screenshot = None
        update_message(message)

        flash("Screenshot removed.", "success")
        log_screenshot_removal(pk, chat_slug)
    except SQLAlchemyError as e:
        logger.error("[DATABASE|MESSAGES] Screenshot removal failed: %s", e)
        flash("Failed to remove screenshot.", "error")

    return redirect(
        url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
    )
