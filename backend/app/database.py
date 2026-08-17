"""
SQLite database management with simple migration runner.
The database is the single source of truth for all application data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import AsyncIterator, Optional

import aiosqlite

logger = logging.getLogger(__name__)

# Module-level connection; opened after setup chooses a data root
_db: Optional[aiosqlite.Connection] = None
_db_path: Optional[Path] = None


async def open_database(db_path: Path) -> aiosqlite.Connection:
    global _db, _db_path
    if _db is not None and _db_path == db_path:
        return _db

    if _db is not None:
        await _db.close()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(str(db_path))
    _db.row_factory = aiosqlite.Row
    await _db.execute("PRAGMA foreign_keys = ON")
    await _db.execute("PRAGMA journal_mode = WAL")
    await _db.execute("PRAGMA synchronous = NORMAL")
    _db_path = db_path
    logger.info("Opened database at %s", db_path)
    return _db


async def close_database() -> None:
    global _db, _db_path
    if _db is not None:
        await _db.close()
        _db = None
        _db_path = None


def get_db() -> aiosqlite.Connection:
    if _db is None:
        raise RuntimeError("Database not opened. Complete setup first.")
    return _db


async def get_db_dependency() -> AsyncIterator[aiosqlite.Connection]:
    """FastAPI dependency."""
    yield get_db()


async def run_migrations(db: aiosqlite.Connection, migrations_dir: Path) -> None:
    """
    Apply any pending migrations in lexical order.
    Migrations are plain .sql files named 001_*.sql, 002_*.sql, ...
    """
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    await db.commit()

    cursor = await db.execute("SELECT version FROM schema_migrations")
    applied = {row[0] for row in await cursor.fetchall()}

    if not migrations_dir.exists():
        logger.warning("Migrations directory %s does not exist", migrations_dir)
        return

    files = sorted(migrations_dir.glob("*.sql"))
    for file in files:
        version = file.stem  # e.g. 001_initial
        if version in applied:
            continue
        sql = file.read_text(encoding="utf-8")
        logger.info("Applying migration %s", version)
        await db.executescript(sql)
        await db.execute(
            "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
        )
        await db.commit()
        logger.info("Migration %s applied", version)


async def ensure_data_directories(data_root: Path) -> None:
    """Create the standard data-root layout."""
    for sub in ("avatars", "character_packages", "backups", "models", "cache"):
        (data_root / sub).mkdir(parents=True, exist_ok=True)
