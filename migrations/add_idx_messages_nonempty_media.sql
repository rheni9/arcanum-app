-- Migration: add partial index for non-empty media messages
-- Optimizes queries that count messages with non-empty media arrays.

-- Up migration:
CREATE INDEX IF NOT EXISTS idx_messages_nonempty_media
ON messages (id)
WHERE jsonb_typeof(media) = 'array'
  AND jsonb_array_length(media) > 0;

-- Rollback (optional):
-- DROP INDEX IF EXISTS idx_messages_nonempty_media;
