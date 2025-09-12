"""
Authentication routes for the Arcanum application.

Provides endpoints for login and logout, CSRF protection, session
management, and authentication feedback.
"""

import logging
from flask import (
    Blueprint, current_app, render_template, jsonify,
    redirect, url_for, session, flash, Response
)
from flask_babel import _

from app.forms.auth_form import AuthForm

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
    form = AuthForm()

    if form.validate_on_submit():
        logger.debug("[AUTH|LOGIN] Login form submitted.")
        expected_password = current_app.config["APP_ADMIN_PASSWORD"]

        if form.password.data == expected_password:
            session["logged_in"] = True
            logger.info("[AUTH|LOGIN] Login successful.")
            flash(_("You have been logged in successfully."), "success")
            return redirect(url_for("dashboard.dashboard"))

        logger.warning("[AUTH|LOGIN] Incorrect password.")
        flash(_("Password is incorrect."), "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout() -> tuple[Response, int]:
    """
    Log out the user by clearing the session.

    Returns a JSON response containing the redirect URL and
    HTTP status code 200, intended for AJAX logout handling.

    :return: Tuple of (JSON response with redirect URL, status code).
    """
    session.pop("logged_in", None)
    logger.info("[AUTH|LOGOUT] Logout successful.")
    flash(_("You have been logged out successfully."), "success")
    return jsonify({"redirect": url_for("home.home")}), 200
