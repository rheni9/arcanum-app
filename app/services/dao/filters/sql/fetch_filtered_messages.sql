-- fetch_filtered_messages.sql
-- Retrieve messages matching filters (search query, tag, or date range).
--
-- Parameters (bound in Python):
--   :query       – search text (optional, only if action=search)
--   :tag         – tag text (optional, only if action=tag)
--   :start_date  – start date (optional, if date filter used)
--   :end_date    – end date (optional, if date filter with "between" mode)
--   :chat_slug   – optional chat slug to scope the filter
--
-- Placeholders for formatting:
--   {where_clause} – dynamically generated WHERE conditions
--   {order_clause} – ORDER BY clause injected from Python
--
-- Returns:
--   One row per message including chat metadata (chat name and slug).

SELECT
    m.id, m.chat_ref_id, m.msg_id, m.timestamp,
    m.link, m.text, m.media, m.screenshot, m.tags, m.notes,
    c.name AS chat_name, c.slug AS chat_slug
FROM messages m
JOIN chats c ON m.chat_ref_id = c.id
{where_clause}
ORDER BY {order_clause};
