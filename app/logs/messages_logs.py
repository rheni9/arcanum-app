"""
Centralized logging for message-related events in the Arcanum application.

Handles logging of message viewing and actions such as creation, updating,
and deletion. Ensures consistent log formatting across routes.
"""

import logging

from app.utils.time_utils import datetimeformat

logger = logging.getLogger(__name__)


def log_message_view(
    pk: int,
    chat_slug: str,
    timestamp: str | None = None,
    short_text: str | None = None
) -> None:
    """
    Log the display of a single message.

    :param pk: Message database ID.
    :param chat_slug: Parent chat slug.
    :param timestamp: Optional ISO string or datetime.
    :param short_text: Optional preview of message text.
    """
    local_time = datetimeformat(timestamp, "datetime")
    logger.info(
        "[MESSAGES|VIEW] Message id=%s in chat='%s' | time=%s | text='%s'",
        pk, chat_slug, local_time, short_text or "-"
    )


def log_message_action(
    action: str,
    msg_id: int | None,
    chat_slug: str
) -> None:
    """
    Log a message-level action.

    :param action: Action type ('create', 'update', 'delete').
    :param msg_id: Message database ID or None.
    :param chat_slug: Related chat slug.
    """
    logger.info(
        "[MESSAGES|%s] Message id=%s in chat='%s'.",
        action.upper(), msg_id, chat_slug
    )
