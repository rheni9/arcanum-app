"""
Application entry point.

This module initializes the Flask application using the factory pattern
and defines global error handlers for common HTTP errors.
"""

import os
from flask import render_template
from app import create_app

app = create_app()


@app.errorhandler(405)
def method_not_allowed(_e):
    """
    Handle 405 Method Not Allowed errors.

    :param e: Exception object
    :type e: Exception
    :returns: Rendered error page with HTTP 405 status code
    :rtype: tuple[str, int]
    """
    return render_template(
        "error.html",
        message="The method is not allowed for this action."
    ), 405


@app.errorhandler(404)
def not_found(_e):
    """
    Handle 404 Not Found errors.

    :param e: Exception object
    :type e: Exception
    :returns: Rendered error page with HTTP 404 status code
    :rtype: tuple[str, int]
    """
    return render_template(
        "error.html",
        message="Page not found."
    ), 404


@app.errorhandler(500)
def internal_server_error(_e):
    """
    Handle 500 Internal Server Error.

    :param e: Exception object
    :type e: Exception
    :returns: Rendered error page with HTTP 500 status code
    :rtype: tuple[str, int]
    """
    return render_template(
        "error.html",
        message="An unexpected error occurred. Please try again later."
    ), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
