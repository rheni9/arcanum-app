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
from flask_babel import _

from app.models.message import Message
from app.models.filters import MessageFilters
from app.forms.message_form import MessageForm
from app.services import message_service
from app.services import chat_service
from app.utils.backblaze_utils import generate_signed_s3_url, clean_url
from app.errors import DuplicateMessageIDError, MessageNotFoundError
from app.logs.messages_logs import (
    log_message_view,
    log_message_action,
    log_media_removal,
    log_screenshot_removal,
)

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
logger = logging.getLogger(__name__)


def render_message_view(
    chat_slug: str, pk: int, prev_message=None, next_message=None
) -> str:
    """
    Render full message view with back URL and context.

    :param chat_slug: Chat slug.
    :param pk: Message ID.
    :param prev_message: Optional previous message object.
    :param next_message: Optional next message object.
    :return: Rendered HTML string.
    """
    chat = chat_service.get_chat_by_slug(chat_slug)
    message = message_service.get_message_by_id(pk)
    if not chat or not message or message.chat_ref_id != chat.id:
        flash("Message not found in this chat.", "error")
        return redirect(url_for("chats.view_chat", slug=chat_slug))

    log_message_view(
        pk, chat.slug, message.timestamp,
        message.get_short_text(30)
    )

    filters = MessageFilters.from_request(request)

    from_search = bool(request.args.get("from_search"))
    from_chats = bool(request.args.get("from_chats"))

    if from_search:
        back_url = url_for("search.global_search", **filters.to_query_args())
        back_label = _("Back to Search")
    elif from_chats:
        back_url = url_for("chats.list_chats")
        back_label = _("Back to Chats")
    else:
        back_url = url_for("chats.view_chat", slug=chat.slug,
                           **filters.to_query_args())
        back_label = _("Back to Chat")

    # Generate signed URL for screenshot if it exists
    signed_screenshot_url = ""
    if message.screenshot:
        signed_screenshot_url = generate_signed_s3_url(
            message.screenshot
        )

    # Generate signed URLs for media if any exist
    signed_media_urls = []
    if message.media:
        signed_media_urls = [
            generate_signed_s3_url(url) for url in message.media
        ]

    return render_template(
        "messages/view.html",
        message=message,
        chat=chat,
        filters=filters,
        signed_screenshot_url=signed_screenshot_url,
        signed_media_urls=signed_media_urls,
        back_url=back_url,
        back_label=back_label,
        prev_message=prev_message,
        next_message=next_message
    )


@messages_bp.route("/<chat_slug>/<int:pk>")
def view_message(chat_slug: str, pk: int) -> str:
    """
    Display details for a single message within a chat,
    including previous and next navigation.

    :param chat_slug: Slug identifier of the chat.
    :param pk: Internal database id of the message.
    :return: Rendered message details page.
    :raises SQLAlchemyError: On retrieval failure.
    """
    try:
        chat = chat_service.get_chat_by_slug(chat_slug)
        message = message_service.get_message_by_id(pk)

        if not chat:
            flash(
                _("Chat with slug '%(slug)s' not found.", slug=chat_slug),
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        if not message or message.chat_ref_id != chat.id:
            flash(_("Message not found in this chat."), "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        prev_message = message_service.get_previous_message(chat.id,
                                                            message.timestamp)
        next_message = message_service.get_next_message(chat.id,
                                                        message.timestamp)

        return render_message_view(
            chat_slug,
            pk,
            prev_message=prev_message,
            next_message=next_message
        )

    except SQLAlchemyError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to retrieve message id=%d: %s", pk, e
        )
        return render_template(
            "error.html", message=_("Database error: %(err)s", err=e)
        )


@messages_bp.route("/<chat_slug>/new", methods=["GET", "POST"])
def add_message(chat_slug: str) -> Response | str:
    """
    Render and process form for creating a new message in a chat.

    :param chat_slug: Slug of the target chat.
    :return: Redirect on success or rendered form on GET/error.
    :raises DuplicateMessageIDError: If msg_id is not unique within the chat.
    :raises SQLAlchemyError: On insertion failure.
    """
    chat = chat_service.get_chat_by_slug(chat_slug)
    if not chat:
        flash(
            _("Chat with slug '%(slug)s' not found.", slug=chat_slug), "error"
        )
        return redirect(url_for("chats.list_chats"))

    form = MessageForm(chat_slug=chat_slug)
    form.chat_ref_id.data = chat.id

    if form.validate_on_submit():
        data = form.to_model_dict()
        message = Message.from_dict(data)
        try:
            pk = message_service.insert_message(message)
            message.id = pk
            flash(_("Message added successfully."), "success")
            log_message_action("create", message.id, chat.slug)
            return redirect(
                url_for("messages.view_message",
                        chat_slug=chat.slug,
                        pk=message.id)
            )
        except DuplicateMessageIDError:
            logger.warning(
                "[DATABASE|MESSAGES] Duplicate msg_id in the chat '%s'",
                chat_slug
            )
            flash(
                _(
                    "This Message ID is already in use in this chat. "
                    "Please check the value."
                ),
                "error"
            )
        except SQLAlchemyError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to add message to '%s': %s",
                chat_slug, e
            )
            flash(_("Failed to add message: %(err)s", err=e), "error")

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
    :raises DuplicateMessageIDError: If msg_id is not unique within the chat.
    :raises SQLAlchemyError: On update failure.
    """
    chat = chat_service.get_chat_by_slug(chat_slug)
    message = message_service.get_message_by_id(pk)

    if not chat:
        flash(
            _("Chat with slug '%(slug)s' not found.", slug=chat_slug),
            "error"
        )
        return redirect(url_for("chats.list_chats"))

    if not message or message.chat_ref_id != chat.id:
        flash(_("Message not found in this chat."), "error")
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
            message_service.update_message(updated_message)
            flash(_("Message updated successfully."), "success")
            log_message_action("update", message.id, chat.slug)
            return redirect(
                url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
            )
        except DuplicateMessageIDError:
            logger.warning(
                "[MESSAGES|ROUTER] Duplicate msg_id update rejected "
                "for chat '%s'.", chat_slug
            )
            flash(
                _(
                    "This Message ID is already in use in this chat. "
                    "Please check the value."
                ),
                "error"
            )
        except MessageNotFoundError:
            logger.warning(
                "[MESSAGES|ROUTER] Tried to update non-existent message "
                "ID=%d.", pk
            )
            flash(_("Message not found for update."), "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        except SQLAlchemyError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to update message id=%d: %s",
                pk, e
            )
            flash(_("Failed to update message: %(err)s", err=e), "error")

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
        chat = chat_service.get_chat_by_slug(chat_slug)
        message = message_service.get_message_by_id(pk)

        if not chat:
            flash(
                _("Chat with slug '%(slug)s' not found.", slug=chat_slug),
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        if not message or message.chat_ref_id != chat.id:
            flash(_("Message not found in this chat."), "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        message_service.delete_message_by_id(pk)
        log_message_action("delete", pk, chat_slug)
        flash(_("Message deleted successfully."), "success")
    except SQLAlchemyError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to delete message id=%d: %s", pk, e
        )
        flash(_("Failed to delete message: %(err)s", err=e), "error")
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
    submitted_url = request.form.get("media_url")
    if not submitted_url:
        flash(_("Missing media URL for deletion."), "error")
        return redirect(
            url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
        )

    try:
        message = message_service.get_message_by_id(pk)
        chat = chat_service.get_chat_by_slug(chat_slug)
        if not chat:
            flash(
                _("Chat with slug '%(slug)s' not found.", slug=chat_slug),
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        if not message or message.chat_ref_id != chat.id:
            flash(_("Message not found in this chat."), "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        clean_submitted = clean_url(submitted_url)
        original_media = message.media or []

        updated_media = [
            url for url in original_media if clean_url(url) != clean_submitted
        ]

        if len(updated_media) == len(original_media):
            flash(_("Could not find matching media for removal."), "warning")
        else:
            message.media = updated_media
            message_service.update_message(message)
            flash(_("Media file removed."), "success")
            log_media_removal(pk, chat_slug, clean_submitted)

    except SQLAlchemyError as e:
        logger.error("[DATABASE|MESSAGES] Media removal failed: %s", e)
        flash(_("Failed to remove media file."), "error")

    return redirect(url_for(
        "messages.view_message", chat_slug=chat_slug, pk=pk)
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
        message = message_service.get_message_by_id(pk)
        chat = chat_service.get_chat_by_slug(chat_slug)

        if not chat:
            flash(
                _("Chat with slug '%(slug)s' not found.", slug=chat_slug),
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        if not message or message.chat_ref_id != chat.id:
            flash(_("Message not found in this chat."), "error")
            return redirect(url_for("chats.view_chat", slug=chat_slug))

        if not message.screenshot:
            flash(
                _("Could not find matching screenshot for removal."), "warning"
            )
        else:
            message.screenshot = None
            message_service.update_message(message)
            flash(_("Screenshot removed."), "success")
            log_screenshot_removal(pk, chat_slug)

    except SQLAlchemyError as e:
        logger.error("[DATABASE|MESSAGES] Screenshot removal failed: %s", e)
        flash(_("Failed to remove screenshot."), "error")

    return redirect(
        url_for("messages.view_message", chat_slug=chat_slug, pk=pk)
    )
