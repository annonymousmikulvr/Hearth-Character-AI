-- Initial schema for Local Character AI v0.2
-- Settings, AI configuration, playback, and core tables.

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed a few default keys so the application can read them without null checks.
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('setup_completed', 'false'),
    ('default_persona_id', ''),
    ('default_model', ''),
    ('default_temperature', '0.85'),
    ('default_max_tokens', '512'),
    ('default_top_p', '0.9'),
    ('default_repetition_penalty', '1.1'),
    ('playback_enabled', 'true'),
    ('playback_chars_per_second', '40'),
    ('playback_initial_delay_ms', '300'),
    ('playback_dialogue_pause_ms', '200'),
    ('playback_action_pause_ms', '400'),
    ('playback_speaker_pause_ms', '500'),
    ('playback_heading_pause_ms', '600'),
    ('ollama_base_url', 'http://127.0.0.1:11434'),
    ('ai_provider', 'ollama');

CREATE TABLE IF NOT EXISTS model_profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'ollama',
    model_name TEXT NOT NULL,
    temperature REAL NOT NULL DEFAULT 0.85,
    top_p REAL NOT NULL DEFAULT 0.9,
    repetition_penalty REAL NOT NULL DEFAULT 1.1,
    context_window INTEGER NOT NULL DEFAULT 4096,
    max_tokens INTEGER NOT NULL DEFAULT 512,
    extra_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS safety_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
