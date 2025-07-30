"""
Database extension for the Arcanum Flask application.

Initializes SQLAlchemy ORM instance for use across the application.
"""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
