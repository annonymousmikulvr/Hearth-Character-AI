-- Per-conversation living character state (mood, relationship, notes that evolve).
-- Custom chat seed support via conversation.seed_notes.

CREATE TABLE IF NOT EXISTS conversation_character_state (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    mood TEXT,
    relationship_stage TEXT,
    emotional_notes TEXT,
    knowledge_notes TEXT,          -- JSON array of short facts learned in this chat
    behavior_shifts TEXT,          -- JSON array of subtle shifts
    last_updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(conversation_id, character_id)
);

CREATE INDEX IF NOT EXISTS idx_ccs_conversation ON conversation_character_state(conversation_id);

-- Allow conversations to carry optional seed / custom intro notes
ALTER TABLE conversations ADD COLUMN seed_notes TEXT;
ALTER TABLE conversations ADD COLUMN is_custom INTEGER NOT NULL DEFAULT 0;
