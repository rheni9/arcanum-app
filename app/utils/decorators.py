"""
Route-level decorators for Arcanum application.

Provides:
- validation of chat existence by slug,
- database error handling for chat lookups,
- automatic injection of chat object into Flask's g context.
"""

import logging
import sqlite3
from functools import wraps
from typing import Callable
from flask import redirect, url_for, render_template, flash, g

from app.services.chats_service import get_chat_by_slug

logger = logging.getLogger(__name__)


def catch_not_found(view_func: Callable) -> Callable:
    """
    Decorator for routes that operate on a chat identified by slug.

    Workflow:
    - Retrieves chat by slug and stores in g.chat.
    - If chat not found -> redirects to chat list with error.
    - On DB error -> renders error page with message.

    :param view_func: Route handler expecting slug as first argument.
    :type view_func: Callable
    :return: Wrapped route function.
    :rtype: Callable
    """
    @wraps(view_func)
    def wrapper(slug: str, *args, **kwargs):
        try:
            chat = get_chat_by_slug(slug)
        except sqlite3.DatabaseError as e:
            logger.error(
                "[DB|CHATS] Failed to retrieve chat '%s': %s", slug, e
            )
            return render_template(
                "error.html",
                message=f"Database error while loading chat: {e}"
            )

        if not chat:
            logger.warning("[CHATS|NOTFOUND] Slug '%s' not found.", slug)
            logger.warning("[NOTFOUND] Chat slug '%s' was not found.", slug)
            flash(
                f"Chat with slug '{slug}' was not found or has been deleted.",
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        g.chat = chat
        return view_func(slug, *args, **kwargs)

    return wrapper
