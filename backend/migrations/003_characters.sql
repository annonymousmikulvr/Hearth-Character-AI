-- Characters: first-class AI profiles.

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    avatar_path TEXT,

    -- Core prompt material
    system_prompt TEXT,
    baseline_personality TEXT,
    scenario TEXT,
    greeting TEXT,
    example_dialogues TEXT,         -- JSON array of dialogue turns

    -- Generation defaults (can be overridden per message / conversation)
    temperature REAL,
    top_p REAL,
    repetition_penalty REAL,
    context_window INTEGER,
    max_tokens INTEGER,

    -- Model binding (null = use application default)
    model_profile_id TEXT REFERENCES model_profiles(id) ON DELETE SET NULL,
    model_name TEXT,                -- convenience override when no profile

    -- Side-character settings
    side_character_enabled INTEGER NOT NULL DEFAULT 1,
    side_character_instructions TEXT,

    -- Metadata
    tags TEXT,                      -- JSON array
    version INTEGER NOT NULL DEFAULT 1,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
CREATE INDEX IF NOT EXISTS idx_characters_archived ON characters(is_archived);
