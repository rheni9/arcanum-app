"""
run.py

Application entry point for the Arcanum Flask application.

- Initializes app via factory
- Defines global error handlers (CSRF, 405, 404, 500)
- Runs development server if script is main
"""

import os
from typing import Tuple
from flask import flash, redirect, url_for, render_template, Response
from flask_wtf.csrf import CSRFError

from app import create_app

app = create_app()


@app.errorhandler(CSRFError)
def handle_csrf_error(_e: CSRFError) -> Response:
    """
    Handle missing or invalid CSRF token by redirecting to login.

    :param _e: CSRFError exception instance.
    :type _e: CSRFError
    :return: Redirect response to the login page.
    :rtype: Response
    """
    flash(
        "Your session has expired or the form was tampered with. "
        "Please try again.",
        "error"
    )
    return redirect(url_for("auth.login"))


@app.errorhandler(405)
def method_not_allowed(_e: Exception) -> Tuple[str, int]:
    """
    Handle 405 Method Not Allowed errors.

    :param _e: Exception instance.
    :type _e: Exception
    :return: Rendered error page with 405 status.
    :rtype: Tuple[str, int]
    """
    return render_template(
        "error.html",
        message="The method is not allowed for this action."
    ), 405


@app.errorhandler(404)
def not_found(_e: Exception) -> Tuple[str, int]:
    """
    Handle 404 Not Found errors.

    :param _e: Exception instance.
    :type _e: Exception
    :return: Rendered error page and with status.
    :rtype: Tuple[str, int]
    """
    return render_template("error.html", message="Page not found."), 404


@app.errorhandler(500)
def internal_server_error(_e: Exception) -> Tuple[str, int]:
    """
    Handle 500 Internal Server Error.

    :param _e: Exception instance.
    :type _e: Exception
    :return: Rendered error page with 500 status.
    :rtype: Tuple[str, int]
    """
    return render_template(
        "error.html",
        message="An unexpected error occurred. Please try again later."
    ), 500


if __name__ == "__main__":
    # Default port 5000, override via PORT env var
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
