-- Track edits on messages (optional metadata; content is updated in place for user messages).
-- Variant regeneration already uses parent_message_id + variant_index.

ALTER TABLE messages ADD COLUMN edited_at TEXT;
ALTER TABLE messages ADD COLUMN edit_count INTEGER NOT NULL DEFAULT 0;
