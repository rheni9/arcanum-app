"""
Route registrations for the Arcanum application.

Exposes all blueprint instances for use in the application factory.
"""

from app.routes.home import home_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.chats import chats_bp
from app.routes.search import search_bp

__all__ = [
    "home_bp",
    "auth_bp",
    "dashboard_bp",
    "chats_bp",
    "search_bp"
]
