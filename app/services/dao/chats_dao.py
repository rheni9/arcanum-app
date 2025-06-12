"""
Chat database access for the Arcanum application.

Handles low-level database operations for retrieving, inserting,
updating, and deleting chat records. Supports access by ID and slug,
and provides aggregate statistics for UI, sorting, and message summaries.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError

from app.models.chat import Chat
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import OrderConfig, build_order_clause

logger = logging.getLogger(__name__)


def fetch_chats(
    sort_by: str = "last_message",
    order: str = "desc"
) -> list[dict]:
    """
    Retrieve all chats with message count and last message timestamp.

    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of chat row dictionaries with aggregate statistics.
    :raises DatabaseError: If the query fails.
    """
    config = OrderConfig(
        allowed_fields={"name", "message_count", "last_message"},
        default_field="last_message",
        default_order="desc",
        prefix=""
    )
    order_clause = build_order_clause(sort_by, order, config)

    query = f"""
        SELECT
            c.id, c.chat_id, c.slug, c.name, c.link, c.type,
            c.joined, c.is_active, c.is_member, c.is_public, c.notes,
            (SELECT COUNT(*) FROM messages m
                WHERE m.chat_ref_id = c.id) AS message_count,
            (SELECT MAX(m.timestamp) FROM messages m
                WHERE m.chat_ref_id = c.id) AS last_message
        FROM chats c
        ORDER BY {order_clause};
    """
    try:
        conn = get_connection_lazy()
        rows = conn.execute(query).fetchall()
        logger.debug("[CHATS|DAO] Retrieved %d chat(s).", len(rows))
        return [dict(row) for row in rows]
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Failed to retrieve chats: %s", e)
        raise


def fetch_chat_by_slug(slug: str) -> Chat | None:
    """
    Retrieve a chat by its slug.

    :param slug: Unique chat slug.
    :return: Chat instance if found, otherwise None.
    :raises DatabaseError: If the query fails.
    """
    query = "SELECT * FROM chats WHERE slug = ?;"
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (slug,)).fetchone()
        if not row:
            logger.debug("[CHATS|DAO] No match for slug '%s'.", slug)
        return Chat.from_row(dict(row)) if row else None
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Failed to fetch chat by slug '%s': %s",
                     slug, e)
        raise


def fetch_chat_by_id(pk: int) -> Chat | None:
    """
    Retrieve a chat by its primary key ID.

    :param pk: Chat primary key.
    :return: Chat instance if found, otherwise None.
    :raises DatabaseError: If the query fails.
    """
    query = "SELECT * FROM chats WHERE id = ?;"
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (pk,)).fetchone()
        if not row:
            logger.debug("[CHATS|DAO] No match for ID=%d.", pk)
        return Chat.from_row(dict(row)) if row else None
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Failed to fetch chat by ID=%d: %s", pk, e)
        raise


def insert_chat_record(chat: Chat) -> int:
    """
    Insert a new chat record into the database.

    :param chat: Chat instance to insert.
    :return: Primary key of the inserted chat.
    :raises IntegrityError: If the slug is not unique.
    :raises DatabaseError: If the query fails.
    """
    query = """
        INSERT INTO chats
            (chat_id, slug, name, link, type, joined,
             is_active, is_member, is_public, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    try:
        conn = get_connection_lazy()
        cursor = conn.execute(query, chat.prepare_for_db())
        conn.commit()
        pk = cursor.lastrowid
        logger.debug("[CHATS|DAO] Inserted chat ID=%d (slug='%s').",
                     pk, chat.slug)
        return pk
    except IntegrityError as e:
        logger.error("[CHATS|DAO] Insert failed due to slug conflict: %s", e)
        raise
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Insert failed: %s", e)
        raise


def update_chat_record(chat: Chat) -> None:
    """
    Update an existing chat record in the database.

    :param chat: Chat instance with updated values.
    :raises IntegrityError: If the slug is not unique.
    :raises DatabaseError: If the query fails.
    """
    query = """
        UPDATE chats
        SET chat_id = ?, slug = ?, name = ?, link = ?, type = ?, joined = ?,
            is_active = ?, is_member = ?, is_public = ?, notes = ?
        WHERE id = ?;
    """
    try:
        conn = get_connection_lazy()
        params = chat.prepare_for_db() + (chat.id,)
        cursor = conn.execute(query, params)
        conn.commit()
        if cursor.rowcount == 0:
            logger.debug("[CHATS|DAO] No rows updated for ID=%d.", chat.id)
        else:
            logger.debug("[CHATS|DAO] Updated chat ID=%d (slug='%s').",
                         chat.id, chat.slug)
    except IntegrityError as e:
        logger.error("[CHATS|DAO] Update failed due to slug conflict: %s", e)
        raise
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Update failed: %s", e)
        raise


def delete_chat_record(pk: int) -> None:
    """
    Delete a chat record by its primary key.

    :param pk: Chat primary key.
    :raises DatabaseError: If the query fails.
    """
    query = "DELETE FROM chats WHERE id = ?;"
    try:
        conn = get_connection_lazy()
        conn.execute(query, (pk,))
        conn.commit()
        logger.debug("[CHATS|DAO] Deleted chat ID=%d.", pk)
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Delete failed: %s", e)
        raise


def check_slug_exists(slug: str) -> bool:
    """
    Check whether a chat slug already exists in the database.

    :param slug: Chat slug.
    :return: True if the slug exists, otherwise False.
    :raises DatabaseError: If the query fails.
    """
    query = "SELECT 1 FROM chats WHERE slug = ? LIMIT 1;"
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (slug,)).fetchone()
        return row is not None
    except DatabaseError as e:
        logger.error("[CHATS|DAO] Slug check failed: %s", e)
        raise


def fetch_global_chat_stats() -> dict:
    """
    Retrieve global aggregate statistics from the database.

    Includes total number of chats and messages, media message count,
    most active chat by message count, and metadata about the last message.

    :return: Dictionary with aggregated statistics for all chats.
    :raises DatabaseError: If the query fails.
    """
    query = """
        WITH most_active AS (
            SELECT chat_ref_id, COUNT(*) AS msg_count
            FROM messages
            GROUP BY chat_ref_id
            ORDER BY msg_count DESC
            LIMIT 1
        ),
        last_msg AS (
            SELECT id, timestamp, chat_ref_id
            FROM messages
            ORDER BY timestamp DESC
            LIMIT 1
        )
        SELECT
            (SELECT COUNT(*) FROM chats) AS total_chats,
            (SELECT COUNT(*) FROM messages) AS total_messages,
            (SELECT COUNT(*) FROM messages
            WHERE media IS NOT NULL AND LENGTH(TRIM(media)) > 0
            ) AS media_messages,
            (SELECT name FROM chats
            WHERE id = (SELECT chat_ref_id FROM most_active)
            ) AS most_active_chat_name,
            (SELECT slug FROM chats
            WHERE id = (SELECT chat_ref_id FROM most_active)
            ) AS most_active_chat_slug,
            (SELECT msg_count FROM most_active) AS most_active_chat_count,
            (SELECT timestamp FROM last_msg) AS last_message_timestamp,
            (SELECT id FROM last_msg) AS last_message_id,
            (SELECT slug FROM chats
            WHERE id = (SELECT chat_ref_id FROM last_msg)
            ) AS last_message_chat_slug;
    """
    try:
        conn = get_connection_lazy()
        row = conn.execute(query).fetchone()
        logger.debug("[CHATS|DAO] Retrieved global chat statistics.")
        return dict(row)
    except DatabaseError as e:
        logger.error(
            "[CHATS|DAO] Failed to fetch global chat statistics: %s", e
        )
        raise
