"""
Decorators for route-level error handling and resource retrieval.

Used to avoid repeating database lookups and error handling in route functions.

Includes tools for:
- validation that a chat exists for a given slug.
- automatic injection of chat object into Flask's `g` context.
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
    Decorator for routes that require a valid chat slug.

    This decorator:
    - extracts the `slug` argument from the route URL,
    - attempts to retrieve the corresponding chat from the database,
    - stores the result in `g.chat` for use inside the view,
    - redirects to the chat list with an error message if the chat is missing.
    - renders an error page if a database error occurs.

    :param view_func: A Flask route handler that requires a `slug` argument.
    :type view_func: Callable
    :return: Wrapped function that injects `g.chat` or redirects with error.
    :rtype: Callable
    """
    @wraps(view_func)
    def wrapper(slug: str, *args, **kwargs):
        try:
            chat = get_chat_by_slug(slug)
        except sqlite3.DatabaseError as e:
            logger.error("[DB] Failed to retrieve chat '%s': %s", slug, e)
            return render_template(
                "error.html", message=f"Database error while loading chat: {e}"
            )

        if not chat:
            logger.warning("[NOTFOUND] Chat slug '%s' was not found.", slug)
            flash(
                f"Chat with slug '{slug}' was not found or has been deleted.",
                "error"
            )
            return redirect(url_for("chats.list_chats"))

        g.chat = chat
        return view_func(slug, *args, **kwargs)

    return wrapper
