"""
Entry point for the Arcanum Flask application.

Initializes the application, registers global error handlers,
and runs the development server.
"""

import sys
import logging
from flask import render_template, Response, Flask
from flask_wtf.csrf import CSRFError

from app import create_app
from app.config import ConfigValidationError
from app.hooks.csrf_hooks import handle_csrf_error

logger = logging.getLogger(__name__)


def initialize_application() -> object:
    """
    Initialize the Flask application.

    :return: Flask app instance.
    :raises RuntimeError: If application initialization fails.
    :raises ConfigValidationError: If configuration is invalid.
    """
    try:
        app_instance = create_app()
        logger.info("[RUN|INIT] Flask application instance created.")
        return app_instance
    except ConfigValidationError as e:
        logger.critical("[RUN|INIT] Configuration validation failed: %s", e)
        sys.exit(1)
    except RuntimeError as e:
        logger.critical("[RUN|INIT] Application failed to start: %s", e)
        raise


def get_server_config(flask_app: Flask) -> tuple[int, bool]:
    """
    Retrieve server configuration parameters.

    :param flask_app: Flask app instance.
    :return: Tuple containing the port and debug mode flag.
    """
    return (
        flask_app.config.get("PORT", 5000),
        flask_app.config.get("DEBUG", False)
    )


def render_error_page(
    status_code: int,
    message: str,
    exception: Exception
) -> Response:
    """
    Render a standardized error page and log the exception.

    Render a standardized error page and log the exception.

    :param status_code: HTTP status code to return.
    :param message: User-facing message for the error page.
    :param exception: Exception instance.
    :return: Rendered error page response.
    """
    level = logging.WARNING if status_code in (404, 405) else logging.ERROR
    logger.log(
        level,
        "[RUN|ERROR] HTTP %s encountered: %s",
        status_code,
        exception
    )
    return render_template("error.html", message=message), status_code


# Initialize the Flask app
app = initialize_application()


@app.errorhandler(CSRFError)
def csrf_error_handler(exception: CSRFError) -> Response:
    """
    Handle CSRF errors by delegating them to the shared handler.

    :param exception: CSRFError exception instance.
    :return: Redirect response with a flash message.
    """
    return handle_csrf_error(exception)


@app.errorhandler(404)
def handle_not_found(exception: Exception) -> Response:
    """
    Handle HTTP 404 Not Found errors.

    :param exception: Exception instance.
    :return: Rendered 404 error page.
    """
    return render_error_page(
        404,
        "The requested page was not found.",
        exception
    )


@app.errorhandler(405)
def handle_method_not_allowed(exception: Exception) -> Response:
    """
    Handle HTTP 405 Method Not Allowed errors.

    :param exception: Exception instance.
    :return: Rendered 405 error page.
    """
    return render_error_page(
        405,
        "The method is not allowed for this action.",
        exception
    )


@app.errorhandler(500)
def handle_internal_server_error(exception: Exception) -> Response:
    """
    Handle HTTP 500 Internal Server errors.

    :param exception: Exception instance.
    :return: Rendered 500 error page.
    """
    return render_error_page(
        500,
        "An unexpected error occurred. Please try again later.",
        exception
    )


# Start the Flask server
if __name__ == "__main__":
    port, debug_mode = get_server_config(app)
    logger.info(
        "[RUN|START] Starting Arcanum Flask server on port %s | Debug=%s",
        port,
        debug_mode
    )
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
