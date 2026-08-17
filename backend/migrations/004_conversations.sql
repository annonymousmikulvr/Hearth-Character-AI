-- Conversations and messages.
-- A conversation binds Character + Persona (+ optional World later).
-- Messages store raw markup, never pre-rendered HTML.

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT,
    character_id TEXT NOT NULL REFERENCES characters(id) ON DELETE RESTRICT,
    persona_id TEXT NOT NULL REFERENCES personas(id) ON DELETE RESTRICT,
    -- Display name for the persona in *this* conversation (may differ from persona.chat_name)
    persona_display_name TEXT NOT NULL,
    world_id TEXT,                          -- reserved for future worlds
    -- Snapshot of generation defaults at creation (can be overridden per message later)
    temperature REAL,
    top_p REAL,
    repetition_penalty REAL,
    max_tokens INTEGER,
    model_name TEXT,
    -- State
    is_archived INTEGER NOT NULL DEFAULT 0,
    last_message_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_conversations_character ON conversations(character_id);
CREATE INDEX IF NOT EXISTS idx_conversations_persona ON conversations(persona_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(is_archived);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,                     -- 'user' | 'assistant' | 'system'
    speaker_type TEXT NOT NULL,              -- 'user' | 'primary' | 'side' | 'system'
    speaker_id TEXT,                        -- persona_id or character_id or side-character key
    speaker_name TEXT NOT NULL,             -- display name at time of message
    raw_content TEXT NOT NULL,              -- original markup, never HTML
    content_format TEXT NOT NULL DEFAULT 'markup',  -- 'markup' | 'plain'
    -- Variant support: messages can have multiple regenerated variants
    parent_message_id TEXT REFERENCES messages(id) ON DELETE CASCADE,
    variant_index INTEGER NOT NULL DEFAULT 0,
    is_selected_variant INTEGER NOT NULL DEFAULT 1,
    -- Generation metadata (assistant messages)
    temperature REAL,
    max_tokens INTEGER,
    model_name TEXT,
    token_count INTEGER,
    generation_ms INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_parent ON messages(parent_message_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
