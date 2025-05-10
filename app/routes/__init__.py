"""
Blueprint registration for all route modules in the Arcanum application.

Initializes and registers application route blueprints, including:
- home (public landing page),
- auth (login/logout),
- dashboard (main panel),
- chats (chat CRUD and message view),
- search (global message filtering).

This module is intended to be imported in the main application factory.
"""

from .home import home_bp
from .auth import auth_bp
from .dashboard import dashboard_bp
from .chats import chats_bp
from .search import search_bp

__all__ = [
    "home_bp",
    "auth_bp",
    "dashboard_bp",
    "chats_bp",
    "search_bp",
]
