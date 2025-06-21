"""
Custom exception classes for the Arcanum application.

Defines application-specific errors used in services, validators,
and business logic.
"""


class DuplicateChatError(Exception):
    """Base class for chat duplication errors."""


class DuplicateChatIDError(DuplicateChatError):
    """Raised when the Telegram ID already exists."""


class DuplicateSlugError(DuplicateChatError):
    """Raised when the slug already exists."""


class DuplicateMessageError(Exception):
    """Raised when msg_id already exists within the same chat."""


class ChatNotFoundError(Exception):
    """Raised when a chat cannot be found by ID or slug."""


class MessageNotFoundError(Exception):
    """Raised when a message cannot be found for update or view."""
