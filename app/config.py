"""
Configuration classes for the Arcanum application.

Handles environment-specific settings, validates required variables,
and prepares runtime configuration for extensions.

Required environment variables:
- FLASK_SECRET_KEY: Secret key for sessions and CSRF protection.
- APP_ADMIN_PASSWORD: Password for single-user access.
- DATABASE_URL: Database connection URI (optional fallback provided).
- Backblaze B2 S3 keys: B2_S3_ENDPOINT_URL, B2_S3_BUCKET_NAME,
                        B2_S3_ACCESS_KEY_ID, B2_S3_SECRET_ACCESS_KEY.

Optional environment variables:
- DEFAULT_TIMEZONE: Default timezone name for UI and date/time conversions
                    (defaults to 'Europe/Kyiv').
- APP_LANGUAGES: Comma-separated list of supported languages.
- APP_DEFAULT_LOCALE: Default locale code (defaults to 'en').
- FLASK_ENV: Application environment ('development', 'testing', 'production').
- LOG_LEVEL: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
- WTF_CSRF_SECRET_KEY: Secret key for WTForms CSRF
                       (defaults to FLASK_SECRET_KEY).
- FORCE_HTTPS: Force HTTPS redirection ('true' or 'false').
- PORT: Custom Flask server port (defaults to 5000).
- APP_ROOT_DIR: Application root directory (absolute path).
- Cloudinary keys.
"""

import os
import logging
from flask import Flask

basedir = os.path.abspath(os.path.dirname(__file__))
logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when critical configuration is missing or invalid."""


# pylint: disable=too-few-public-methods
class Config:
    """
    Base configuration for the Arcanum application.

    Defines defaults and environment-specific flags.
    """

    # === Database ===
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, '..', 'data', 'chatvault.sqlite')}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,   # 30 min
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # === Core App Flags ===
    WTF_CSRF_ENABLED = True
    FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    PORT = int(os.getenv("PORT", "5000"))
    APP_ROOT_DIR = os.getenv(
        "APP_ROOT_DIR",
        os.path.abspath(os.path.join(basedir, ".."))
    )

    # === Timezone ===
    DEFAULT_TZ_NAME = os.getenv("DEFAULT_TIMEZONE", "Europe/Kyiv")
    BABEL_DEFAULT_TIMEZONE = DEFAULT_TZ_NAME

    # === Localization / i18n ===
    LANGUAGES = os.getenv("APP_LANGUAGES", "en,uk").split(",")
    DEFAULT_LOCALE = os.getenv("APP_DEFAULT_LOCALE", "en_GB")
    BABEL_TRANSLATION_DIRECTORIES = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "..",
        "translations"
    )
    BABEL_DEFAULT_DOMAIN = "messages"

    # === Environment Flags ===
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False

    # === Runtime Initialization ===
    @classmethod
    def init_app(cls: type, app: Flask) -> None:
        """
        Validate and apply runtime configuration.

        Loads secrets, Cloudinary, and Backblaze B2 configs.

        :param app: Flask app instance.
        :raises ConfigValidationError: If required settings are missing.
        :raises RuntimeError: If Backblaze config is incomplete.
        """

        # Core secrets
        cls._validate_secret_key(app)
        cls._validate_admin_password(app)
        cls._validate_cloudinary_config(app)
        cls._validate_backblaze_config(app)

        # CSRF secret fallback
        app.config["WTF_CSRF_SECRET_KEY"] = os.getenv(
            "WTF_CSRF_SECRET_KEY",
            app.config["SECRET_KEY"]
        )

        logger.debug(
            "[CONFIG|INIT] Configuration applied for '%s' environment.",
            cls.ENV
        )

    # === Secret Key ===
    @staticmethod
    def _validate_secret_key(app: Flask) -> None:
        """
        Ensure that FLASK_SECRET_KEY is set.

        :param app: Flask app instance.
        :raises ConfigValidationError: If secret key is missing.
        """
        app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
        if not app.config["SECRET_KEY"]:
            logger.error("[CONFIG|VALIDATION] 'FLASK_SECRET_KEY' is missing.")
            raise ConfigValidationError(
                "'FLASK_SECRET_KEY' must be set in environment variables."
            )

    # === Admin Password ===
    @staticmethod
    def _validate_admin_password(app: Flask) -> None:
        """
        Ensure that APP_ADMIN_PASSWORD is set.

        :param app: Flask app instance.
        :raises ConfigValidationError: If admin password is missing.
        """
        app.config["APP_ADMIN_PASSWORD"] = os.getenv("APP_ADMIN_PASSWORD")
        if not app.config["APP_ADMIN_PASSWORD"]:
            logger.error(
                "[CONFIG|VALIDATION] 'APP_ADMIN_PASSWORD' is missing."
            )
            raise ConfigValidationError(
                "'APP_ADMIN_PASSWORD' must be set in environment variables."
            )

    # === Cloudinary ===
    @staticmethod
    def _validate_cloudinary_config(app: Flask) -> None:
        """
        Load and validate Cloudinary configuration.

        Logs a warning if required Cloudinary env variables are missing.

        :param app: Flask app instance.
        """
        app.config["CLOUDINARY_CLOUD_NAME"] = os.getenv(
            "CLOUDINARY_CLOUD_NAME"
        )
        app.config["CLOUDINARY_API_KEY"] = os.getenv("CLOUDINARY_API_KEY")
        app.config["CLOUDINARY_API_SECRET"] = os.getenv(
            "CLOUDINARY_API_SECRET"
        )

        if not all([
            app.config["CLOUDINARY_CLOUD_NAME"],
            app.config["CLOUDINARY_API_KEY"],
            app.config["CLOUDINARY_API_SECRET"]
        ]):
            logger.warning(
                "[CONFIG|INIT] Cloudinary configuration is incomplete."
            )

    # === Backblaze B2 ===
    @staticmethod
    def _validate_backblaze_config(app: Flask) -> None:
        """
        Load and validate Backblaze B2 S3 configuration.

        :param app: Flask app instance.
        :raises RuntimeError: if required Backblaze env variables are missing.
        """
        app.config["B2_S3_ENDPOINT_URL"] = os.getenv("B2_S3_ENDPOINT_URL")
        app.config["B2_S3_BUCKET_NAME"] = os.getenv("B2_S3_BUCKET_NAME")
        app.config["B2_S3_ACCESS_KEY_ID"] = os.getenv("B2_S3_ACCESS_KEY_ID")
        app.config["B2_S3_SECRET_ACCESS_KEY"] = os.getenv(
            "B2_S3_SECRET_ACCESS_KEY"
        )

        if not all([
            app.config["B2_S3_ENDPOINT_URL"],
            app.config["B2_S3_BUCKET_NAME"],
            app.config["B2_S3_ACCESS_KEY_ID"],
            app.config["B2_S3_SECRET_ACCESS_KEY"]
        ]):
            logger.critical(
                "[CONFIG|INIT] Backblaze B2 configuration is incomplete!"
            )
            raise RuntimeError("Backblaze B2 S3 configuration is incomplete!")


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    ENV = "development"
    DEBUG = True


class TestingConfig(Config):
    """Configuration for testing environment."""
    ENV = "testing"
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Configuration for production environment."""
    ENV = "production"
    DEBUG = False
