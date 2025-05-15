"""
Chat utilities for the Arcanum application.

Provides:
- construction of Chat model instances from form data,
- centralized object building for insert/update operations.
"""

import logging

from app.models.models import Chat

logger = logging.getLogger(__name__)


def build_chat_object(
    data: dict,
    slug: str,
    chat_ref_id: int | None = None
) -> Chat:
    """
    Construct a Chat model instance from validated form data.

    :param data: Cleaned form data fields.
    :type data: dict
    :param slug: Unique slug identifier for the chat.
    :type slug: str
    :param chat_ref_id: Existing database ID for update (None for insert).
    :type chat_ref_id: int | None
    :return: Chat model instance ready for database operation.
    :rtype: Chat
    """
    chat = Chat(
        id=chat_ref_id,
        slug=slug,
        name=data.get("name"),
        chat_id=data.get("chat_id"),
        link=data.get("link"),
        type=data.get("type"),
        joined=data.get("joined"),
        is_active="is_active" in data,
        is_member="is_member" in data,
        notes=data.get("notes"),
    )

    logger.debug(
        "[CHATS|UTILS] Built Chat object: "
        "%s | slug='%s' | name='%s' | chat_id=%s",
        "new (id=None)" if chat.id is None else f"existing (id={chat.id})",
        chat.slug, chat.name, chat.chat_id
    )

    return chat
