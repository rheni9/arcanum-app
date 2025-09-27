-- fetch_adjacent_message.sql
-- Retrieve the adjacent message (previous or next) within a chat.
--
-- Parameters:
--   chat_ref_id - foreign key to chats.id
--   current_ts  - timestamp of the reference message (exclusive)
--
-- Placeholders for formatting:
--   {ts_expr}    - expression for timestamp field (backend-specific)
--   {ts_param}   - expression for parameter (backend-specific)
--   {comparator} - "<" or ">" depending on direction
--   {order}      - "ASC" or "DESC" depending on direction
--
-- Returns:
--   Single row (the previous or next message) or no rows.

SELECT *
FROM messages
WHERE chat_ref_id = :chat_ref_id
  AND {ts_expr} {comparator} {ts_param}
ORDER BY {ts_expr} {order}
LIMIT 1;
