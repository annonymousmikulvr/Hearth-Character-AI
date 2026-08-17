-- Ratings, branches, pins, triggers, mutes, intensity, roster, mood board

ALTER TABLE conversations ADD COLUMN emotion_intensity REAL DEFAULT 0.5;
ALTER TABLE conversations ADD COLUMN topic_mutes TEXT;           -- JSON string array
ALTER TABLE conversations ADD COLUMN active_branch_id TEXT;
ALTER TABLE conversations ADD COLUMN persona_mode TEXT;          -- outfit/mode label
ALTER TABLE conversations ADD COLUMN pinned_lines TEXT;          -- JSON array of strings

ALTER TABLE messages ADD COLUMN branch_id TEXT;
ALTER TABLE messages ADD COLUMN rating INTEGER;                  -- -1 dislike, 1 like, null none
ALTER TABLE messages ADD COLUMN is_scene_header INTEGER NOT NULL DEFAULT 0;

ALTER TABLE memories ADD COLUMN is_pinned INTEGER NOT NULL DEFAULT 0;

ALTER TABLE characters ADD COLUMN side_roster TEXT;              -- JSON [{name, notes}]
ALTER TABLE characters ADD COLUMN mood_board TEXT;               -- JSON [paths]
ALTER TABLE characters ADD COLUMN trigger_phrases TEXT;          -- JSON [{phrase, reaction}]

ALTER TABLE personas ADD COLUMN modes TEXT;                      -- JSON [{name, description, age_override?}]
ALTER TABLE personas ADD COLUMN active_mode TEXT;

CREATE TABLE IF NOT EXISTS conversation_branches (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '🌿',
    parent_branch_id TEXT,
    created_from_message_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_branches_conv ON conversation_branches(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_branch ON messages(branch_id);
