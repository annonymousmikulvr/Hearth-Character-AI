from __future__ import annotations

import json
from typing import Any, Optional

import aiosqlite


class SettingsService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        cursor = await self.db.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        )
        row = await cursor.fetchone()
        if row is None:
            return default
        return row[0]

    async def set(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = datetime('now')
            """,
            (key, value),
        )
        await self.db.commit()

    async def get_bool(self, key: str, default: bool = False) -> bool:
        val = await self.get(key)
        if val is None:
            return default
        return val.lower() in ("1", "true", "yes", "on")

    async def set_bool(self, key: str, value: bool) -> None:
        await self.set(key, "true" if value else "false")

    async def get_json(self, key: str, default: Any = None) -> Any:
        val = await self.get(key)
        if val is None:
            return default
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return default

    async def set_json(self, key: str, value: Any) -> None:
        await self.set(key, json.dumps(value))

    async def get_all(self) -> dict[str, str]:
        cursor = await self.db.execute("SELECT key, value FROM settings")
        rows = await cursor.fetchall()
        return {r[0]: r[1] for r in rows}

    # Convenience helpers used by the persona/character layer
    async def get_default_persona_id(self) -> Optional[str]:
        val = await self.get("default_persona_id")
        return val if val else None

    async def set_default_persona_id(self, persona_id: Optional[str]) -> None:
        await self.set("default_persona_id", persona_id or "")
