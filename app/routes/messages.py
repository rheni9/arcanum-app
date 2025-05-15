"""
Message routes for the Arcanum application.

Provides endpoints to view, create, update, and delete messages.
Messages are linked to chats via chat_ref_id.
"""

import logging
from sqlite3 import DatabaseError
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, Response
)

from app.services.messages_service import (
    get_message_by_id, insert_message,
    update_message, delete_message_record
)
from app.utils.form_utils import clean_form
from app.utils.decorators import catch_not_found

messages_bp = Blueprint("messages", __name__, url_prefix="/messages")
logger = logging.getLogger(__name__)


@messages_bp.route("/<int:db_id>")
@catch_not_found
def view_message(db_id: int) -> str:
    """
    View message details.

    :param db_id: Internal database ID of the message.
    :type db_id: int
    :returns: Rendered message details page.
    :rtype: str
    :raises DatabaseError: On retrieval failure.
    """
    try:
        message = get_message_by_id(db_id)
        return render_template("messages/view.html", message=message)
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to retrieve message id=%d: %s",
            db_id, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@messages_bp.route("/<chat_slug>/new", methods=["GET", "POST"])
def add_message(chat_slug: str) -> Response | str:
    """
    Add a new message to a chat.

    :param chat_slug: Slug of the target chat.
    :type chat_slug: str
    :returns: Redirect on success or render form on GET/error.
    :rtype: Response | str
    :raises DatabaseError: On insertion failure.
    """
    if request.method == "POST":
        data = clean_form(request.form.to_dict())
        try:
            insert_message(chat_slug, data)
            logger.info(
                "[MESSAGES|CREATE] Message added to chat '%s'.", chat_slug
            )
            flash("Message added successfully.", "success")
            return redirect(url_for("chats.view_chat", slug=chat_slug))
        except DatabaseError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to add message to '%s': %s",
                chat_slug, e
            )
            flash(f"Failed to add message: {e}", "error")

    return render_template(
        "messages/form.html",
        message=None,
        is_edit=False,
        chat_slug=chat_slug
    )


@messages_bp.route("/<int:db_id>/edit", methods=["GET", "POST"])
@catch_not_found
def edit_message(db_id: int) -> Response | str:
    """
    Edit an existing message.

    :param db_id: Internal database ID of the message.
    :type db_id: int
    :returns: Redirect on success or render form on GET/error.
    :rtype: Response | str
    :raises DatabaseError: On update failure.
    """
    if request.method == "POST":
        data = clean_form(request.form.to_dict())
        try:
            update_message(db_id, data)
            logger.info("[MESSAGES|UPDATE] Message id=%d updated.", db_id)
            flash("Message updated successfully.", "success")
            return redirect(url_for("messages.view_message", db_id=db_id))
        except DatabaseError as e:
            logger.error(
                "[DATABASE|MESSAGES] Failed to update message id=%d: %s",
                db_id, e
            )
            flash(f"Failed to update message: {e}", "error")

    message = get_message_by_id(db_id)
    return render_template(
        "messages/form.html",
        message=message,
        is_edit=True
    )


@messages_bp.route("/<int:db_id>/delete", methods=["POST"])
@catch_not_found
def delete_message(db_id: int) -> Response:
    """
    Delete a message.

    :param db_id: Internal database ID of the message.
    :type db_id: int
    :returns: Redirect to chat view after deletion.
    :rtype: Response
    :raises DatabaseError: On deletion failure.
    """
    try:
        message = get_message_by_id(db_id)
        delete_message_record(db_id)
        logger.info("[MESSAGES|DELETE] Message id=%d deleted.", db_id)
        flash("Message deleted successfully.", "success")
        return redirect(url_for("chats.view_chat", slug=message["chat_slug"]))
    except DatabaseError as e:
        logger.error(
            "[DATABASE|MESSAGES] Failed to delete message id=%d: %s",
            db_id, e
        )
        flash(f"Failed to delete message: {e}", "error")
        return redirect(request.referrer or url_for("dashboard.dashboard"))
