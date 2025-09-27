-- fetch_chats.sql
-- Retrieve all chats with message count and last message timestamp.
--
-- Placeholders for formatting:
--   {order_clause} – ORDER BY clause injected from Python.
--
-- Returns:
--   One row per chat with the following extra fields:
--     - message_count: number of messages in the chat
--     - last_message: timestamp of the most recent message

SELECT
    c.id, c.chat_id, c.slug, c.name, c.link, c.type, c.image,
    c.joined, c.is_active, c.is_member, c.is_public, c.notes,
    (SELECT COUNT(*) FROM messages m
        WHERE m.chat_ref_id = c.id) AS message_count,
    (SELECT MAX(m.timestamp) FROM messages m
        WHERE m.chat_ref_id = c.id) AS last_message
FROM chats c
ORDER BY {order_clause};
