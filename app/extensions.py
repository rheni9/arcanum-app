"""
Application extensions for the Arcanum Flask application.

Initializes the SQLAlchemy ORM for working with the database,
CSRFProtect for securing forms and requests, and Babel for
internationalization and localization across the application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_babel import Babel


db = SQLAlchemy()
csrf = CSRFProtect()
babel = Babel()
