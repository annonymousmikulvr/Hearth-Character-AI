-- Memory graph + Worlds

CREATE TABLE IF NOT EXISTS worlds (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    rules TEXT,
    lore TEXT,
    locations TEXT,          -- JSON array of {name, description}
    factions TEXT,           -- JSON array
    objects TEXT,            -- JSON array
    tags TEXT,               -- JSON array
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_worlds_name ON worlds(name);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL,       -- global | character | conversation | world | persona
    owner_id TEXT NOT NULL,         -- id of owner, or 'global'
    content TEXT NOT NULL,
    category TEXT,                 -- fact | preference | event | relationship | location | other
    confidence REAL NOT NULL DEFAULT 0.7,
    importance REAL NOT NULL DEFAULT 0.5,
    source_conversation_id TEXT,
    source_message_id TEXT,
    tags TEXT,                     -- JSON array
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_memories_owner ON memories(owner_type, owner_id);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(is_archived);

-- Link conversations to worlds (column may already exist as nullable world_id)
-- Ensure index for world lookups on conversations
CREATE INDEX IF NOT EXISTS idx_conversations_world ON conversations(world_id);
