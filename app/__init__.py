"""
Application factory for the Arcanum Flask application.

Creates and configures the Flask app instance, loads environment variables,
applies validated configuration, initializes logging, database, Babel (i18n),
timezone, Cloudinary, Backblaze B2, CSRF protection, blueprints, filters,
and request hooks.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import boto3
from botocore.config import Config as BotoConfig
from pytz import timezone as PytzTimeZone

from flask import Flask
from cloudinary import config as cloudinary_config

from app.config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.hooks.auth_hooks import restrict_access
from app.utils.logging_utils import configure_logging
from app.utils.time_utils import datetimeformat, dateonlyformat
from app.utils.db_utils import close_request_connection, ensure_db_exists
from app.utils.i18n_utils import get_locale
from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.chats import chats_bp
from app.routes.messages import messages_bp
from app.routes.search import search_bp
from app.routes.lang import lang_bp
from app.extensions import db, csrf, babel

logger = logging.getLogger(__name__)


def create_app(config_class: type = None) -> Flask:
    """
    Create and configure the Flask application instance.

    Loads environment variables, configures logging, validates configuration,
    initializes extensions (database, Babel for i18n, CSRF), timezone,
    and third-party integrations (Cloudinary, Backblaze B2).
    Registers blueprints, Jinja filters, and request hooks.

    :param config_class: Optional configuration class.
    :return: Configured Flask app instance.
    :raises ConfigValidationError: If required env variables are missing.
    """

    # === Load Environment Variables from .env ===
    load_dotenv()
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    # === Select Configuration Class ===
    if not config_class:
        config_class = {
            "development": DevelopmentConfig,
            "testing": TestingConfig,
        }.get(os.getenv("FLASK_ENV", "production"), ProductionConfig)

    logger.debug("[CONFIG|INIT] Using config class: %s", config_class.__name__)

    # === Initialize Flask Application ===
    app = Flask(__name__)
    app.config.from_object(config_class)

    # === Initialize Database & Context Processors ===
    db.init_app(app)

    # === Initialize Babel ===
    babel.init_app(app, locale_selector=get_locale)
    logger.debug(
        "[BABEL|INIT] Babel configured | Languages=%s | Default=%s",
        app.config.get("LANGUAGES"),
        app.config.get("DEFAULT_LOCALE"),
    )

    @app.context_processor
    def inject_lang():
        """Inject current UI language code into all templates."""
        return {"lang": get_locale()}

    # === Initialize tz object from config ===
    app.config["DEFAULT_TZ"] = PytzTimeZone(app.config["DEFAULT_TZ_NAME"])

    @app.context_processor
    def inject_current_year():
        """Inject 'current_year' for all templates."""
        return {"current_year": datetime.utcnow().year}

    # === Re-configure Logging with App Settings ===
    configure_logging(app.config.get("LOG_LEVEL"))

    # === Validate & Apply Configuration ===
    config_class.init_app(app)

    # === Initialize Cloudinary ===
    cloudinary_config(
        cloud_name=app.config["CLOUDINARY_CLOUD_NAME"],
        api_key=app.config["CLOUDINARY_API_KEY"],
        api_secret=app.config["CLOUDINARY_API_SECRET"]
    )
    logger.debug("[CLOUDINARY|INIT] Cloudinary configured successfully.")

    # === Initialize Backblaze B2 S3 ===
    app.s3_client = boto3.client(
        "s3",
        endpoint_url=app.config["B2_S3_ENDPOINT_URL"],
        aws_access_key_id=app.config["B2_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=app.config["B2_S3_SECRET_ACCESS_KEY"],
        config=BotoConfig(signature_version="s3v4")
    )
    logger.debug("[B2|INIT] Backblaze B2 S3 client initialized successfully.")

    # === Initialize CSRF Protection ===
    csrf.init_app(app)

    # === Ensure Database Exists ===
    with app.app_context():
        ensure_db_exists()

    # === Register Filters & Blueprints ===
    _register_filters(app)
    _register_blueprints(app)

    # === Global Request Hooks ===
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
    app.register_blueprint(lang_bp)
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(chats_bp, url_prefix="/chats")
    app.register_blueprint(messages_bp, url_prefix="/messages")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(search_bp, url_prefix="/search")
