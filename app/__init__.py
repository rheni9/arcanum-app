"""
Application factory for the Arcanum Flask application.

Initializes app configuration, logging, CSRF, blueprints, Jinja filters,
and global request hooks.
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
    Create and configure the Flask application.

    :param config_class: Optional config class.
                         Determined by FLASK_ENV if None.
    :type config_class: type
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

    app.jinja_env.filters["datetimeformat"] = datetimeformat
    app.jinja_env.filters["dateonlyformat"] = dateonlyformat

    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chats_bp, url_prefix="/chats")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(search_bp, url_prefix="/search")

    app.before_request(restrict_access)

    return app
