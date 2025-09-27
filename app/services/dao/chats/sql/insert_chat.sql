-- insert_chat.sql
-- Insert a new chat record into the database.
--
-- Parameters (all bound by Python):
--   chat_id, slug, name, link, type, image, joined,
--   is_active, is_member, is_public, notes
--
-- Returns:
--   The primary key of the inserted row (handled in Python).

INSERT INTO chats (
    chat_id, slug, name, link, type, image, joined,
    is_active, is_member, is_public, notes
) VALUES (
    :chat_id, :slug, :name, :link, :type, :image, :joined,
    :is_active, :is_member, :is_public, :notes
);
