"""
Message utilities for the Arcanum application.

Groups messages by chat slug and prepares structured containers
for UI display. Used primarily in global search results.
"""

import logging
from typing import Any
from flask import render_template, request, redirect, url_for, flash

from app.models.filters import MessageFilters
from app.services.messages_service import get_message_by_id
from app.services.chats_service import get_chat_by_slug
from app.logs.messages_logs import log_message_view

logger = logging.getLogger(__name__)


def group_messages_by_chat(
    messages: list[dict]
) -> dict[str, dict[str, Any]]:
    """
    Group message dicts by chat slug.

    Each group contains the chat's name and list of corresponding messages.
    Skips messages without a valid 'chat_slug'.

    :param messages: List of message dicts with 'chat_slug' and 'chat_name'.
    :return: Mapping {slug: {"chat_name": ..., "messages": [...]}}.
    """
    grouped: dict[str, dict[str, Any]] = {}

    for msg in messages:
        slug = msg.get("chat_slug")

        if not slug:
            logger.warning(
                "[GROUP|UTIL] Skipping message without chat_slug: id=%s",
                msg.get("id")
            )
            continue

        name = msg.get("chat_name") or slug

        if slug not in grouped:
            grouped[slug] = {
                "chat_name": name,
                "messages": [],
            }
        grouped[slug]["messages"].append(msg)

    logger.debug("[GROUP|UTIL] Grouped %d chat(s) from %d message(s)",
                 len(grouped), len(messages))
    return grouped


def render_message_view(chat_slug: str, pk: int) -> str:
    """
    Render full message view with back URL and context.

    :param chat_slug: Chat slug.
    :param pk: Message id.
    :return: Rendered HTML string.
    """
    chat = get_chat_by_slug(chat_slug)
    message = get_message_by_id(pk)
    if not chat or not message or message.chat_ref_id != chat.id:
        flash("Message not found in this chat.", "error")
        return redirect(url_for("chats.view_chat", slug=chat_slug))

    log_message_view(
        pk, chat.slug, message.timestamp,
        message.get_short_text(10)
    )

    filters = MessageFilters.from_request(request)

    from_search = bool(request.args.get("from_search"))
    from_chats = bool(request.args.get("from_chats"))

    if from_search:
        back_url = url_for("search.global_search", **filters.to_query_args())
        back_label = "Back to Search"
    elif from_chats:
        back_url = url_for("chats.list_chats")
        back_label = "Back to Chats"
    else:
        back_url = url_for("chats.view_chat", slug=chat.slug,
                           **filters.to_query_args())
        back_label = "Back to Chat"

    return render_template(
        "messages/view.html",
        message=message,
        chat=chat,
        filters=filters,
        back_url=back_url,
        back_label=back_label
    )
