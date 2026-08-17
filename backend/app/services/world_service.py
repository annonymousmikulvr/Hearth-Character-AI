"""Worlds: shared setting/lore for conversations."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Optional

import aiosqlite


@dataclass
class World:
    id: str
    name: str
    description: Optional[str] = None
    rules: Optional[str] = None
    lore: Optional[str] = None
    locations: list[dict] = field(default_factory=list)
    factions: list[dict] = field(default_factory=list)
    objects: list[dict] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_prompt_block(self) -> str:
        lines = [f"World: {self.name}"]
        if self.description:
            lines.append(self.description.strip())
        if self.rules:
            lines.append(f"Rules:\n{self.rules.strip()}")
        if self.lore:
            lines.append(f"Lore:\n{self.lore.strip()}")
        if self.locations:
            lines.append("Locations:")
            for loc in self.locations[:12]:
                if isinstance(loc, dict):
                    lines.append(f"- {loc.get('name', '?')}: {loc.get('description', '')}")
                else:
                    lines.append(f"- {loc}")
        if self.factions:
            lines.append("Factions:")
            for f in self.factions[:8]:
                if isinstance(f, dict):
                    lines.append(f"- {f.get('name', '?')}: {f.get('description', '')}")
                else:
                    lines.append(f"- {f}")
        lines.append("Stay consistent with this world. Do not invent contradictions.")
        return "\n".join(lines)


def _jlist(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _row(row: aiosqlite.Row) -> World:
    return World(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        rules=row["rules"],
        lore=row["lore"],
        locations=_jlist(row["locations"]),
        factions=_jlist(row["factions"]),
        objects=_jlist(row["objects"]),
        tags=_jlist(row["tags"]),
        is_archived=bool(row["is_archived"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class WorldService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, data: dict) -> World:
        wid = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO worlds (id, name, description, rules, lore, locations, factions, objects, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                wid,
                data["name"],
                data.get("description"),
                data.get("rules"),
                data.get("lore"),
                json.dumps(data.get("locations") or []),
                json.dumps(data.get("factions") or []),
                json.dumps(data.get("objects") or []),
                json.dumps(data.get("tags") or []),
            ),
        )
        await self.db.commit()
        return await self.get(wid)  # type: ignore

    async def get(self, world_id: str) -> Optional[World]:
        cursor = await self.db.execute("SELECT * FROM worlds WHERE id = ?", (world_id,))
        row = await cursor.fetchone()
        return _row(row) if row else None

    async def list(self, include_archived: bool = False, limit: int = 100) -> list[World]:
        if include_archived:
            cursor = await self.db.execute(
                "SELECT * FROM worlds ORDER BY updated_at DESC LIMIT ?", (limit,)
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM worlds WHERE is_archived = 0 ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
        return [_row(r) for r in await cursor.fetchall()]

    async def update(self, world_id: str, data: dict) -> Optional[World]:
        existing = await self.get(world_id)
        if not existing:
            return None
        fields = {k: v for k, v in data.items() if v is not None or k in data}
        if not fields:
            return existing
        for key in ("locations", "factions", "objects", "tags"):
            if key in fields and not isinstance(fields[key], str):
                fields[key] = json.dumps(fields[key])
        if "is_archived" in fields:
            fields["is_archived"] = 1 if fields["is_archived"] else 0
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        await self.db.execute(
            f"UPDATE worlds SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            list(fields.values()) + [world_id],
        )
        await self.db.commit()
        return await self.get(world_id)

    async def delete(self, world_id: str, hard: bool = False) -> bool:
        if hard:
            cur = await self.db.execute("DELETE FROM worlds WHERE id = ?", (world_id,))
        else:
            cur = await self.db.execute(
                "UPDATE worlds SET is_archived = 1 WHERE id = ?", (world_id,)
            )
        await self.db.commit()
        return cur.rowcount > 0
