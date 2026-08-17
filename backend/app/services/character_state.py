"""
Living character state per conversation.
Makes characters feel more human by tracking mood, relationship, and notes
that evolve as the chat progresses — without retraining the model.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

import aiosqlite


@dataclass
class CharacterState:
    id: str
    conversation_id: str
    character_id: str
    mood: Optional[str] = None
    relationship_stage: Optional[str] = None
    emotional_notes: Optional[str] = None
    knowledge_notes: list[str] = field(default_factory=list)
    behavior_shifts: list[str] = field(default_factory=list)
    last_updated_at: Optional[str] = None

    def to_prompt_block(self) -> str:
        lines = ["Living character state for THIS conversation (update naturally over time):"]
        if self.mood:
            lines.append(f"- Current mood: {self.mood}")
        if self.relationship_stage:
            lines.append(f"- Relationship with user: {self.relationship_stage}")
        if self.emotional_notes:
            lines.append(f"- Emotional notes: {self.emotional_notes}")
        if self.knowledge_notes:
            lines.append("- Things learned in this chat:")
            for n in self.knowledge_notes[-12:]:
                lines.append(f"  • {n}")
        if self.behavior_shifts:
            lines.append("- Subtle behavior shifts:")
            for n in self.behavior_shifts[-8:]:
                lines.append(f"  • {n}")
        if len(lines) == 1:
            return ""
        lines.append(
            "Let these influence tone and choices. Do not recite this list to the user."
        )
        return "\n".join(lines)


def _parse_list(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


class CharacterStateService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def get(
        self, conversation_id: str, character_id: str
    ) -> Optional[CharacterState]:
        cursor = await self.db.execute(
            """
            SELECT * FROM conversation_character_state
            WHERE conversation_id = ? AND character_id = ?
            """,
            (conversation_id, character_id),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return CharacterState(
            id=row["id"],
            conversation_id=row["conversation_id"],
            character_id=row["character_id"],
            mood=row["mood"],
            relationship_stage=row["relationship_stage"],
            emotional_notes=row["emotional_notes"],
            knowledge_notes=_parse_list(row["knowledge_notes"]),
            behavior_shifts=_parse_list(row["behavior_shifts"]),
            last_updated_at=row["last_updated_at"],
        )

    async def ensure(
        self, conversation_id: str, character_id: str
    ) -> CharacterState:
        existing = await self.get(conversation_id, character_id)
        if existing:
            return existing
        sid = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO conversation_character_state
                (id, conversation_id, character_id, mood, relationship_stage)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sid, conversation_id, character_id, "neutral", "new acquaintance"),
        )
        await self.db.commit()
        return await self.get(conversation_id, character_id)  # type: ignore

    async def update_from_exchange(
        self,
        conversation_id: str,
        character_id: str,
        user_text: str,
        assistant_text: str,
    ) -> CharacterState:
        """
        Lightweight heuristic evolution after each exchange.
        A future version can use a small local model; heuristics keep it offline-safe.
        """
        state = await self.ensure(conversation_id, character_id)
        mood = state.mood or "neutral"
        rel = state.relationship_stage or "new acquaintance"
        knowledge = list(state.knowledge_notes)
        shifts = list(state.behavior_shifts)
        emotional = state.emotional_notes or ""

        low_user = (user_text or "").lower()
        low_asst = (assistant_text or "").lower()

        # Mood heuristics
        positive = any(
            w in low_user or w in low_asst
            for w in ("thank", "love", "glad", "happy", "smile", "laugh", "warm")
        )
        negative = any(
            w in low_user or w in low_asst
            for w in ("angry", "hate", "furious", "betray", "hurt", "cry", "fear")
        )
        if negative and not positive:
            mood = "tense"
        elif positive and not negative:
            mood = "warm"
        elif "joke" in low_user or "laugh" in low_asst:
            mood = "amused"

        # Relationship drift
        if any(w in low_user for w in ("friend", "trust", "together")):
            if rel in ("new acquaintance", "wary"):
                rel = "friendly"
            elif rel == "friendly":
                rel = "close"
        if any(w in low_user for w in ("enemy", "threat", "kill", "attack")):
            rel = "hostile"

        # Knowledge: extract short "I/you are/like" style facts (very light)
        for m in re.finditer(
            r"(?:i am|i'm|my name is|i like|i love|i hate)\s+([^.!?\n]{3,60})",
            low_user,
            re.I,
        ):
            fact = m.group(0).strip()
            if fact not in knowledge:
                knowledge.append(fact)
        knowledge = knowledge[-20:]

        # Behavior shift note occasionally
        if positive and "more open" not in " ".join(shifts):
            shifts.append("slightly more open with the user")
        if negative and "guarded" not in " ".join(shifts):
            shifts.append("more guarded after recent tension")
        shifts = shifts[-12:]

        if positive:
            emotional = (emotional + " Recent exchange felt positive.").strip()[-500:]
        elif negative:
            emotional = (emotional + " Recent exchange felt strained.").strip()[-500:]

        await self.db.execute(
            """
            UPDATE conversation_character_state
            SET mood = ?, relationship_stage = ?, emotional_notes = ?,
                knowledge_notes = ?, behavior_shifts = ?,
                last_updated_at = datetime('now')
            WHERE conversation_id = ? AND character_id = ?
            """,
            (
                mood,
                rel,
                emotional or None,
                json.dumps(knowledge),
                json.dumps(shifts),
                conversation_id,
                character_id,
            ),
        )
        await self.db.commit()
        return await self.get(conversation_id, character_id)  # type: ignore
