"""
Application entry point for the Arcanum Flask application.

Initializes the Flask app using the factory pattern.
Defines global error handlers (CSRF, 405, 404, 500).
Runs the development server if executed as the main module.
"""

import os
from flask import flash, redirect, url_for, render_template, request, Response
from flask_wtf.csrf import CSRFError

from app import create_app

app = create_app()


@app.errorhandler(CSRFError)
def handle_csrf_error(_e: CSRFError) -> Response:
    """
    Handle missing or invalid CSRF token.

    Displays a flash message and redirects the user to the previous page
    or to the homepage if referrer is not available.

    :param _e: CSRFError exception instance.
    :type _e: CSRFError
    :returns: Redirect response with a flash message.
    :rtype: Response
    """
    flash(
        "Your session has expired or the form was tampered with. "
        "Please try again.",
        "error"
    )
    target = request.referrer or url_for("home.home")
    return redirect(target)


@app.errorhandler(405)
def handle_method_not_allowed(_e: Exception) -> Response:
    """
    Handle HTTP 405 Method Not Allowed errors.

    Renders an error page indicating the method is not allowed.

    :param _e: Exception instance.
    :type _e: Exception
    :returns: Rendered error page with 405 status code.
    :rtype: Response
    """
    return render_template(
        "error.html",
        message="The method is not allowed for this action."
    ), 405


@app.errorhandler(404)
def handle_not_found(_e: Exception) -> Response:
    """
    Handle HTTP 404 Not Found errors.

    Renders an error page indicating the page was not found.

    :param _e: Exception instance.
    :type _e: Exception
    :returns: Rendered error page with 404 status code.
    :rtype: Response
    """
    return render_template(
        "error.html",
        message="The requested page was not found."
    ), 404


@app.errorhandler(500)
def handle_internal_server_error(_e: Exception) -> Response:
    """
    Handle HTTP 500 Internal Server errors.

    Renders an error page indicating an unexpected error occurred.

    :param _e: Exception instance.
    :type _e: Exception
    :returns: Rendered error page with 500 status code.
    :rtype: Response
    """
    return render_template(
        "error.html",
        message="An unexpected error occurred. Please try again later."
    ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = app.config.get("DEBUG", False)
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
