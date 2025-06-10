"""
CSRF error hook for the Arcanum application.

Handles CSRF validation errors globally with logging and redirection.
"""

import logging
from flask import flash, redirect, request, url_for, Response
from flask_wtf.csrf import CSRFError

logger = logging.getLogger(__name__)


def handle_csrf_error(exception: CSRFError) -> Response:
    """
    Handle CSRF validation errors globally.

    Logs the error, flashes a user message, and redirects the user to
    the referring page or home if unavailable.

    :param exception: CSRFError exception instance.
    :return: Redirect response with a flash message.
    """
    logger.error("[SECURITY|CSRF] CSRF validation failed: %s", exception)
    flash(
        "Your session has expired or the form was tampered with. "
        "Please refresh the page and try again.",
        "error"
    )
    return redirect(request.referrer or url_for("home.home"))
