"""
Configuration classes for the Arcanum Flask application.

Defines environment-specific settings using environment variables.

Required:
- FLASK_SECRET_KEY: Main secret key for sessions and CSRF.
- DATABASE_URL: Database connection URI.

Optional:
- FLASK_ENV: Application environment ('development', 'testing', 'production').
             Defaults to 'production'.
- LOG_LEVEL: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR').
             Defaults to 'INFO'.
- WTF_CSRF_SECRET_KEY: Separate secret key for WTForms CSRF.
                       Defaults to FLASK_SECRET_KEY.
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


# pylint: disable=too-few-public-methods
class Config:
    """
    Base configuration class.

    Attributes:
        SECRET_KEY (str): Secret key for sessions and CSRF protection.
        WTF_CSRF_SECRET_KEY (str): CSRF secret key for WTForms.
        WTF_CSRF_ENABLED (bool): Enable CSRF protection for forms.
        LOG_LEVEL (str): Application logging level.
        SQLALCHEMY_DATABASE_URI (str): Database connection string.
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): Disable SQLAlchemy tracking.
        ENV (str): App environment ('development', 'testing', 'production').
        DEBUG (bool): Enable Flask debug mode.
        TESTING (bool): Enable testing mode.
    """
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "Environment variable 'FLASK_SECRET_KEY' is required but not set."
        )

    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)
    WTF_CSRF_ENABLED = True

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(
            basedir, "..", "data", "chatvault_new.sqlite"
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False


class DevelopmentConfig(Config):
    """
    Configuration for the development environment.

    Enables debug mode and development-specific settings.
    """
    ENV = "development"
    DEBUG = True


class TestingConfig(Config):
    """
    Configuration for the testing environment.

    Disables CSRF protection for easier testing.
    """
    ENV = "testing"
    DEBUG = False
    TESTING = True
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """
    Configuration for the production environment.

    Ensures debug mode is disabled.
    """
    ENV = "production"
    DEBUG = False
