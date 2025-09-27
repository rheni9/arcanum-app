-- fetch_global_chat_stats.postgres.sql
-- Aggregate global statistics about chats and messages (PostgreSQL version).
--
-- Includes:
--   - total number of chats
--   - total number of messages
--   - total number of media messages (non-empty JSONB array in "media")
--   - most active chat (name, slug, message count)
--   - most recent message (id, timestamp, chat slug)

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
