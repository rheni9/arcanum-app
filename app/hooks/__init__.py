"""
Authentication hook package for the Arcanum application.

Imports request lifecycle handlers for authentication checks and CSRF errors.
"""

from .auth_hooks import restrict_access  # noqa: F401
from .csrf_hooks import handle_csrf_error  # noqa: F401
