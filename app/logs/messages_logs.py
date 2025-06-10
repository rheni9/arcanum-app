"""
Provides centralized logging functions for message-related events.

Handles logging for viewing, creating, updating, and deleting messages.
Ensures unified log formatting across message routes and services.
"""

import logging

from app.utils.time_utils import datetimeformat

logger = logging.getLogger("app.messages")


def log_message_view(
    pk: int,
    chat_slug: str,
    timestamp: str | None = None,
    short_text: str | None = None
) -> None:
    """
    Log the display of a single message.

    :param pk: Internal message database id.
    :type pk: int
    :param chat_slug: Parent chat slug.
    :type chat_slug: str
    :param timestamp: (Optional) Message timestamp (ISO string or datetime).
    :type timestamp: str | None
    :param short_text: (Optional) Shortened message text.
    :type short_text: str | None
    """
    local_time = datetimeformat(timestamp, "datetime")
    logger.info(
        "[MESSAGES|VIEW] Message id=%s in chat='%s' | time=%s | text='%s'",
        pk,
        chat_slug,
        local_time,
        short_text or "-"
    )


def log_message_action(
    action: str, msg_id: int | None, chat_slug: str
) -> None:
    """
    Log a message action in a unified style.

    :param action: Action string (CREATE, UPDATE, DELETE).
    :param msg_id: Message database id or None.
    :param chat_slug: Chat slug.
    """
    logger.info(
        "[MESSAGES|%s] Message id=%s in chat='%s'.",
        action.upper(), msg_id, chat_slug
    )
