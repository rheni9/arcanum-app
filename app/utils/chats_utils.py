"""
Chat utilities for the Arcanum application.

Provides helper functions for processing filtered chat views,
including tag redirection, filter application, result loading,
and structured logging for AJAX and full-page views.
"""

import logging
from flask import render_template, request, redirect, url_for, Response

from app.models.chat import Chat
from app.models.filters import MessageFilters
from app.services.chats_service import get_chats, get_global_stats
from app.services.messages_service import (
    get_messages_by_chat_slug, count_messages_in_chat
)
from app.services.filters_service import (
    resolve_message_query, normalize_filter_action
)
from app.utils.sort_utils import get_sort_order
from app.utils.backblaze_utils import generate_signed_s3_url
from app.logs.chats_logs import log_chat_list, log_chat_view

logger = logging.getLogger(__name__)


def render_chat_list() -> str:
    """
    Render full chat list or AJAX table fragment.

    :return: HTML response for chat list.
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"name", "message_count", "last_message"},
        default_field="last_message",
        default_order="desc"
    )

    chats = get_chats(sort_by, order)
    stats = get_global_stats()

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    template = "chats/_chats_table.html" if is_ajax else "chats/index.html"

    log_chat_list(len(chats), sort_by, order, is_ajax)

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


def render_chat_view(chat: Chat) -> str | Response:
    """
    Render chat view or AJAX fragment with filters applied.

    :param chat: Chat object.
    :return: HTML response (full or partial).
    """
    sort_by, order = get_sort_order(
        request.args.get("sort"),
        request.args.get("order"),
        allowed_fields={"timestamp", "msg_id", "text"},
        default_field="timestamp",
        default_order="desc"
    )

    filters = MessageFilters.from_request(request)
    filters.chat_slug = chat.slug
    normalize_filter_action(filters)

    if (
        filters.action == "search"
        and filters.query
        and filters.query.strip().startswith("#")
    ):
        return _redirect_tag_search(chat.slug, filters.query)

    messages, count, info_message = _resolve_messages(chat.slug, filters,
                                                      sort_by, order)

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    template = "chats/_messages_table.html" if is_ajax else "chats/view.html"

    log_chat_view(chat.slug, filters, count, is_ajax)

    # Generate signed URL for chat image
    signed_image_url = ""
    if chat.image:
        signed_image_url = generate_signed_s3_url(chat.image)

    return render_template(
        template,
        chat=chat,
        messages=messages,
        total_count=count_messages_in_chat(chat.id),
        sort_by=sort_by,
        order=order,
        filters=filters,
        info_message=info_message,
        signed_image_url=signed_image_url,
        search_action=url_for("chats.view_chat", slug=chat.slug),
        clear_url=url_for("chats.view_chat", slug=chat.slug),
        extra_args=_get_extra_args(),
        from_chats=bool(request.args.get("from_chats")),
    )


def _redirect_tag_search(slug: str, query: str) -> Response:
    """
    Redirect to tag-based search.

    :param slug: Chat slug.
    :param query: Raw user query.
    :return: Redirect response.
    """
    tag = query.strip().lstrip("#")
    return redirect(
        url_for("chats.view_chat", slug=slug, action="tag", tag=tag)
    )


def _resolve_messages(
    slug: str,
    filters: MessageFilters,
    sort_by: str,
    order: str
) -> tuple[list, int, str | None]:
    """
    Retrieve messages according to filters and sorting.

    :param slug: Chat slug.
    :param filters: Parsed filter object.
    :param sort_by: Field to sort by.
    :param order: Sort direction.
    :return: Tuple of (messages, count, info message).
    """
    if not filters.action:
        messages = get_messages_by_chat_slug(slug, sort_by, order)
        return messages, len(messages), None

    status, context = resolve_message_query(filters, sort_by, order)

    if status == "invalid":
        return [], 0, context["info_message"]
    if status == "cleared":
        messages = get_messages_by_chat_slug(slug, sort_by, order)
        return messages, len(messages), context["info_message"]

    return context["messages"], context["count"], context["info_message"]


def _get_extra_args() -> dict:
    """
    Extract non-filter extra arguments from request.

    :return: Dictionary of query args.
    """
    args = request.args.to_dict(flat=True)
    args.pop("chat_slug", None)
    return args
