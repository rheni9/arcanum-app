"""
Log routing for the Arcanum application.

Centralized access point for logging utilities related to chats, messages,
and search/filtering. Facilitates unified import and consistent usage
throughout the application.
"""

# flake8: noqa

from .chats_logs import (
    log_chat_list,
    log_chat_view,
    log_chat_action,
)

from .messages_logs import (
    log_message_view,
    log_message_action,
)

from .search_logs import (
    log_search_outcome,
)
