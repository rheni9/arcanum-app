"""
Configuration classes for the Arcanum Flask application.

Manages environment-specific settings using environment variables.

Required:
- FLASK_SECRET_KEY: Main secret for sessions and CSRF.
- DATABASE_URL: Database URI.

Optional:
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO.
- FLASK_ENV: App environment (development, testing, production).
             Default: production.
- WTF_CSRF_SECRET_KEY: WTForms CSRF secret. Defaults to SECRET_KEY.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


# pylint: disable=too-few-public-methods
class Config:
    """
    Base application configuration.

    Attributes:
        SECRET_KEY (str): Secret for sessions and CSRF.
        WTF_CSRF_SECRET_KEY (str): Secret for WTForms CSRF.
        WTF_CSRF_ENABLED (bool): CSRF protection enabled.
        LOG_LEVEL (str): Root logger level.
        SQLALCHEMY_DATABASE_URI (str): DB connection string.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Disable change tracking.
        ENV (str): Flask environment name.
        DEBUG (bool): Debug mode flag.
        TESTING (bool): Testing mode flag.
    """
    _key = os.getenv("FLASK_SECRET_KEY")
    if not _key:
        raise RuntimeError(
            "Environment variable FLASK_SECRET_KEY is required but not set."
        )
    SECRET_KEY = _key
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)
    WTF_CSRF_ENABLED = True

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, '..', 'data', 'chatvault.sqlite')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False


class DevelopmentConfig(Config):
    """Configuration for development environment."""
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Configuration for testing environment."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # Disabled in tests for convenience


class ProductionConfig(Config):
    """Configuration for production environment."""
    ENV = "production"
    DEBUG = False
