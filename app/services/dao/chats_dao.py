"""
Chat database access for the Arcanum application.

Handles low-level database operations for retrieving, inserting,
updating, and deleting chat records in a PostgreSQL database.
Supports access by ID and slug, and provides aggregate statistics
for UI, sorting, and message summaries.
"""
# pylint: disable=no-member

import logging
from psycopg2 import errors
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.models.chat import Chat
from app.utils.db_utils import get_connection_lazy
from app.utils.sql_utils import OrderConfig, build_order_clause
from app.errors import (
    DuplicateSlugError, DuplicateChatIDError, ChatNotFoundError
)

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
    :raises SQLAlchemyError: If the query fails.
    """
    config = OrderConfig(
        allowed_fields={"name", "message_count", "last_message"},
        default_field="last_message",
        default_order="desc",
        prefix=""
    )
    order_clause = build_order_clause(sort_by, order, config)

    query = text(f"""
        SELECT
            c.id, c.chat_id, c.slug, c.name, c.link, c.type, c.image,
            c.joined, c.is_active, c.is_member, c.is_public, c.notes,
            (SELECT COUNT(*) FROM messages m
                WHERE m.chat_ref_id = c.id) AS message_count,
            (SELECT MAX(m.timestamp) FROM messages m
                WHERE m.chat_ref_id = c.id) AS last_message
        FROM chats c
        ORDER BY {order_clause};
    """)
    try:
        conn = get_connection_lazy()
        result = conn.execute(query)
        rows = result.mappings().all()
        logger.debug("[CHATS|DAO] Retrieved %d chat(s).", len(rows))
        return [dict(row) for row in rows]
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Failed to retrieve chats: %s", e)
        raise


def fetch_chat_by_slug(slug: str) -> Chat | None:
    """
    Retrieve a chat by its slug.

    :param slug: Unique chat slug.
    :return: Chat instance if found, otherwise None.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("SELECT * FROM chats WHERE slug = :slug;")
    try:
        conn = get_connection_lazy()
        result = conn.execute(query, {"slug": slug})
        row = result.mappings().fetchone()
        if not row:
            logger.debug("[CHATS|DAO] No match for slug '%s'.", slug)
        return Chat.from_row(dict(row)) if row else None
    except SQLAlchemyError as e:
        logger.error(
            "[CHATS|DAO] Failed to fetch chat by slug '%s': %s",
            slug, e
        )
        raise


def fetch_chat_by_id(pk: int) -> Chat | None:
    """
    Retrieve a chat by its primary key ID.

    :param pk: Chat primary key.
    :return: Chat instance if found, otherwise None.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("SELECT * FROM chats WHERE id = :id;")
    try:
        conn = get_connection_lazy()
        result = conn.execute(query, {"id": pk})
        row = result.mappings().fetchone()
        if not row:
            logger.debug("[CHATS|DAO] No match for ID=%d.", pk)
        return Chat.from_row(dict(row)) if row else None
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Failed to fetch chat by ID=%d: %s", pk, e)
        raise


def insert_chat_record(chat: Chat) -> int:
    """
    Insert a new chat record into the database.

    :param chat: Chat instance to insert.
    :return: Primary key of the inserted chat.
    :raises DuplicateSlugError: If the slug already exists.
    :raises DuplicateChatIDError: If the Telegram chat ID already exists.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("""
        INSERT INTO chats
            (chat_id, slug, name, link, type, image, joined,
             is_active, is_member, is_public, notes)
        VALUES (:chat_id, :slug, :name, :link, :type, :image, :joined,
                :is_active, :is_member, :is_public, :notes)
        RETURNING id;
    """)
    try:
        conn = get_connection_lazy()
        params = chat.prepare_for_db()
        cursor = conn.execute(query, params)
        conn.commit()
        pk = cursor.scalar_one()
        logger.debug(
            "[CHATS|DAO] Inserted chat ID=%d (slug='%s').",
            pk, chat.slug
        )
        return pk
    except IntegrityError as e:
        if isinstance(e.orig, errors.UniqueViolation):
            constraint = getattr(e.orig.diag, "constraint_name", "")
            if constraint == "chats_slug_key":
                logger.warning(
                    "[CHATS|DAO] Slug conflict during insert: '%s'",
                    chat.slug
                )
                raise DuplicateSlugError(slug=chat.slug) from e
            if constraint == "chats_chat_id_key":
                logger.warning(
                    "[CHATS|DAO] Chat ID conflict during insert: %s",
                    chat.chat_id
                )
                raise DuplicateChatIDError(chat_id=chat.chat_id) from e
        logger.error("[CHATS|DAO] Insert integrity error: %s", e)
        raise
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Insert failed: %s", e)
        raise


def update_chat_record(chat: Chat) -> None:
    """
    Update an existing chat record in the database.

    :param chat: Chat instance with updated values.
    :raises ChatNotFoundError: If the chat to update does not exist.
    :raises DuplicateSlugError: If the slug already exists.
    :raises DuplicateChatIDError: If the Telegram chat ID already exists.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("""
        UPDATE chats
        SET chat_id = :chat_id, slug = :slug, name = :name, link = :link,
            type = :type, image = :image, joined = :joined,
            is_active = :is_active, is_member = :is_member,
            is_public = :is_public, notes = :notes
        WHERE id = :id;
    """)
    try:
        conn = get_connection_lazy()
        params = chat.prepare_for_db()
        params["id"] = chat.id
        cursor = conn.execute(query, params)
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning("[CHATS|DAO] No rows updated for ID=%d.", chat.id)
            raise ChatNotFoundError(chat_id=chat.id)
        logger.debug(
            "[CHATS|DAO] Updated chat ID=%d (slug='%s').",
            chat.id, chat.slug
        )
    except IntegrityError as e:
        if isinstance(e.orig, errors.UniqueViolation):
            constraint = getattr(e.orig.diag, "constraint_name", "")
            if constraint == "chats_slug_key":
                logger.warning(
                    "[CHATS|DAO] Slug conflict during update: '%s'",
                    chat.slug
                )
                raise DuplicateSlugError(slug=chat.slug) from e
            if constraint == "chats_chat_id_key":
                logger.warning(
                    "[CHATS|DAO] Chat ID conflict during update: %s",
                    chat.chat_id
                )
                raise DuplicateChatIDError(chat_id=chat.chat_id) from e
        logger.error("[CHATS|DAO] Update integrity error: %s", e)
        raise
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Update failed: %s", e)
        raise


def delete_chat_record(pk: int) -> None:
    """
    Delete a chat record by its primary key.

    :param pk: Chat primary key.
    :raises ChatNotFoundError: If no chat exists with the given ID.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("DELETE FROM chats WHERE id = :id;")
    try:
        conn = get_connection_lazy()
        cursor = conn.execute(query, {"id": pk})
        conn.commit()
        if cursor.rowcount == 0:
            logger.warning(
                "[CHATS|DAO] No chat found to delete with ID=%d.", pk
            )
            raise ChatNotFoundError(chat_id=pk)
        logger.debug("[CHATS|DAO] Deleted chat ID=%d.", pk)
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Delete failed: %s", e)
        raise


def check_slug_exists(slug: str, exclude_id: int | None = None) -> bool:
    """
    Check whether a chat slug already exists in the database.

    :param slug: Chat slug.
    :param exclude_id: Chat ID to exclude from the check (useful for updates).
    :return: True if the slug exists, otherwise False.
    :raises SQLAlchemyError: If the query fails.
    """
    query = "SELECT 1 FROM chats WHERE slug = :slug"
    params = {"slug": slug}
    if exclude_id is not None:
        query += " AND id != :id"
        params["id"] = exclude_id
    query += " LIMIT 1;"

    try:
        conn = get_connection_lazy()
        row = conn.execute(text(query), params).fetchone()
        return row is not None
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Slug check failed: %s", e)
        raise


def check_chat_id_exists(chat_id: int, exclude_id: int | None = None) -> bool:
    """
    Check whether a chat ID already exists in the database.

    :param chat_id: Telegram chat ID.
    :param exclude_id: Chat ID to exclude from the check (useful for updates).
    :return: True if the chat ID exists, otherwise False.
    :raises SQLAlchemyError: If the query fails.
    """
    query = "SELECT 1 FROM chats WHERE chat_id = :chat_id"
    params = {"chat_id": chat_id}
    if exclude_id is not None:
        query += " AND id != :id"
        params["id"] = exclude_id
    query += " LIMIT 1;"

    try:
        conn = get_connection_lazy()
        row = conn.execute(text(query), params).fetchone()
        return row is not None
    except SQLAlchemyError as e:
        logger.error("[CHATS|DAO] Chat ID check failed: %s", e)
        raise


def fetch_global_chat_stats() -> dict:
    """
    Retrieve global aggregate statistics from the database.

    Includes total number of chats and messages, media message count,
    most active chat by message count, and metadata about the last message.

    :return: Dictionary with aggregated statistics for all chats.
    :raises SQLAlchemyError: If the query fails.
    """
    query = text("""
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
             WHERE jsonb_typeof(media) = 'array'
             AND jsonb_array_length(media) > 0
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
    """)
    try:
        conn = get_connection_lazy()
        result = conn.execute(query)
        row = result.mappings().fetchone()
        logger.debug("[CHATS|DAO] Retrieved global chat statistics.")
        return dict(row) if row else {}
    except SQLAlchemyError as e:
        logger.error(
            "[CHATS|DAO] Failed to fetch global chat statistics: %s", e
        )
        raise
