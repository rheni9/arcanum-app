"""
CSRF error handler hook for the Arcanum Flask application.

Handles global handling of CSRF validation errors.
"""

import logging
from flask import flash, redirect, request, url_for, Response
from flask_wtf.csrf import CSRFError

logger = logging.getLogger(__name__)


def handle_csrf_error(exception: CSRFError) -> Response:
    """
    Handle CSRF token validation errors.

    Logs the error, flashes a user-friendly message, and redirects the user
    to the referrer or the home page.

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
