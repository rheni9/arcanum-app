"""
Messages service module for the Arcanum application.

Provides database-level operations for messages:
retrieval, search, filtering, creation, updating, deletion.
"""

import logging
import json
from typing import List, Tuple
from sqlite3 import DatabaseError, IntegrityError

from app.models.models import Message
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import build_order_clause, OrderConfig
from app.services.chats_service import get_chat_id_by_slug

logger = logging.getLogger(__name__)


def get_chat_data(
    slug: str, sort_by: str, order: str
) -> Tuple[int, List[Message]]:
    """
    Retrieve messages for a chat with total count.

    :param slug: Chat slug identifier.
    :type slug: str
    :param sort_by: Sort field ('timestamp', 'msg_id').
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :returns: Tuple of (message count, list of Message instances).
    :rtype: Tuple[int, List[Message]]
    :raises DatabaseError: On query failure.
    """
    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc"
    )

    chat_ref_id = get_chat_id_by_slug(slug)

    sql = f'''
        SELECT m.*, COUNT(*) OVER() as total_count
        FROM messages m
        WHERE m.chat_ref_id = ?
        {build_order_clause(sort_by, order, config)}
    '''

    try:
        conn = get_connection_lazy()
        rows = conn.execute(sql, (chat_ref_id,)).fetchall()
    except DatabaseError as e:
        logger.error("[DB|MESSAGES] Failed to retrieve chat '%s': %s",
                     slug, e)
        raise

    messages = [
        Message(
            id=row["id"],
            chat_ref_id=row["chat_ref_id"],
            msg_id=row["msg_id"],
            timestamp=row["timestamp"],
            link=row["link"],
            text=row["text"],
            media=row["media"],
            screenshot=row["screenshot"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            notes=row["notes"]
        )
        for row in rows
    ]

    count = rows[0]["total_count"] if rows else 0

    logger.debug(
        "[MESSAGES|SERVICE] Retrieved %d message(s) for chat '%s'.",
        count, slug
    )
    return count, messages


def get_message_by_id(db_id: int) -> Message:
    """
    Retrieve a single message by its ID.

    :param db_id: Message primary key.
    :type db_id: int
    :returns: Message instance.
    :rtype: Message
    :raises ValueError: If message not found.
    :raises DatabaseError: On retrieval failure.
    """
    sql = "SELECT * FROM messages WHERE id = ?"

    try:
        conn = get_connection_lazy()
        row = conn.execute(sql, (db_id,)).fetchone()
    except DatabaseError as e:
        logger.error(
            "[DB|MESSAGES] Failed to retrieve message with id=%d: %s",
            db_id, e
        )
        raise

    if not row:
        logger.warning(
            "[MESSAGES|SERVICE] No message found with id=%d.", db_id
        )
        raise ValueError(f"Message with id {db_id} not found.")

    logger.debug("[MESSAGES|SERVICE] Retrieved message id=%d.", db_id)

    return Message(
        id=row["id"],
        chat_ref_id=row["chat_ref_id"],
        msg_id=row["msg_id"],
        timestamp=row["timestamp"],
        link=row["link"],
        text=row["text"],
        media=row["media"],
        screenshot=row["screenshot"],
        tags=json.loads(row["tags"]) if row["tags"] else [],
        notes=row["notes"]
    )


def insert_message(chat_slug: str, data: dict) -> None:
    """
    Insert a new message linked to a chat.

    :param chat_slug: Chat slug for lookup.
    :type chat_slug: str
    :param data: Message fields.
    :type data: dict
    :raises DatabaseError: On insertion failure.
    """
    chat_ref_id = get_chat_id_by_slug(chat_slug)

    sql = '''
        INSERT INTO messages (
            msg_id, chat_ref_id, timestamp, link, text,
            media, screenshot, tags, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    values = (
        data.get("msg_id"),
        chat_ref_id,
        data.get("timestamp"),
        data.get("link"),
        data.get("text"),
        data.get("media"),
        data.get("screenshot"),
        data.get("tags"),
        data.get("notes")
    )

    try:
        conn = get_connection_lazy()
        conn.execute(sql, values)
        conn.commit()
    except IntegrityError as e:
        logger.error("[DB|MESSAGES] Integrity constraint failed: %s", e)
        raise
    except DatabaseError as e:
        logger.error("[DB|MESSAGES] Insert failed: %s", e)
        raise

    logger.info(
        "[MESSAGES|SERVICE] New message inserted into chat '%s'.", chat_slug
    )


def update_message(db_id: int, data: dict) -> None:
    """
    Update an existing message.

    :param db_id: Message primary key.
    :type db_id: int
    :param data: Updated fields.
    :type data: dict
    :raises DatabaseError: On update failure.
    """
    sql = '''
        UPDATE messages
        SET msg_id = ?, text = ?, timestamp = ?, link = ?,
            media = ?, screenshot = ?, tags = ?, notes = ?
        WHERE id = ?
    '''
    values = (
        data.get("msg_id"),
        data.get("text"),
        data.get("timestamp"),
        data.get("link"),
        data.get("media"),
        data.get("screenshot"),
        data.get("tags"),
        data.get("notes"),
        db_id
    )

    try:
        conn = get_connection_lazy()
        conn.execute(sql, values)
        conn.commit()
    except DatabaseError as e:
        logger.error(
            "[DB|MESSAGES] Update failed for message with id=%d: %s", db_id, e
        )
        raise

    logger.info("[MESSAGES|SERVICE] Message updated (id=%d).", db_id)


def delete_message_record(db_id: int) -> None:
    """
    Delete a message by its ID.

    :param db_id: Message primary key.
    :type db_id: int
    :raises DatabaseError: On deletion failure.
    """
    sql = "DELETE FROM messages WHERE id = ?"

    try:
        conn = get_connection_lazy()
        conn.execute(sql, (db_id,))
        conn.commit()
    except DatabaseError as e:
        logger.error(
            "[DB|MESSAGES] Deletion failed for message with id=%d: %s",
            db_id, e
        )
        raise

    logger.info(
        "[MESSAGES|SERVICE] Message removed from database (id=%d).", db_id
    )
