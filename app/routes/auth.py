"""
Authentication routes for the Arcanum application.

Provides login and logout endpoints with CSRF protection,
session handling, flash messages, and authentication logging.
"""

import os
import logging
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, Response
)

from app.forms.auth_forms import LoginForm

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Response | str:
    """
    Render and process the login form.

    - GET: Display login form with CSRF token.
    - POST: Validate form, authenticate user, update session.

    :returns: Redirect to dashboard on success, or render form with errors.
    :rtype: Response | str
    """
    form = LoginForm()

    if form.validate_on_submit():
        logger.debug("[AUTH|LOGIN] Login form submitted.")
        expected_password = os.getenv("LOGIN_PASSWORD")

        if form.password.data == expected_password:
            session["logged_in"] = True
            logger.info("[AUTH|LOGIN] Login successful.")
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard.dashboard"))

        logger.warning("[AUTH|LOGIN] Incorrect password.")
        flash("Incorrect password.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Response:
    """
    Process user logout and clear the session.

    :returns: Redirect to homepage after logout.
    :rtype: Response
    """
    session.pop("logged_in", None)
    logger.info("[AUTH|LOGOUT] Logout successful.")
    flash("Logged out successfully.", "success")
    return redirect(url_for("home.home"))
