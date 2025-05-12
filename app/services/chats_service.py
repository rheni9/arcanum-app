"""
Service module for managing chat data in the database.

Provides functions to:
- fetch chats with sorting,
- retrieve a chat by slug,
- insert and update chats,
- delete chats and their messages,
- check for existing slugs.

Built on SQLite with structured logging and context-managed DB access.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError
from typing import List, Dict, Optional

from app.models.models import Chat
from app.utils.db_utils import get_connection
from app.utils.sql_utils import build_order_clause, OrderConfig

logger = logging.getLogger(__name__)


def get_chats(sort_by: str = "name", order: str = "asc") -> List[Dict]:
    """
    Retrieve all chats from the database, sorted by the selected field.

    Supports sorting by name, number of messages, or time of last message.

    :param sort_by: Field to sort by (e.g., 'name', 'last_message_at').
    :type sort_by: str
    :param order: Sorting direction ('asc' or 'desc').
    :type order: str
    :return: List of chat records as dictionaries.
    :rtype: List[dict]
    :raises DatabaseError: If retrieval fails due to a database error.
    """
    config = OrderConfig(
        allowed_fields={"name", "message_count", "last_message_at"},
        default_field="last_message_at",
        default_order="desc"
    )

    order_clause = build_order_clause(sort_by, order, config)
    logger.debug("[DB] Chats have been fetched sorted by %s %s",
                 sort_by, order)

    query = f'''
        SELECT c.slug, c.name,
               COUNT(m.chat_slug) AS message_count,
               MAX(m.timestamp) AS last_message_at
        FROM chats c
        LEFT JOIN messages m ON m.chat_slug = c.slug
        GROUP BY c.slug, c.name
        {order_clause}
    '''

    with get_connection() as conn:
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_chat_by_slug(slug: str) -> Optional[Chat]:
    """
    Retrieve a single chat record from the database using its slug.

    If no matching chat is found, returns None. Ensures safe access
    with structured logging and graceful handling of missing records.

    :param slug: Unique identifier of the chat.
    :type slug: str
    :return: Chat instance or None if not found.
    :rtype: Optional[Chat]
    :raises DatabaseError: If the database query fails.
    """
    sql = "SELECT * FROM chats WHERE slug = ?"

    try:
        with get_connection() as conn:
            row = conn.execute(sql, (slug,)).fetchone()
    except DatabaseError as e:
        logger.error("[DB] Failed to retrieve chat '%s': %s", slug, e)
        raise

    if not row:
        logger.warning("[DB] Chat with slug '%s' was not found.", slug)
        return None

    joined = row["joined"]
    joined_str = (
        joined if isinstance(joined, str) and joined.count("-") == 2 else None
    )

    return Chat(
        slug=row["slug"],
        name=row["name"],
        chat_id=row["chat_id"],
        link=row["link"],
        type=row["type"],
        joined=joined_str,
        is_active=bool(row["is_active"]),
        is_member=bool(row["is_member"]),
        notes=row["notes"]
    )


def insert_chat(chat: Chat) -> None:
    """
    Insert a new chat record into the database.

    Validates and stores all provided chat metadata. If a chat with the same
    slug already exists, raises a ValueError with a descriptive message.

    :param chat: Chat object to insert.
    :type chat: Chat
    :raises ValueError: If the chat slug already exists or insertion fails.
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
        with get_connection() as conn:
            conn.execute(sql, values)
            conn.commit()
            logger.info("[INSERT] New chat '%s' has been inserted.", chat.slug)
    except IntegrityError as e:
        logger.error(
            "[INSERT] Chat insert failed due to integrity error: %s", e
        )
        raise ValueError(
            f"Chat with slug '{chat.slug}' already exists."
        ) from e
    except DatabaseError as e:
        logger.error("[INSERT] Database error during chat insert: %s", e)
        raise


def update_chat(chat: Chat) -> None:
    """
    Update an existing chat record with new data.

    All editable fields are updated in the database. The chat is identified
    by its slug. Changes are committed transactionally.

    :param chat: Chat object containing updated fields.
    :type chat: Chat
    :raises DatabaseError: If the update operation fails.
    """
    sql = '''
        UPDATE chats SET
            chat_id = ?, type = ?, name = ?, link = ?, joined = ?,
            is_active = ?, is_member = ?, notes = ?
        WHERE slug = ?
    '''
    values = (
        chat.chat_id, chat.type, chat.name, chat.link, chat.joined,
        int(chat.is_active), int(chat.is_member), chat.notes, chat.slug
    )
    try:
        with get_connection() as conn:
            conn.execute(sql, values)
            conn.commit()
            logger.info("[UPDATE] Chat '%s' has been updated.", chat.slug)
    except DatabaseError as e:
        logger.error("[UPDATE] Database error during chat update: %s", e)
        raise


def delete_chat_and_messages(slug: str) -> None:
    """
    Delete a chat and all associated messages from the database.

    The operation is irreversible. The chat is identified by its slug
    and removed along with its related messages using ON DELETE CASCADE.

    :param slug: Slug of the chat to delete.
    :type slug: str
    :raises DatabaseError: If the deletion fails.
    """
    sql = "DELETE FROM chats WHERE slug = ?"
    try:
        with get_connection() as conn:
            conn.execute(sql, (slug,))
            conn.commit()
            logger.info("[DELETE] Chat '%s' has been deleted.", slug)
    except DatabaseError as e:
        logger.error("[DELETE] Database error during chat deletion: %s", e)
        raise


def slug_exists(slug: str) -> bool:
    """
    Check whether a chat slug already exists in the database.

    Used to prevent duplicate chat creation or identify existing records
    for update operations.

    :param slug: Slug to check for existence.
    :type slug: str
    :return: True if the slug exists, False otherwise.
    :rtype: bool
    """
    sql = "SELECT 1 FROM chats WHERE slug = ?"

    with get_connection() as conn:
        cur = conn.execute(sql, (slug,))
        exists = cur.fetchone() is not None

    logger.debug("[CHECK] Slug '%s' exists: %s", slug, exists)
    return exists
