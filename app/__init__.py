"""
Application factory for the Arcanum Flask application.

Creates and configures the Flask app:
- Loads environment variables
- Applies configuration from config classes
- Initializes CSRF protection
- Sets up logging
- Registers Jinja filters, blueprints, and global hooks
"""

import os
from flask import Flask
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.utils.time_utils import datetimeformat, dateonlyformat
from app.utils.logging_utils import configure_logging
from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.chats import chats_bp
from app.routes.dashboard import dashboard_bp
from app.routes.search import search_bp
from app.hooks.auth_hooks import restrict_access

# Initialize CSRF protection
csrf = CSRFProtect()


def create_app(config_class=None) -> Flask:
    """
    Create and configure the Flask application instance.

    :param config_class: Optional config class to use (dev, test, prod).
    :type config_class: class
    :return: Configured Flask application.
    :rtype: Flask
    """

    # Load environment variables from .env file
    load_dotenv()

    # Determine config class if not provided
    if not config_class:
        env = os.getenv("FLASK_ENV", "production")
        if env == "development":
            config_class = DevelopmentConfig
        elif env == "testing":
            config_class = TestingConfig
        else:
            config_class = ProductionConfig

    # Create Flask app and load configuration
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF and logging
    csrf.init_app(app)
    configure_logging(app.config.get("LOG_LEVEL", "INFO"))

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
