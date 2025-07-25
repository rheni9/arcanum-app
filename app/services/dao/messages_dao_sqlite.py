"""
Message database access for the Arcanum application.

Handles low-level database operations for retrieving, inserting,
updating, and deleting message records. Supports access by ID and
chat association, sorting of results, and message counting per chat.
"""

import logging
from sqlite3 import DatabaseError, IntegrityError

from app.models.message import Message
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import OrderConfig, build_order_clause

logger = logging.getLogger(__name__)


def fetch_message_by_id(pk: int) -> Message | None:
    """
    Retrieve a message by its primary key ID.

    :param pk: Message primary key.
    :return: Message instance if found, otherwise None.
    :raises DatabaseError: If the query fails.
    """
    query = "SELECT * FROM messages WHERE id = ?;"
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (pk,)).fetchone()
        if not row:
            logger.debug("[MESSAGES|DAO] No message found with ID=%d.", pk)
        return Message.from_row(dict(row)) if row else None
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Failed to fetch message by ID=%d: %s",
                     pk, e)
        raise


def fetch_messages_by_chat(
    chat_slug: str,
    sort_by: str,
    order: str
) -> list[dict]:
    """
    Retrieve all messages for a specific chat with sorting.

    :param chat_slug: Slug of the target chat.
    :param sort_by: Field to sort by.
    :param order: Sort direction ('asc' or 'desc').
    :return: List of message row dictionaries.
    :raises DatabaseError: If the query fails.
    """
    config = OrderConfig(
        allowed_fields={"timestamp", "msg_id"},
        default_field="timestamp",
        default_order="desc",
        prefix="m."
    )
    order_clause = build_order_clause(sort_by, order, config)

    query = f"""
        SELECT m.*, c.name AS chat_name, c.slug AS chat_slug
        FROM messages m
        JOIN chats c ON m.chat_ref_id = c.id
        WHERE c.slug = ?
        ORDER BY {order_clause};
    """
    try:
        conn = get_connection_lazy()
        cursor = conn.execute(query, (chat_slug,))
        rows = cursor.fetchall()
        logger.debug("[MESSAGES|DAO] Retrieved %d message(s) for chat '%s'.",
                     len(rows), chat_slug)
        return [dict(row) for row in rows]
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Failed to retrieve messages for chat "
                     "'%s': %s", chat_slug, e)
        raise


def insert_message_record(message: Message) -> int:
    """
    Insert a new message record into the database.

    :param message: Message instance to insert.
    :return: Primary key of the inserted message.
    :raises IntegrityError: If msg_id is not unique within the chat.
    :raises DatabaseError: If the query fails.
    """
    query = '''
        INSERT INTO messages (
            chat_ref_id, msg_id, timestamp, link,
            text, media, screenshot, tags, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''
    try:
        conn = get_connection_lazy()
        cursor = conn.execute(query, message.prepare_for_db())
        conn.commit()
        pk = cursor.lastrowid
        logger.debug("[MESSAGES|DAO] Inserted message ID=%d for "
                     "(chat_ref_id=%d).",
                     pk, message.chat_ref_id)
        return pk
    except IntegrityError as e:
        logger.error(
            "[MESSAGES|DAO] Insert failed due to unique msg_id conflict "
            "(chat_ref_id=%d, msg_id=%s): %s",
            message.chat_ref_id, str(message.msg_id), e
        )
        raise
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Insert failed: %s", e)
        raise


def update_message_record(message: Message) -> None:
    """
    Update an existing message record in the database.

    :param message: Message instance with updated values.
    :raises IntegrityError: If msg_id is not unique within the chat.
    :raises DatabaseError: If the query fails.
    """
    query = '''
        UPDATE messages
        SET msg_id = ?, timestamp = ?, link = ?, text = ?,
            media = ?, screenshot = ?, tags = ?, notes = ?
        WHERE id = ?;
    '''
    try:
        conn = get_connection_lazy()
        params = message.prepare_for_db()[1:] + (message.id,)
        cursor = conn.execute(query, params)
        conn.commit()
        if cursor.rowcount == 0:
            logger.debug("[MESSAGES|DAO] No rows updated for ID=%d.",
                         message.id)
        else:
            logger.debug("[MESSAGES|DAO] Updated message ID=%d.", message.id)
    except IntegrityError as e:
        logger.error(
            "[MESSAGES|DAO] Update failed due to unique msg_id conflict "
            "(chat_ref_id=%d, msg_id=%s): %s",
            message.chat_ref_id, str(message.msg_id), e
        )
        raise
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Update failed: %s", e)
        raise


def delete_message_record(pk: int) -> None:
    """
    Delete a message record by its primary key.

    :param pk: Message primary key.
    :raises DatabaseError: If the query fails.
    """
    query = "DELETE FROM messages WHERE id = ?;"
    try:
        conn = get_connection_lazy()
        conn.execute(query, (pk,))
        conn.commit()
        logger.debug("[MESSAGES|DAO] Deleted message ID=%d.", pk)
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Delete failed: %s", e)
        raise


def check_message_exists(chat_ref_id: int, msg_id: int) -> bool:
    """
    Check whether a message with the given Telegram ID exists within the chat.

    :param chat_ref_id: ID of the chat (foreign key in messages table).
    :param msg_id: Telegram message ID (unique within the given chat).
    :return: True if such a message exists within the chat, otherwise False.
    :raises DatabaseError: If the query fails.
    """
    query = (
        "SELECT 1 FROM messages "
        "WHERE chat_ref_id = ? AND msg_id = ? "
        "LIMIT 1;"
    )
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (chat_ref_id, msg_id)).fetchone()
        return row is not None
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Existence check failed: %s", e)
        raise


def count_messages_for_chat(chat_ref_id: int) -> int:
    """
    Count the number of messages in a given chat.

    :param chat_ref_id: ID of the related chat (foreign key).
    :return: Total number of messages in the chat.
    :raises DatabaseError: If the query fails.
    """
    query = "SELECT COUNT(*) FROM messages WHERE chat_ref_id = ?;"
    try:
        conn = get_connection_lazy()
        row = conn.execute(query, (chat_ref_id,)).fetchone()
        return row[0] if row else 0
    except DatabaseError as e:
        logger.error("[MESSAGES|DAO] Count failed: %s", e)
        raise
