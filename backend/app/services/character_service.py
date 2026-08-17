from __future__ import annotations

import json
import uuid
from typing import Any, Optional

import aiosqlite

from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate


def _json_list(value: object) -> str:
    if value is None:
        return "[]"
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        out = []
        for d in value:
            if hasattr(d, "model_dump"):
                out.append(d.model_dump())
            elif isinstance(d, dict):
                out.append(d)
            else:
                out.append(d)
        return json.dumps(out)
    return json.dumps(value)


def _parse_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _g(row: aiosqlite.Row, key: str, default=None):
    try:
        keys = row.keys()
        if key in keys:
            return row[key]
    except Exception:
        pass
    return default


def _row_to_character(row: aiosqlite.Row) -> Character:
    return Character(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        avatar_path=_g(row, "avatar_path"),
        filter_level=_g(row, "filter_level") or "mature",
        system_prompt=row["system_prompt"],
        baseline_personality=row["baseline_personality"],
        scenario=row["scenario"],
        greeting=row["greeting"],
        example_dialogues=_parse_list(row["example_dialogues"]),
        age=_g(row, "age"),
        pronouns=_g(row, "pronouns"),
        height=_g(row, "height"),
        build=_g(row, "build"),
        hair=_g(row, "hair"),
        eyes=_g(row, "eyes"),
        skin=_g(row, "skin"),
        clothing=_g(row, "clothing"),
        appearance_description=_g(row, "appearance_description"),
        traits=_parse_list(_g(row, "traits")),
        likes=_parse_list(_g(row, "likes")),
        dislikes=_parse_list(_g(row, "dislikes")),
        habits=_parse_list(_g(row, "habits")),
        speaking_style=_g(row, "speaking_style"),
        occupation=_g(row, "occupation"),
        location=_g(row, "location"),
        biography=_g(row, "biography"),
        additional_facts=_parse_list(_g(row, "additional_facts")),
        how_they_act=_g(row, "how_they_act"),
        how_they_respond=_g(row, "how_they_respond"),
        custom_instructions=_g(row, "custom_instructions"),
        family_tree=_parse_list(_g(row, "family_tree")),
        relationships=_parse_list(_g(row, "relationships")),
        goals=_g(row, "goals"),
        fears=_g(row, "fears"),
        secrets=_g(row, "secrets"),
        temperature=row["temperature"],
        top_p=row["top_p"],
        repetition_penalty=row["repetition_penalty"],
        context_window=row["context_window"],
        max_tokens=row["max_tokens"],
        model_profile_id=row["model_profile_id"],
        model_name=row["model_name"],
        side_character_enabled=bool(row["side_character_enabled"]),
        side_character_instructions=row["side_character_instructions"],
        image_gen_enabled=bool(_g(row, "image_gen_enabled") or 0),
        image_gen_style=_g(row, "image_gen_style"),
        side_roster=_parse_list(_g(row, "side_roster")),
        mood_board=_parse_list(_g(row, "mood_board")),
        trigger_phrases=_parse_list(_g(row, "trigger_phrases")),
        tags=_parse_list(row["tags"]),
        version=row["version"] or 1,
        is_archived=bool(row["is_archived"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


_JSON_FIELDS = {
    "example_dialogues",
    "tags",
    "traits",
    "likes",
    "dislikes",
    "habits",
    "additional_facts",
    "family_tree",
    "relationships",
    "side_roster",
    "mood_board",
    "trigger_phrases",
}
_BOOL_FIELDS = {
    "side_character_enabled",
    "image_gen_enabled",
    "is_archived",
}


class CharacterService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, data: CharacterCreate) -> Character:
        character_id = str(uuid.uuid4())
        dump = data.model_dump()
        cols = [
            "id", "name", "description", "filter_level",
            "system_prompt", "baseline_personality", "scenario", "greeting",
            "example_dialogues",
            "age", "pronouns", "height", "build", "hair", "eyes", "skin", "clothing",
            "appearance_description", "traits", "likes", "dislikes", "habits",
            "speaking_style", "occupation", "location", "biography", "additional_facts",
            "how_they_act", "how_they_respond", "custom_instructions",
            "family_tree", "relationships", "goals", "fears", "secrets",
            "temperature", "top_p", "repetition_penalty", "context_window", "max_tokens",
            "model_profile_id", "model_name",
            "side_character_enabled", "side_character_instructions",
            "image_gen_enabled", "image_gen_style", "tags",
        ]
        values: list[Any] = [character_id]
        for c in cols[1:]:
            v = dump.get(c)
            if c in _JSON_FIELDS:
                v = _json_list(v)
            elif c in _BOOL_FIELDS:
                v = 1 if v else 0
            values.append(v)
        placeholders = ", ".join("?" for _ in cols)
        col_sql = ", ".join(cols)
        try:
            await self.db.execute(
                f"INSERT INTO characters ({col_sql}) VALUES ({placeholders})",
                values,
            )
        except aiosqlite.OperationalError:
            # Pre-migration fallback: core columns only
            await self.db.execute(
                """
                INSERT INTO characters (
                    id, name, description, system_prompt, baseline_personality,
                    scenario, greeting, example_dialogues, temperature, top_p,
                    repetition_penalty, context_window, max_tokens, model_name,
                    side_character_enabled, side_character_instructions, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    character_id,
                    data.name,
                    data.description,
                    data.system_prompt,
                    data.baseline_personality,
                    data.scenario,
                    data.greeting,
                    _json_list(data.example_dialogues),
                    data.temperature,
                    data.top_p,
                    data.repetition_penalty,
                    data.context_window,
                    data.max_tokens,
                    data.model_name,
                    1 if data.side_character_enabled else 0,
                    data.side_character_instructions,
                    _json_list(data.tags),
                ),
            )
        await self.db.commit()
        return await self.get(character_id)  # type: ignore

    async def get(self, character_id: str) -> Optional[Character]:
        cursor = await self.db.execute(
            "SELECT * FROM characters WHERE id = ?", (character_id,)
        )
        row = await cursor.fetchone()
        return _row_to_character(row) if row else None

    async def list(
        self,
        include_archived: bool = False,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Character]:
        clauses = []
        params: list[Any] = []
        if not include_archived:
            clauses.append("is_archived = 0")
        if search:
            clauses.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
            q = f"%{search}%"
            params.extend([q, q, q])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"SELECT * FROM characters{where} ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_character(r) for r in rows]

    async def chat_count(self, character_id: str) -> int:
        cursor = await self.db.execute(
            "SELECT COUNT(*) AS c FROM conversations WHERE character_id = ? AND is_archived = 0",
            (character_id,),
        )
        row = await cursor.fetchone()
        return int(row["c"]) if row else 0

    async def update(self, character_id: str, data: CharacterUpdate) -> Optional[Character]:
        existing = await self.get(character_id)
        if existing is None:
            return None
        fields = data.model_dump(exclude_unset=True)
        if not fields:
            return existing
        for key in list(fields.keys()):
            if key in _JSON_FIELDS and fields[key] is not None:
                fields[key] = _json_list(fields[key])
            if key in _BOOL_FIELDS:
                fields[key] = 1 if fields[key] else 0
        fields["version"] = existing.version + 1
        cursor = await self.db.execute("PRAGMA table_info(characters)")
        existing_cols = {row[1] for row in await cursor.fetchall()}
        fields = {k: v for k, v in fields.items() if k in existing_cols}
        if not fields:
            return existing
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [character_id]
        await self.db.execute(
            f"UPDATE characters SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        await self.db.commit()
        return await self.get(character_id)

    async def delete(self, character_id: str, hard: bool = False) -> bool:
        if hard:
            cursor = await self.db.execute(
                "DELETE FROM characters WHERE id = ?", (character_id,)
            )
        else:
            cursor = await self.db.execute(
                "UPDATE characters SET is_archived = 1, updated_at = datetime('now') WHERE id = ?",
                (character_id,),
            )
        await self.db.commit()
        return cursor.rowcount > 0
