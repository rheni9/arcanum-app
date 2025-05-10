"""
Request access control middleware for the Arcanum application.

Defines a reusable `restrict_access()` function that protects authenticated
routes using session-based authorization. Public and static routes are
explicitly excluded from enforcement.

Features:
- Permits access to public routes and static assets.
- Enforces session-based login via `session["logged_in"]`.
- Designed for global use via Flask's `before_request` hook.
"""

import logging
from flask import request, redirect, session, url_for

logger = logging.getLogger(__name__)


def restrict_access():
    """
    Restrict access to authenticated views based on session state.

    Redirects unauthenticated users to the login page, unless the
    current route is explicitly allowed.

    Allowed endpoints:
    - 'home'
    - 'auth.login'
    - 'auth.logout'
    - 'static'

    :return: Redirect response to login page if unauthorized, otherwise None.
    :rtype: Optional[Response]
    """
    allowed_routes = {"home.home", "auth.login", "auth.logout", "static"}

    if request.endpoint is None:
        return None

    if not session.get("logged_in") and request.endpoint not in allowed_routes:
        logger.warning(
            "[AUTH] Unauthorized access attempt to '%s'", request.endpoint
        )
        return redirect(url_for("auth.login"))

    return None
