"""
Chat routes for the Arcanum application.

Provides endpoints for listing, viewing, creating, editing, and deleting chats.
Supports AJAX updates, sorting, and message filtering for chat messages.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError
from flask import (
    Blueprint, render_template, redirect, url_for, flash, Response
)

from app.models.chat import Chat
from app.forms.chat_form import ChatForm
from app.services.chats_service import (
    get_chat_by_slug, insert_chat, update_chat,
    delete_chat_and_messages, slug_exists
)
from app.utils.slugify_utils import slugify, generate_unique_slug
from app.utils.chats_utils import render_chat_list, render_chat_view
from app.logs.chats_logs import log_chat_action

chats_bp = Blueprint("chats", __name__, url_prefix="/chats")
logger = logging.getLogger(__name__)


@chats_bp.route("/")
def list_chats() -> str:
    """
    Display list of all chats with optional sorting and AJAX updates.

    :return: Rendered chat list page or table fragment.
    :raises DatabaseError: On retrieval failure.
    """
    try:
        return render_chat_list()
    except DatabaseError as e:
        logger.error("[DATABASE|CHATS] Failed to retrieve chats: %s", e)
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/<slug>")
def view_chat(slug: str) -> str:
    """
    Display details for a chat and its messages with filters and sorting.

    :param slug: Slug identifier of the chat.
    :return: Rendered chat view page or table fragment.
    :raises DatabaseError: On retrieval failure.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        flash(f"Chat with slug '{slug}' not found.", "error")
        return redirect(url_for("chats.list_chats"))

    try:
        return render_chat_view(chat)
    except DatabaseError as e:
        logger.error(
            "[DATABASE|CHATS] Failed to load messages for '%s': %s", slug, e
        )
        return render_template("error.html", message=f"Database error: {e}")


@chats_bp.route("/new", methods=["GET", "POST"])
def add_chat() -> Response | str:
    """
    Render and process form for creating a new chat.

    :return: Redirect on success or rendered form on GET/error.
    :raises IntegrityError: If slug is not unique.
    :raises DatabaseError: On insertion failure.
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
            log_chat_action(action="create", chat_slug=chat.slug)
            flash(f"Chat '{chat.name}' created successfully.", "success")
            return redirect(url_for("chats.view_chat", slug=chat.slug))
        except IntegrityError as e:
            logger.warning("[DATABASE|CHATS] Integrity error: %s", e)
            flash("Slug already exists. Please choose another name.", "error")

        except DatabaseError as e:
            logger.error("[DATABASE|CHATS] Failed to create chat: %s", e)
            flash(f"Failed to create chat: {e}", "error")

    return render_template("chats/form.html", form=form, is_edit=False)


@chats_bp.route("/<slug>/edit", methods=["GET", "POST"])
def edit_chat(slug: str) -> Response | str:
    """
    Render and process form for editing an existing chat.

    :param slug: Slug of the chat to edit.
    :return: Redirect on success or rendered form on GET/error.
    :raises IntegrityError: If new slug already exists.
    :raises DatabaseError: On update failure.
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
            log_chat_action(action="update", chat_slug=updated_chat.slug)
            flash(
                f"Chat '{updated_chat.name}' updated successfully.", "success"
            )
            return redirect(url_for("chats.view_chat", slug=updated_chat.slug))
        except IntegrityError as e:
            logger.warning("[DATABASE|CHATS] Integrity error: %s", e)
            flash("Slug already exists. Please choose another name.", "error")
        except DatabaseError as e:
            logger.error("[DATABASE|CHATS] Failed to update chat: %s", e)
            flash(f"Failed to update chat: {e}", "error")

    return render_template(
        "chats/form.html", form=form, is_edit=True, chat=chat
    )


@chats_bp.route("/<slug>/delete", methods=["POST"])
def delete_chat(slug: str) -> Response:
    """
    Delete a chat along with its messages.

    :param slug: Slug of the chat to delete.
    :return: Redirect to chat list after deletion.
    :raises DatabaseError: On deletion failure.
    """
    chat = get_chat_by_slug(slug)
    if not chat:
        flash(f"Chat with slug '{slug}' not found.", "error")
        return redirect(url_for("chats.list_chats"))

    try:
        delete_chat_and_messages(slug)
        log_chat_action(action="delete", chat_slug=slug)
        flash(f"Chat '{chat.name}' deleted successfully.", "success")
    except DatabaseError as e:
        logger.error(
            "[DATABASE|CHATS] Failed to delete chat '%s': %s", slug, e
        )
        flash(f"Failed to delete chat: {e}", "error")

    return redirect(url_for("chats.list_chats"))
