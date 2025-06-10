"""
Configuration classes for the Arcanum Flask application.

Supports development, testing, and production environments.
Handles environment variable validation and application settings.

Required environment variables:
- FLASK_SECRET_KEY: Secret key for sessions and CSRF protection.
- APP_ADMIN_PASSWORD: Password for single-user access.
- DATABASE_URL: Database connection URI (optional fallback provided).

Optional environment variables:
- FLASK_ENV: Application environment ('development', 'testing',
             'production'). Defaults to 'production'.
- LOG_LEVEL: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
             Defaults to 'INFO'.
- WTF_CSRF_SECRET_KEY: Secret key for WTForms CSRF.
                       Defaults to FLASK_SECRET_KEY.
- FORCE_HTTPS: Force HTTPS redirection ('true' or 'false').
               Defaults to 'false'.
- PORT: Custom Flask server port. Defaults to 5000.
- APP_ROOT_DIR: Application root directory (absolute path).
                Defaults to the project base directory.
"""

import os
import logging
from flask import Flask

basedir = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Represents a configuration validation error."""


# pylint: disable=too-few-public-methods
class Config:
    """
    Represents the base configuration class.

    Provides default and environment-specific settings.
    """

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        (
            "sqlite:///" + os.path.join(
                basedir, "..", "data", "chatvault_new4.sqlite"
            )
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Optional app settings
    WTF_CSRF_ENABLED = True
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    APP_ROOT_DIR = os.getenv(
        "APP_ROOT_DIR", os.path.abspath(os.path.join(basedir, ".."))
    )
    PORT = int(os.getenv("PORT", "5000"))

    # Flask runtime
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False

    @classmethod
    def init_app(cls: type, app: Flask) -> None:
        """
        Validate required environment variables and apply defaults.

        :param app: Flask app instance.
        :raises ConfigValidationError: If required env variables are missing.
        """
        cls._validate_secret_key(app)
        cls._validate_admin_password(app)

        app.config["WTF_CSRF_SECRET_KEY"] = os.getenv(
            "WTF_CSRF_SECRET_KEY",
            app.config["SECRET_KEY"]
        )

        logger.debug(
            "[CONFIG|INIT] Configuration applied for '%s' environment.",
            cls.ENV
        )

    @staticmethod
    def _validate_secret_key(app: Flask) -> None:
        """
        Validate that the secret key is set.

        :param app: Flask app instance.
        :raises ConfigValidationError: If secret key is missing.
        """
        app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
        if not app.config["SECRET_KEY"]:
            logger.error("[CONFIG|VALIDATION] 'FLASK_SECRET_KEY' is missing.")
            raise ConfigValidationError(
                "Environment variable 'FLASK_SECRET_KEY' is required "
                "but not set."
            )

    @staticmethod
    def _validate_admin_password(app: Flask) -> None:
        """
        Validate that the admin password is set.

        :param app: Flask app instance.
        :raises ConfigValidationError: If admin password is missing.
        """
        app.config["APP_ADMIN_PASSWORD"] = os.getenv("APP_ADMIN_PASSWORD")
        if not app.config["APP_ADMIN_PASSWORD"]:
            logger.error(
                "[CONFIG|VALIDATION] 'APP_ADMIN_PASSWORD' is missing."
            )
            raise ConfigValidationError(
                "Environment variable 'APP_ADMIN_PASSWORD' is required "
                "but not set."
            )


class DevelopmentConfig(Config):
    """
    Represents the configuration for the development environment.
    """
    ENV = "development"
    DEBUG = True


class TestingConfig(Config):
    """
    Represents the configuration for the testing environment.

    Disables CSRF protection for easier testing.
    """
    ENV = "testing"
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """
    Represents the configuration for the production environment.
    """
    ENV = "production"
    DEBUG = False
