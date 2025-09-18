"""
Configuration classes for the Arcanum application.

Handles environment-specific settings, validates required variables,
and prepares runtime configuration for extensions.

Required environment variables:
- FLASK_SECRET_KEY: Secret key for sessions and CSRF protection.
- APP_ADMIN_PASSWORD: Password for single-user access.
- DB_BACKEND: Which database backend to use ('sqlite' or 'postgres').
- SQLITE_PATH: Path to SQLite database file (required if DB_BACKEND=sqlite).
- POSTGRES_URL: PostgreSQL connection URI (required if DB_BACKEND=postgres).
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

    # === Database / SQLAlchemy Settings ===
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

        Performs initialization of:
          - Database backend (SQLite or PostgreSQL) and SQLAlchemy URI
          - Core application secrets (Flask secret key, admin password)
          - Optional third-party integrations (Cloudinary, Backblaze B2)
          - CSRF secret fallback

        :param app: Flask app instance.
        :raises ConfigValidationError: If required settings are missing
                                       or invalid.
        :raises RuntimeError: If Backblaze config is incomplete.
        """

        # Database
        cls._configure_database(app)

        # Core secrets
        cls._validate_secret_key(app)
        cls._validate_admin_password(app)
        cls._validate_cloudinary_config(app)
        cls._validate_backblaze_config(app)

        # CSRF secret
        cls._configure_csrf(app)

        logger.debug(
            "[CONFIG|INIT] Configuration applied for '%s' environment.",
            cls.ENV
        )

    # === Database ===
    @staticmethod
    def _configure_database(app: Flask) -> None:
        """
        Configure SQLAlchemy database URI based on DB_BACKEND.

        Supported values:
        - DB_BACKEND=sqlite: requires SQLITE_PATH (absolute file path)
        - DB_BACKEND=postgres: requires POSTGRES_URL (full URI)

        :param app: Flask app instance.
        :raises ConfigValidationError: If DB_BACKEND is unsupported
                                       or required variables are missing.
        """
        db_backend = os.getenv("DB_BACKEND", "sqlite").lower()

        if db_backend == "sqlite":
            sqlite_path = os.getenv(
                "SQLITE_PATH",
                os.path.join(basedir, "..", "data", "chatvault.sqlite"),
            )
            app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

        elif db_backend == "postgres":
            postgres_url = os.getenv("POSTGRES_URL")
            if not postgres_url:
                logger.error(
                    "[CONFIG|VALIDATION] 'POSTGRES_URL' must be set "
                    "when DB_BACKEND=postgres."
                )
                raise ConfigValidationError(
                    "'POSTGRES_URL' must be set when DB_BACKEND=postgres."
                )
            app.config["SQLALCHEMY_DATABASE_URI"] = postgres_url

        else:
            logger.error(
                "[CONFIG|VALIDATION] Unsupported DB_BACKEND='%s'. "
                "Use 'sqlite' or 'postgres'.",
                db_backend,
            )
            raise ConfigValidationError(
                f"Unsupported DB_BACKEND: {db_backend}. "
                "Use 'sqlite' or 'postgres'."
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

    # === CSRF ===
    @staticmethod
    def _configure_csrf(app: Flask) -> None:
        """
        Configure CSRF secret key.

        Uses WTF_CSRF_SECRET_KEY if provided, otherwise falls back to
        the main Flask SECRET_KEY.
        """
        app.config["WTF_CSRF_SECRET_KEY"] = os.getenv(
            "WTF_CSRF_SECRET_KEY",
            app.config["SECRET_KEY"]
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
