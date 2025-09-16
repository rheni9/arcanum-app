"""
Custom exception classes for the Arcanum application.

Defines application-specific errors used in services, validators,
and business logic.
"""


class AppError(Exception):
    """
    Base class for all custom application errors.

    :param message: Description of the error.
    :param params: Optional extra context (e.g., slug, chat_id).
    """
    code = "app_error"

    def __init__(self, message: str | None = None, **params):
        self.params = params
        self.message = message or self.__class__.__name__
        super().__init__(self.message)

    def __str__(self):
        return self.message


class DuplicateChatIDError(AppError):
    """
    Raised when the Telegram ID already exists.

    :param chat_id: Conflicting Telegram chat ID.
    """
    code = "duplicate_chat_id"

    def __init__(self, chat_id: int):
        msg = (
            f"Chat with Telegram ID '{chat_id}' already exists."
            if chat_id is not None else None
        )
        super().__init__(msg, chat_id=chat_id)


class DuplicateSlugError(AppError):
    """
    Raised when the chat slug already exists.

    :param slug: Conflicting chat slug.
    """
    code = "duplicate_slug"

    def __init__(self, slug: str):
        msg = (
            f"Chat with slug '{slug}' already exists."
            if slug is not None else None
        )
        super().__init__(msg, slug=slug)


class ChatNotFoundError(AppError):
    """
    Raised when a chat cannot be found by ID or slug.

    :param chat_id: The chat ID used for lookup.
    :param slug: The chat slug used for lookup.
    """
    code = "chat_not_found"

    def __init__(
            self,
            chat_id: int | None = None,
            slug: str | None = None):
        if chat_id is not None:
            msg = f"Chat with ID={chat_id} not found."
        elif slug is not None:
            msg = f"Chat with slug '{slug}' not found."
        else:
            msg = "Chat not found."
        super().__init__(msg, chat_id=chat_id, slug=slug)


class DuplicateMessageError(Exception):
    """Raised when msg_id already exists within the same chat."""


class MessageNotFoundError(Exception):
    """Raised when a message cannot be found for update or view."""
