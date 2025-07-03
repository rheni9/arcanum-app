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


def log_media_removal(
    msg_id: int,
    chat_slug: str,
    media_url: str
) -> None:
    """
    Log the removal of a media file from a message.

    :param msg_id: ID of the message.
    :param chat_slug: Related chat slug.
    :param media_url: URL of the removed media.
    """
    logger.info(
        "[MESSAGES|MEDIA|REMOVE] Removed media from message id=%s "
        "in chat='%s' | url='%s'",
        msg_id, chat_slug, media_url
    )


def log_screenshot_removal(
    msg_id: int,
    chat_slug: str
) -> None:
    """
    Log the removal of a screenshot from a message.

    :param msg_id: ID of the message.
    :param chat_slug: Related chat slug.
    """
    logger.info(
        "[MESSAGES|SCREENSHOT|REMOVE] Removed screenshot from message id=%s "
        "in chat='%s'.",
        msg_id, chat_slug
    )
