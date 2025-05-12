"""
Authentication routes for the Arcanum application.

Handles user login and logout using a password-based form.
Manages session state and access to authenticated views.
"""

import os
import logging
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, Response
)

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    """
    Handle user authentication via password-protected login form.

    Accepts POST requests to validate the provided password against
    the stored application secret.

    :returns: Redirect to dashboard if successful, or login form.
    :rtype: str | Response
    """
    if request.method == "POST":
        logger.debug("[AUTH] Received POST request for login form.")
        password = request.form.get("password")
        if password == os.getenv("LOGIN_PASSWORD"):
            session["logged_in"] = True
            logger.info("[AUTH] User logged in successfully.")
            flash("You have been successfully logged in.", "success")
            return redirect(url_for("dashboard.dashboard"))

        logger.warning("[AUTH] Failed login attempt with incorrect password.")
        flash("Incorrect password.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout() -> Response:
    """
    Log out the currently authenticated user and clear session data.

    :returns: Redirect to home page after logout.
    :rtype: Response
    """
    session.pop("logged_in", None)
    logger.info("[AUTH] User logged out and session cleared.")
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home.home"))
