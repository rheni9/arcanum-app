"""
Authentication routes for the Arcanum application.

Provides endpoints for login and logout, CSRF protection, session
management, and authentication feedback.
"""

import logging
from flask import (
    Blueprint, current_app, render_template,
    redirect, url_for, session, flash, Response
)

from app.forms.auth_form import LoginForm

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Response | str:
    """
    Render and process the login form.

    On GET, render the login form with CSRF protection.
    On POST, validate the form, authenticate the user, update the session.

    :return: Redirect to dashboard on success, or render the form with errors.
    """
    form = LoginForm()

    if form.validate_on_submit():
        logger.debug("[AUTH|LOGIN] Login form submitted.")
        expected_password = current_app.config["APP_ADMIN_PASSWORD"]

        if form.password.data == expected_password:
            session["logged_in"] = True
            logger.info("[AUTH|LOGIN] Login successful.")
            flash("You have been logged in successfully.", "success")
            return redirect(url_for("dashboard.dashboard"))

        logger.warning("[AUTH|LOGIN] Incorrect password.")
        flash("Password is incorrect.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Response:
    """
    Log out the user and clear the session.

    :return: Redirect to homepage after logout.
    """
    session.pop("logged_in", None)
    logger.info("[AUTH|LOGOUT] Logout successful.")
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("home.home"))
