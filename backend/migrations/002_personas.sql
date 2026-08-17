-- Personas: first-class representation of the user inside conversations.

CREATE TABLE IF NOT EXISTS personas (
    id TEXT PRIMARY KEY,
    -- Identity
    profile_name TEXT NOT NULL,
    chat_name TEXT NOT NULL,
    age INTEGER,
    pronouns TEXT,

    -- Physical appearance
    height TEXT,
    build TEXT,
    hair TEXT,
    eyes TEXT,
    skin TEXT,
    clothing TEXT,
    appearance_description TEXT,

    -- Personality
    traits TEXT,                    -- JSON array of strings
    personality_description TEXT,
    likes TEXT,                     -- JSON array
    dislikes TEXT,                  -- JSON array
    habits TEXT,                    -- JSON array
    speaking_style TEXT,

    -- Background
    biography TEXT,
    occupation TEXT,
    location TEXT,
    additional_facts TEXT,          -- JSON array

    -- Behaviour
    how_they_act TEXT,
    how_they_respond TEXT,
    custom_instructions TEXT,

    -- Examples (few-shot)
    example_dialogues TEXT,         -- JSON array of {user, persona} pairs

    -- Metadata
    avatar_path TEXT,
    tags TEXT,                      -- JSON array
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_personas_profile_name ON personas(profile_name);
CREATE INDEX IF NOT EXISTS idx_personas_archived ON personas(is_archived);
