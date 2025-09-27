-- fetch_messages_by_chat.sql
-- Retrieve messages with chat join for a given chat slug and ordering.
--
-- Parameters:
--   :slug – chat slug to filter by
--   {order_clause} – ORDER BY clause injected from Python.
--
-- Returns:
--   One row per message including chat name and slug.

SELECT m.*, c.name AS chat_name, c.slug AS chat_slug
FROM messages m
JOIN chats c ON m.chat_ref_id = c.id
WHERE c.slug = :slug
ORDER BY {order_clause};
