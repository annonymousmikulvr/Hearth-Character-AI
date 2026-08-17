from __future__ import annotations

import json
import uuid
from typing import Optional

import aiosqlite

from app.models.persona import Persona
from app.schemas.persona import PersonaCreate, PersonaUpdate


def _json_list(value: object) -> str:
    if value is None:
        return "[]"
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _parse_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _row_to_persona(row: aiosqlite.Row) -> Persona:
    return Persona(
        id=row["id"],
        profile_name=row["profile_name"],
        chat_name=row["chat_name"],
        age=row["age"],
        pronouns=row["pronouns"],
        height=row["height"],
        build=row["build"],
        hair=row["hair"],
        eyes=row["eyes"],
        skin=row["skin"],
        clothing=row["clothing"],
        appearance_description=row["appearance_description"],
        traits=_parse_list(row["traits"]),
        personality_description=row["personality_description"],
        likes=_parse_list(row["likes"]),
        dislikes=_parse_list(row["dislikes"]),
        habits=_parse_list(row["habits"]),
        speaking_style=row["speaking_style"],
        biography=row["biography"],
        occupation=row["occupation"],
        location=row["location"],
        additional_facts=_parse_list(row["additional_facts"]),
        how_they_act=row["how_they_act"],
        how_they_respond=row["how_they_respond"],
        custom_instructions=row["custom_instructions"],
        example_dialogues=_parse_list(row["example_dialogues"]),
        family_tree=_parse_list(row["family_tree"]) if "family_tree" in row.keys() else [],
        modes=_parse_list(row["modes"]) if "modes" in row.keys() else [],
        active_mode=row["active_mode"] if "active_mode" in row.keys() else None,
        relationships=_parse_list(row["relationships"]) if "relationships" in row.keys() else [],
        avatar_path=row["avatar_path"],
        tags=_parse_list(row["tags"]),
        is_archived=bool(row["is_archived"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class PersonaService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, data: PersonaCreate) -> Persona:
        persona_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO personas (
                id, profile_name, chat_name, age, pronouns,
                height, build, hair, eyes, skin, clothing, appearance_description,
                traits, personality_description, likes, dislikes, habits, speaking_style,
                biography, occupation, location, additional_facts,
                how_they_act, how_they_respond, custom_instructions,
                example_dialogues, tags
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?
            )
            """,
            (
                persona_id,
                data.profile_name,
                data.chat_name,
                data.age,
                data.pronouns,
                data.height,
                data.build,
                data.hair,
                data.eyes,
                data.skin,
                data.clothing,
                data.appearance_description,
                _json_list(data.traits),
                data.personality_description,
                _json_list(data.likes),
                _json_list(data.dislikes),
                _json_list(data.habits),
                data.speaking_style,
                data.biography,
                data.occupation,
                data.location,
                _json_list(data.additional_facts),
                data.how_they_act,
                data.how_they_respond,
                data.custom_instructions,
                _json_list([d.model_dump() for d in data.example_dialogues]),
                _json_list(data.tags),
            ),
        )
        await self.db.commit()
        return await self.get(persona_id)  # type: ignore

    async def get(self, persona_id: str) -> Optional[Persona]:
        cursor = await self.db.execute(
            "SELECT * FROM personas WHERE id = ?", (persona_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_persona(row)

    async def list(
        self,
        include_archived: bool = False,
        search: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Persona]:
        clauses = []
        params: list = []
        if not include_archived:
            clauses.append("is_archived = 0")
        if search:
            clauses.append("(profile_name LIKE ? OR chat_name LIKE ? OR tags LIKE ?)")
            q = f"%{search}%"
            params.extend([q, q, q])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM personas{where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_persona(r) for r in rows]

    async def update(self, persona_id: str, data: PersonaUpdate) -> Optional[Persona]:
        existing = await self.get(persona_id)
        if existing is None:
            return None

        fields = data.model_dump(exclude_unset=True)
        if not fields:
            return existing

        # Serialise list / nested fields
        for key in ("traits", "likes", "dislikes", "habits", "additional_facts", "tags"):
            if key in fields and fields[key] is not None:
                fields[key] = _json_list(fields[key])
        for jf in ("example_dialogues", "family_tree", "relationships", "modes", "traits", "likes", "dislikes", "habits", "additional_facts", "tags"):
            if jf in fields and fields[jf] is not None:
                fields[jf] = _json_list(fields[jf])
        if False and "example_dialogues" in fields and fields["example_dialogues"] is not None:
            fields["example_dialogues"] = _json_list(
                [d if isinstance(d, dict) else d.model_dump() for d in fields["example_dialogues"]]
            )
        if "is_archived" in fields:
            fields["is_archived"] = 1 if fields["is_archived"] else 0

        # Only update columns that exist (handles pre-migration DBs)
        cursor = await self.db.execute("PRAGMA table_info(personas)")
        existing_cols = {row[1] for row in await cursor.fetchall()}
        fields = {k: v for k, v in fields.items() if k in existing_cols}
        if not fields:
            return existing
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [persona_id]
        await self.db.execute(
            f"UPDATE personas SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        await self.db.commit()
        return await self.get(persona_id)

    async def delete(self, persona_id: str, hard: bool = False) -> bool:
        if hard:
            cursor = await self.db.execute(
                "DELETE FROM personas WHERE id = ?", (persona_id,)
            )
        else:
            cursor = await self.db.execute(
                "UPDATE personas SET is_archived = 1, updated_at = datetime('now') WHERE id = ?",
                (persona_id,),
            )
        await self.db.commit()
        return cursor.rowcount > 0
