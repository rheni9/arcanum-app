"""
Application factory for the Arcanum Flask application.

Initializes the Flask instance, loads configuration from environment,
registers Jinja filters, global hooks, and application blueprints.
"""

import os
from flask import Flask
from dotenv import load_dotenv

from app.utils.time_utils import datetimeformat, dateonlyformat
from app.utils.logging_utils import configure_logging
from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.chats import chats_bp
from app.routes.dashboard import dashboard_bp
from app.routes.search import search_bp
from app.hooks.auth_hooks import restrict_access


def create_app() -> Flask:
    """
    Create and configure the Flask application instance.

    Loads environment variables, applies logging configuration,
    registers Jinja filters, application blueprints, and request hooks.

    :return: A configured Flask application instance.
    :rtype: Flask
    """

    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)

    # Configure logging
    configure_logging()

    # Set secret key from environment
    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # Register Jinja2 filters
    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["dateonlyformat"] = dateonlyformat

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chats_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(search_bp)

    # Register global before-request hooks
    app.before_request(restrict_access)

    return app
