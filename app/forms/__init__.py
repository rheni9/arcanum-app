"""
Form module exports for the Arcanum application.

Aggregates all WTForms-based classes for authentication, chat, and message
handling into a single importable module.
"""

from .auth_form import AuthForm
from .chat_form import ChatForm
from .message_form import MessageForm

__all__ = ["AuthForm", "ChatForm", "MessageForm"]
