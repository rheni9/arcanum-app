-- insert_message.sql
-- Insert a new message record into the database.
--
-- Parameters (all bound by Python):
--   chat_ref_id, msg_id, timestamp, link,
--   text, media, screenshot, tags, notes
--
-- Returns:
--   The primary key of the inserted row (handled in Python).

INSERT INTO messages (
    chat_ref_id, msg_id, timestamp, link,
    text, media, screenshot, tags, notes
) VALUES (
    :chat_ref_id, :msg_id, :timestamp, :link,
    :text, :media, :screenshot, :tags, :notes
);
