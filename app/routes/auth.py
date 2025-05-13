"""
Authentication routes for the Arcanum application.

Provides login and logout endpoints.
Handles CSRF protection, session state,
flash messages, and authentication logging.
"""

import logging
from os import getenv
from flask import (
    Blueprint, render_template, redirect,
    url_for, session, flash, Response
)

from app.forms.auth_forms import LoginForm

auth_bp = Blueprint("auth", __name__, template_folder="../../templates/auth")
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Response:
    """
    Render and process the login form.

    - GET: Display login form with CSRF token.
    - POST: Validate form, authenticate user, update session.

    :returns: Redirect to dashboard on success, or re-render form.
    :rtype: Response
    """
    form = LoginForm()
    if form.validate_on_submit():
        logger.debug("[AUTH|LOGIN] Processing login form submission.")
        if form.password.data == getenv("LOGIN_PASSWORD"):
            session["logged_in"] = True
            logger.info("[AUTH|LOGIN] User logged in successfully.")
            flash("Successfully logged in.", "success")
            return redirect(url_for("dashboard.dashboard"))
        logger.warning("[AUTH|LOGIN] Incorrect password entered.")
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
    logger.info("[AUTH|LOGOUT] User logged out successfully.")
    flash("Successfully logged out.", "success")
    return redirect(url_for("home.home"))
