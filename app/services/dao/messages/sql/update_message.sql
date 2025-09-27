-- update_message.sql
-- Update an existing message record.
--
-- Parameters:
--   :id – primary key of the message to update
--   :msg_id, :timestamp, :link, :text, :media,
--   :screenshot, :tags, :notes – updated values
--
-- Returns:
--   Number of rows affected (should be 1 on success).

UPDATE messages
SET msg_id = :msg_id,
    timestamp = :timestamp,
    link = :link,
    text = :text,
    media = :media,
    screenshot = :screenshot,
    tags = :tags,
    notes = :notes
WHERE id = :id;
