"""
Idempotent schema ensure — runs after migrations on every startup.
Safe if migrations were skipped or partially applied.
"""

from __future__ import annotations

import logging

import aiosqlite

logger = logging.getLogger(__name__)

ENSURE: dict[str, list[tuple[str, str]]] = {
    "personas": [
        ("family_tree", "TEXT"),
        ("relationships", "TEXT"),
        ("modes", "TEXT"),
        ("active_mode", "TEXT"),
    ],
    "characters": [
        ("avatar_path", "TEXT"),
        ("filter_level", "TEXT DEFAULT 'mature'"),
        ("age", "TEXT"),
        ("pronouns", "TEXT"),
        ("height", "TEXT"),
        ("build", "TEXT"),
        ("hair", "TEXT"),
        ("eyes", "TEXT"),
        ("skin", "TEXT"),
        ("clothing", "TEXT"),
        ("appearance_description", "TEXT"),
        ("traits", "TEXT"),
        ("likes", "TEXT"),
        ("dislikes", "TEXT"),
        ("habits", "TEXT"),
        ("speaking_style", "TEXT"),
        ("occupation", "TEXT"),
        ("location", "TEXT"),
        ("biography", "TEXT"),
        ("additional_facts", "TEXT"),
        ("how_they_act", "TEXT"),
        ("how_they_respond", "TEXT"),
        ("custom_instructions", "TEXT"),
        ("family_tree", "TEXT"),
        ("relationships", "TEXT"),
        ("goals", "TEXT"),
        ("fears", "TEXT"),
        ("secrets", "TEXT"),
        ("image_gen_enabled", "INTEGER DEFAULT 0"),
        ("image_gen_style", "TEXT"),
        ("side_roster", "TEXT"),
        ("mood_board", "TEXT"),
        ("trigger_phrases", "TEXT"),
    ],
    "conversations": [
        ("seed_notes", "TEXT"),
        ("is_custom", "INTEGER DEFAULT 0"),
        ("filter_level", "TEXT"),
        ("emotion_intensity", "REAL DEFAULT 0.5"),
        ("topic_mutes", "TEXT"),
        ("active_branch_id", "TEXT"),
        ("persona_mode", "TEXT"),
        ("pinned_lines", "TEXT"),
        ("live_overrides", "TEXT"),
        ("world_id", "TEXT"),
        ("model_name", "TEXT"),
        ("temperature", "REAL"),
        ("top_p", "REAL"),
        ("max_tokens", "INTEGER"),
        ("last_message_at", "TEXT"),
        ("is_archived", "INTEGER DEFAULT 0"),
    ],
    "messages": [
        ("branch_id", "TEXT"),
        ("rating", "INTEGER"),
        ("is_scene_header", "INTEGER DEFAULT 0"),
        ("edited_at", "TEXT"),
        ("variant_index", "INTEGER DEFAULT 0"),
        ("parent_message_id", "TEXT"),
        ("is_selected_variant", "INTEGER DEFAULT 1"),
        ("temperature", "REAL"),
        ("max_tokens", "INTEGER"),
        ("model_name", "TEXT"),
    ],
    "memories": [
        ("is_pinned", "INTEGER DEFAULT 0"),
    ],
}

BRANCHES_DDL = """
CREATE TABLE IF NOT EXISTS conversation_branches (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    icon TEXT DEFAULT '',
    parent_branch_id TEXT,
    created_from_message_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


async def ensure_columns(db: aiosqlite.Connection) -> None:
    try:
        await db.execute(BRANCHES_DDL)
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_branches_conv ON conversation_branches(conversation_id)"
        )
        logger.info("Ensured conversation_branches table")
    except Exception as e:
        logger.warning("Could not ensure conversation_branches: %s", e)

    for table, cols in ENSURE.items():
        try:
            cursor = await db.execute(f"PRAGMA table_info({table})")
            rows = await cursor.fetchall()
            existing = {row[1] for row in rows}
            if not existing:
                logger.warning("Table %s missing or empty schema", table)
                continue
        except Exception as e:
            logger.warning("Could not inspect table %s: %s", table, e)
            continue
        for name, decl in cols:
            if name in existing:
                continue
            sql = f"ALTER TABLE {table} ADD COLUMN {name} {decl}"
            try:
                await db.execute(sql)
                logger.info("Added column %s.%s", table, name)
            except Exception as e:
                logger.warning("Could not add %s.%s: %s", table, name, e)

    await db.commit()
