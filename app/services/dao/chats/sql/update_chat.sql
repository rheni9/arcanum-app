-- update_chat.sql
-- Update an existing chat record.
--
-- Parameters:
--   id – primary key of the chat to update
--   chat_id, slug, name, link, type, image, joined,
--   is_active, is_member, is_public, notes – updated values
--
-- Returns:
--   Number of rows affected (should be 1 on success).

UPDATE chats
SET chat_id = :chat_id,
    slug = :slug,
    name = :name,
    link = :link,
    type = :type,
    image = :image,
    joined = :joined,
    is_active = :is_active,
    is_member = :is_member,
    is_public = :is_public,
    notes = :notes
WHERE id = :id;
