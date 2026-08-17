"""
Memory graph: extract, store, retrieve relevant memories for prompts.
Does not retrain the model — retrieval only.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import aiosqlite


@dataclass
class Memory:
    id: str
    owner_type: str
    owner_id: str
    content: str
    category: Optional[str] = None
    confidence: float = 0.7
    importance: float = 0.5
    source_conversation_id: Optional[str] = None
    source_message_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    is_archived: bool = False
    is_pinned: bool = False
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


def _parse_tags(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _row(row: aiosqlite.Row) -> Memory:
    return Memory(
        id=row["id"],
        owner_type=row["owner_type"],
        owner_id=row["owner_id"],
        content=row["content"],
        category=row["category"],
        confidence=row["confidence"] or 0.7,
        importance=row["importance"] or 0.5,
        source_conversation_id=row["source_conversation_id"],
        source_message_id=row["source_message_id"],
        tags=_parse_tags(row["tags"]),
        is_archived=bool(row["is_archived"]),
        is_pinned=bool(row["is_pinned"]) if "is_pinned" in row.keys() else False,
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )


# Lightweight fact extractors from user text
_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    ("preference", re.compile(r"\bi (?:like|love|enjoy|prefer)\s+([^.!?\n]{2,80})", re.I), 0.7),
    ("preference", re.compile(r"\bi (?:hate|dislike|can't stand)\s+([^.!?\n]{2,80})", re.I), 0.7),
    ("fact", re.compile(r"\bmy name is\s+([^.!?\n]{2,40})", re.I), 0.9),
    ("fact", re.compile(r"\bi(?:'m| am)\s+(?:a |an )?([^.!?\n]{2,60})", re.I), 0.55),
    ("fact", re.compile(r"\bi (?:work|live|study)(?:\s+as)?\s+([^.!?\n]{2,60})", re.I), 0.65),
    ("event", re.compile(r"\b(?:yesterday|today|last night|earlier)\s+([^.!?\n]{5,80})", re.I), 0.5),
]


class MemoryService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(
        self,
        *,
        owner_type: str,
        owner_id: str,
        content: str,
        category: Optional[str] = None,
        confidence: float = 0.7,
        importance: float = 0.5,
        source_conversation_id: Optional[str] = None,
        source_message_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Memory:
        content = content.strip()
        if not content:
            raise ValueError("Empty memory")
        # Dedup: same owner + near-identical content
        existing = await self.find_similar(owner_type, owner_id, content)
        if existing:
            return existing

        mid = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO memories (
                id, owner_type, owner_id, content, category, confidence, importance,
                source_conversation_id, source_message_id, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mid,
                owner_type,
                owner_id,
                content,
                category,
                confidence,
                importance,
                source_conversation_id,
                source_message_id,
                json.dumps(tags or []),
            ),
        )
        await self.db.commit()
        return await self.get(mid)  # type: ignore

    async def get(self, memory_id: str) -> Optional[Memory]:
        cursor = await self.db.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        )
        row = await cursor.fetchone()
        return _row(row) if row else None

    async def find_similar(
        self, owner_type: str, owner_id: str, content: str
    ) -> Optional[Memory]:
        cursor = await self.db.execute(
            """
            SELECT * FROM memories
            WHERE owner_type = ? AND owner_id = ? AND is_archived = 0
              AND lower(content) = lower(?)
            LIMIT 1
            """,
            (owner_type, owner_id, content.strip()),
        )
        row = await cursor.fetchone()
        return _row(row) if row else None

    async def list(
        self,
        *,
        owner_type: Optional[str] = None,
        owner_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[Memory]:
        clauses = ["is_archived = 0"]
        params: list = []
        if owner_type:
            clauses.append("owner_type = ?")
            params.append(owner_type)
        if owner_id:
            clauses.append("owner_id = ?")
            params.append(owner_id)
        where = " AND ".join(clauses)
        cursor = await self.db.execute(
            f"""
            SELECT * FROM memories WHERE {where}
            ORDER BY importance DESC, updated_at DESC
            LIMIT ?
            """,
            params + [limit],
        )
        return [_row(r) for r in await cursor.fetchall()]

    async def retrieve_for_prompt(
        self,
        *,
        conversation_id: str,
        character_id: str,
        persona_id: str,
        world_id: Optional[str] = None,
        query_text: str = "",
        limit: int = 12,
    ) -> list[Memory]:
        """
        Pull relevant memories: conversation + character + persona + global + world.
        Simple keyword overlap scoring + importance.
        """
        owners = [
            ("conversation", conversation_id),
            ("character", character_id),
            ("persona", persona_id),
            ("global", "global"),
        ]
        if world_id:
            owners.append(("world", world_id))

        results: list[Memory] = []
        for ot, oid in owners:
            results.extend(await self.list(owner_type=ot, owner_id=oid, limit=40))

        q_tokens = set(re.findall(r"[a-z0-9']{3,}", (query_text or "").lower()))
        scored: list[tuple[float, Memory]] = []
        for m in results:
            score = float(m.importance)
            if getattr(m, 'is_pinned', False):
                score += 2.0
            if q_tokens:
                m_tokens = set(re.findall(r"[a-z0-9']{3,}", m.content.lower()))
                overlap = len(q_tokens & m_tokens)
                score += overlap * 0.15
            score += float(m.confidence) * 0.1
            scored.append((score, m))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [m for _, m in scored[:limit]]

        # Touch last_used
        for m in top:
            await self.db.execute(
                "UPDATE memories SET last_used_at = datetime('now') WHERE id = ?",
                (m.id,),
            )
        if top:
            await self.db.commit()
        return top

    async def extract_from_user_message(
        self,
        *,
        text: str,
        conversation_id: str,
        message_id: Optional[str],
        persona_id: str,
        character_id: str,
    ) -> list[Memory]:
        """Heuristic extraction into persona + conversation memories."""
        created: list[Memory] = []
        for category, pattern, importance in _PATTERNS:
            for m in pattern.finditer(text or ""):
                snippet = m.group(0).strip()
                if len(snippet) < 5:
                    continue
                try:
                    mem = await self.create(
                        owner_type="persona",
                        owner_id=persona_id,
                        content=snippet,
                        category=category,
                        confidence=0.65,
                        importance=importance,
                        source_conversation_id=conversation_id,
                        source_message_id=message_id,
                    )
                    created.append(mem)
                    # Also attach a copy scope to conversation for local recall
                    await self.create(
                        owner_type="conversation",
                        owner_id=conversation_id,
                        content=snippet,
                        category=category,
                        confidence=0.6,
                        importance=importance * 0.9,
                        source_conversation_id=conversation_id,
                        source_message_id=message_id,
                    )
                except ValueError:
                    continue
        return created

    def format_for_prompt(self, memories: list[Memory]) -> str:
        if not memories:
            return ""
        lines = ["Relevant memories (use naturally, do not list them back):"]
        for m in memories:
            tag = m.category or "note"
            lines.append(f"- [{tag}] {m.content}")
        return "\n".join(lines)

    async def delete(self, memory_id: str, hard: bool = False) -> bool:
        if hard:
            cur = await self.db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        else:
            cur = await self.db.execute(
                "UPDATE memories SET is_archived = 1 WHERE id = ?", (memory_id,)
            )
        await self.db.commit()
        return cur.rowcount > 0
