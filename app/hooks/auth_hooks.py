"""
Access control hook for the Arcanum application.

Restricts access to protected routes based on authentication state.
"""

import logging
from flask import request, redirect, session, url_for, Response

logger = logging.getLogger(__name__)


def restrict_access() -> Response | None:
    """
    Restrict access to authenticated views.

    Redirects the user to the login page if not logged in and attempting to
    access a route outside the public allowlist.

    :return: Redirect response to login page if unauthorized, otherwise None.
    """
    allowed_routes = {
        "home.home",
        "auth.login",
        "auth.logout",
        "lang.set_language",
        "static"
    }

    # Do nothing if endpoint is missing (static file, etc)
    if request.endpoint is None:
        return None

    # Verify if user is authenticated
    if not session.get("logged_in") and request.endpoint not in allowed_routes:
        logger.info(
            "[AUTH|ACCESS] Unauthorized access attempted to '%s'",
            request.endpoint
        )
        return redirect(url_for("auth.login"))

    return None
