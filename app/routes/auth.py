"""
app/routes/auth.py

Authentication routes for the Arcanum application.

Handles user login and logout using a password-based form.
Manages session state and access to authenticated views.
"""

import os
import logging
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
    Display login form and process submission.

    On GET: render login form with CSRF token.
    On POST: validate form, check password, set session.

    :returns: Redirect to dashboard or re-render login.
    :rtype: Response
    """
    form = LoginForm()
    if form.validate_on_submit():
        logger.debug("[AUTH] Processing login form.")
        if form.password.data == os.getenv("LOGIN_PASSWORD"):
            session["logged_in"] = True
            logger.info("[AUTH] User logged in successfully.")
            flash("You have been successfully logged in.", "success")
            return redirect(url_for("dashboard.dashboard"))

        logger.warning("[AUTH] Incorrect login attempt.")
        flash("Incorrect password.", "error")

    return render_template("auth/login.html", form=form)


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
