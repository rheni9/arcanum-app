"""
config.py

Configuration classes for the Arcanum Flask application.

Uses environment variables to manage settings for different environments.

Required environment variables:
- FLASK_SECRET_KEY    (required): Secret key for sessions and CSRF protection.
- DATABASE_URL        (required): Database URI
- LOG_LEVEL           (optional): Logging level
                      (DEBUG, INFO, WARNING, ERROR). Defaults to 'INFO'.
- FLASK_ENV           (optional): App environment
                      ('development', 'testing', 'production').
                      Defaults to 'production'.
- WTF_CSRF_SECRET_KEY (optional): Separate secret for WTForms CSRF.
                      Defaults to SECRET_KEY.
"""
import os

# Base directory for constructing default paths
basedir = os.path.abspath(os.path.dirname(__file__))


# pylint: disable=too-few-public-methods
class Config:
    """
    Base configuration with defaults and overrides.

    Attributes:
        SECRET_KEY (str): Main secret for sessions and CSRF.
        WTF_CSRF_SECRET_KEY (str): Secret for WTForms CSRF.
        WTF_CSRF_ENABLED (bool): Enable CSRF protection.
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
            "Environment variable FLASK_SECRET_KEY is required and not set."
        )
    SECRET_KEY = _key

    # CSRF configuration
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)
    WTF_CSRF_ENABLED = True

    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(basedir, '..', 'data', 'chatvault.sqlite')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask environment settings
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    """
    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """
    Testing environment configuration.
    """
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False  # disable CSRF in tests for convenience


class ProductionConfig(Config):
    """
    Production environment configuration.
    """
    ENV = "production"
    DEBUG = False
