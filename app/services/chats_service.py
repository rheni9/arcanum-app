"""
Chat service module for the Arcanum application.

Provides database-level operations for chats:
retrieval, insertion, updating, deletion.
Relies on chat.id as primary key for relationships.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError
from typing import List, Dict, Optional

from app.models.models import Chat
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import build_order_clause, OrderConfig

logger = logging.getLogger(__name__)


def get_chats(sort_by: str = "name", order: str = "asc") -> List[Dict]:
    """
    Retrieve all chats with sorting options.

    :param sort_by: Sort field ('name', 'message_count', 'last_message_at').
    :type sort_by: str
    :param order: Sort direction ('asc' or 'desc').
    :type order: str
    :return: List of chat records.
    :rtype: List[dict]
    :raises DatabaseError: On retrieval failure.
    """
    config = OrderConfig(
        allowed_fields={"name", "message_count", "last_message_at"},
        default_field="last_message_at",
        default_order="desc"
    )

    sql = f'''
        SELECT c.id, c.slug, c.name,
               COUNT(m.id) AS message_count,
               MAX(m.timestamp) AS last_message_at
        FROM chats c
        LEFT JOIN messages m ON m.chat_ref_id = c.id
        GROUP BY c.id, c.slug, c.name
        {build_order_clause(sort_by, order, config)}
    '''

    try:
        conn = get_connection_lazy()
        cursor = conn.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
    except DatabaseError as e:
        logger.error("[DB|CHATS] Failed to list chats: %s", e)
        raise

    logger.debug("[CHATS|SERVICE] Retrieved %d chat record(s).", len(results))
    return results


def get_chat_by_slug(slug: str) -> Optional[Chat]:
    """
    Retrieve a chat by its slug.

    Used for URL-based identification.

    :param slug: Chat slug identifier.
    :type slug: str
    :return: Chat instance or None.
    :rtype: Optional[Chat]
    :raises DatabaseError: On query failure.
    """
    sql = "SELECT * FROM chats WHERE slug = ?"

    try:
        conn = get_connection_lazy()
        row = conn.execute(sql, (slug,)).fetchone()
    except DatabaseError as e:
        logger.error("[DB|CHATS] Failed to fetch slug '%s': %s", slug, e)
        raise

    if not row:
        logger.warning("[CHATS|SERVICE] No chat found with slug '%s'.", slug)
        return None

    return Chat(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        chat_id=row["chat_id"],
        type=row["type"],
        link=row["link"],
        joined=row["joined"],
        is_active=bool(row["is_active"]),
        is_member=bool(row["is_member"]),
        notes=row["notes"]
    )


def get_chats_by_ids(ids: set[int]) -> List[dict]:
    """
    Retrieve chats by a set of IDs.

    Optimized for message grouping.

    :param ids: Set of chat IDs.
    :type ids: set[int]
    :return: List of chat records (id, slug, name).
    :rtype: List[dict]
    :raises DatabaseError: On retrieval failure.
    """
    if not ids:
        return []

    placeholders = ", ".join("?" for _ in ids)
    sql = f"SELECT id, slug, name FROM chats WHERE id IN ({placeholders})"

    try:
        conn = get_connection_lazy()
        cursor = conn.execute(sql, tuple(ids))
        results = [dict(row) for row in cursor.fetchall()]
    except DatabaseError as e:
        logger.error("[DB|CHATS] Failed to fetch chats by IDs: %s", e)
        raise

    logger.debug(
        "[CHATS|SERVICE] Retrieved %d chat(s) by ID filter.", len(results)
    )
    return results


def insert_chat(chat: Chat) -> None:
    """
    Insert a new chat record into the database.

    :param chat: Chat instance to insert.
    :type chat: Chat
    :raises ValueError: If slug is not unique.
    :raises DatabaseError: On insertion failure.
    """
    sql = '''
        INSERT INTO chats (
            slug, chat_id, type, name, link, joined,
            is_active, is_member, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    values = (
        chat.slug, chat.chat_id, chat.type, chat.name,
        chat.link, chat.joined,
        int(chat.is_active), int(chat.is_member), chat.notes
    )

    try:
        conn = get_connection_lazy()
        conn.execute(sql, values)
        conn.commit()
    except IntegrityError as e:
        logger.error("[DB|CHATS] Insert failed: %s", e)
        raise ValueError(f"Slug '{chat.slug}' already exists.") from e
    except DatabaseError as e:
        logger.error("[DB|CHATS] Insert failed: %s", e)
        raise

    logger.info("[CHATS|SERVICE] New chat inserted: '%s'.", chat.slug)


def update_chat(chat: Chat) -> None:
    """
    Update an existing chat by its ID.

    :param chat: Chat instance with updated fields.
    :type chat: Chat
    :raises DatabaseError: On update failure.
    """
    sql = '''
        UPDATE chats SET
            slug = ?, chat_id = ?, type = ?, name = ?, link = ?, joined = ?,
            is_active = ?, is_member = ?, notes = ?
        WHERE id = ?
    '''
    values = (
        chat.slug, chat.chat_id, chat.type, chat.name,
        chat.link, chat.joined,
        int(chat.is_active), int(chat.is_member), chat.notes, chat.id
    )

    try:
        conn = get_connection_lazy()
        conn.execute(sql, values)
        conn.commit()
    except DatabaseError as e:
        logger.error("[DB|CHATS] Update failed for chat '%s': %s",
                     chat.slug, e)
        raise

    logger.info(
        "[CHATS|SERVICE] Chat updated (id=%d, slug='%s').", chat.id, chat.slug
    )


def delete_chat_and_messages(slug: str) -> None:
    """
    Delete a chat and its messages.

    :param slug: Chat slug identifier.
    :type slug: str
    :raises DatabaseError: On deletion failure.
    """
    chat_ref_id = get_chat_id_by_slug(slug)

    try:
        conn = get_connection_lazy()
        conn.execute(
            "DELETE FROM messages WHERE chat_ref_id = ?", (chat_ref_id,)
        )
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_ref_id,))
        conn.commit()
    except DatabaseError as e:
        logger.error(
            "[DB|CHATS] Deletion failed for id=%d: %s", chat_ref_id, e
        )
        raise

    logger.info(
        "[CHATS|SERVICE] Chat removed from database (id=%d, slug='%s').",
        chat_ref_id, slug
    )


def slug_exists(slug: str) -> bool:
    """
    Check if a chat slug exists.

    :param slug: Slug to check.
    :type slug: str
    :returns: True if slug exists, False otherwise.
    :rtype: bool
    """
    sql = "SELECT 1 FROM chats WHERE slug = ?"

    conn = get_connection_lazy()
    cur = conn.execute(sql, (slug,))
    exists = cur.fetchone() is not None

    logger.debug("[CHATS|SERVICE] Slug '%s' existence check: %s", slug, exists)
    return exists


def get_chat_id_by_slug(slug: str) -> int:
    """
    Retrieve a chat's ID by its slug.

    :param slug: Unique chat slug.
    :type slug: str
    :returns: Chat primary key.
    :rtype: int
    :raises ValueError: If chat with given slug not found.
    :raises DatabaseError: On query failure.
    """
    sql = "SELECT id FROM chats WHERE slug = ?"

    try:
        conn = get_connection_lazy()
        row = conn.execute(sql, (slug,)).fetchone()
    except DatabaseError as e:
        logger.error("[DB|CHATS] Failed to get ID for slug '%s': %s", slug, e)
        raise

    if not row:
        logger.warning("[CHATS|SERVICE] No chat found with slug '%s'.", slug)
        raise ValueError(f"Chat slug '{slug}' not found.")

    logger.debug("[CHATS|SERVICE] Found id=%d for slug='%s'.", row["id"], slug)
    return row["id"]
