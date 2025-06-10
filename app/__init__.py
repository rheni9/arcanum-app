"""
Application factory for the Arcanum Flask application.

Creates and configures the Flask app instance, registers blueprints,
Jinja filters, global request hooks, logging, and CSRF protection.
"""

import os
import logging
from datetime import datetime

from flask import Flask
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.hooks.auth_hooks import restrict_access
from app.utils.logging_utils import configure_logging
from app.utils.time_utils import datetimeformat, dateonlyformat
from app.utils.db_utils import close_request_connection, ensure_db_exists
from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.chats import chats_bp
from app.routes.messages import messages_bp
from app.routes.search import search_bp

logger = logging.getLogger(__name__)

csrf = CSRFProtect()


def create_app(config_class: type = None) -> Flask:
    """
    Create and configure the Flask application instance.

    Loads environment variables, validates configuration, initializes
    logging, CSRF, blueprints, Jinja filters, and global hooks.

    :param config_class: Optional configuration class.
    :return: Configured Flask app instance.
    :raises ConfigValidationError: If required env variables are missing.
    """

    # Load environment variables (early logging)
    load_dotenv()
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    # Select configuration class if not provided
    if not config_class:
        config_class = {
            "development": DevelopmentConfig,
            "testing": TestingConfig,
        }.get(os.getenv("FLASK_ENV", "production"), ProductionConfig)

    logger.debug(
        "[CONFIG|INIT] Loaded configuration class: %s",
        config_class.__name__
    )

    # Initialize Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.context_processor
    def inject_current_year():
        """
        Inject the current year into Jinja templates as 'current_year'.

        Useful for footers or legal notices that require a dynamic year.
        """
        return {"current_year": datetime.utcnow().year}

    # Second-stage logging config (from app.config)
    configure_logging(app.config.get("LOG_LEVEL"))

    # Initialize configuration
    config_class.init_app(app)

    # Initialize CSRF protection
    csrf.init_app(app)

    # Ensure the database exists on startup
    with app.app_context():
        ensure_db_exists()

    _register_filters(app)
    _register_blueprints(app)

    # Enforce access restrictions globally
    app.before_request(restrict_access)

    @app.teardown_request
    def teardown_request(exception: Exception):
        """
        Close the database connection after each request.

        :param exception: Exception raised during request handling.
        """
        close_request_connection(exception)

    return app


def _register_filters(app: Flask) -> None:
    """
    Register custom Jinja filters.

    :param app: Flask app instance.
    """
    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["dateonlyformat"] = dateonlyformat


def _register_blueprints(app: Flask) -> None:
    """
    Register application blueprints.

    :param app: Flask app instance.
    """
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chats_bp, url_prefix="/chats")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(search_bp, url_prefix="/search")
