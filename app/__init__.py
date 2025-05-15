"""
Application factory for the Arcanum Flask application.

Initializes configuration, logging, CSRF protection, blueprints,
Jinja filters, and global request hooks.
"""

import os
import logging
from flask import Flask
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.utils.time_utils import datetimeformat, dateonlyformat
from app.utils.logging_utils import configure_logging
from app.utils.db_utils import close_request_connection, ensure_db_exists
from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.chats import chats_bp
from app.routes.messages import messages_bp
from app.routes.search import search_bp
from app.hooks.auth_hooks import restrict_access

logger = logging.getLogger(__name__)

csrf = CSRFProtect()


def create_app(config_class=None) -> Flask:
    """
    Create and configure the Flask application instance.

    :param config_class: Optional configuration class.
                         Determined by FLASK_ENV if not provided.
    :type config_class: type | None
    :returns: Configured Flask app instance.
    :rtype: Flask
    """
    load_dotenv()

    if not config_class:
        env = os.getenv("FLASK_ENV", "production")
        if env == "development":
            config_class = DevelopmentConfig
        elif env == "testing":
            config_class = TestingConfig
        else:
            config_class = ProductionConfig

    app = Flask(__name__)
    app.config.from_object(config_class)

    csrf.init_app(app)
    configure_logging(app.config.get("LOG_LEVEL"))

    with app.app_context():
        ensure_db_exists()

    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["dateonlyformat"] = dateonlyformat

    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chats_bp, url_prefix="/chats")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(search_bp, url_prefix="/search")

    app.before_request(restrict_access)

    @app.teardown_request
    def teardown_request(exception):
        """
        Close database connection after each request.

        :param exception: Exception raised during request handling.
        :type exception: Exception | None
        """
        close_request_connection(exception)

    return app
