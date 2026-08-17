"""Branches, ratings, pins, mutes, intensity helpers."""

from __future__ import annotations

import json
import uuid
from typing import Optional

import aiosqlite


def _parse_list(raw: Optional[str]) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


class AdvancedChatService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self._ready = False

    async def _ensure(self) -> None:
        if self._ready:
            return
        from app.schema_ensure import ensure_columns

        await ensure_columns(self.db)
        self._ready = True

    # ── Branches ──────────────────────────────────────────────

    async def list_branches(self, conversation_id: str) -> list[dict]:
        await self._ensure()
        try:
            cursor = await self.db.execute(
                """
                SELECT * FROM conversation_branches
                WHERE conversation_id = ?
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    async def create_branch(
        self,
        conversation_id: str,
        name: str,
        *,
        icon: str = "🌿",
        from_message_id: Optional[str] = None,
        parent_branch_id: Optional[str] = None,
    ) -> dict:
        await self._ensure()
        bid = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO conversation_branches
                (id, conversation_id, name, icon, parent_branch_id, created_from_message_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                bid,
                conversation_id,
                name.strip() or "Branch",
                icon,
                parent_branch_id,
                from_message_id,
            ),
        )
        try:
            await self.db.execute(
                "UPDATE conversations SET active_branch_id = ?, updated_at = datetime('now') WHERE id = ?",
                (bid, conversation_id),
            )
        except Exception:
            pass
        await self.db.commit()
        cursor = await self.db.execute(
            "SELECT * FROM conversation_branches WHERE id = ?", (bid,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"id": bid, "name": name, "icon": icon}

    async def set_active_branch(
        self, conversation_id: str, branch_id: Optional[str]
    ) -> None:
        await self._ensure()
        try:
            await self.db.execute(
                "UPDATE conversations SET active_branch_id = ?, updated_at = datetime('now') WHERE id = ?",
                (branch_id, conversation_id),
            )
            await self.db.commit()
        except Exception:
            pass

    # ── Ratings ───────────────────────────────────────────────

    async def rate_message(self, message_id: str, rating: Optional[int]) -> bool:
        await self._ensure()
        if rating is not None and rating not in (-1, 1):
            raise ValueError("rating must be -1, 1, or null")
        try:
            cursor = await self.db.execute(
                "UPDATE messages SET rating = ? WHERE id = ?",
                (rating, message_id),
            )
            await self.db.commit()
            return cursor.rowcount > 0
        except Exception:
            return False

    # ── Pins ──────────────────────────────────────────────────

    async def get_pins(self, conversation_id: str) -> list[str]:
        await self._ensure()
        try:
            cursor = await self.db.execute(
                "SELECT pinned_lines FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return []
            keys = row.keys()
            return _parse_list(
                row["pinned_lines"] if "pinned_lines" in keys else None
            )
        except Exception:
            return []

    async def set_pins(self, conversation_id: str, pins: list[str]) -> list[str]:
        await self._ensure()
        pins = [p.strip() for p in pins if p and p.strip()][:40]
        try:
            await self.db.execute(
                "UPDATE conversations SET pinned_lines = ?, updated_at = datetime('now') WHERE id = ?",
                (json.dumps(pins), conversation_id),
            )
            await self.db.commit()
        except Exception:
            pass
        return pins

    async def add_pin(self, conversation_id: str, text: str) -> list[str]:
        pins = await self.get_pins(conversation_id)
        text = text.strip()
        if text and text not in pins:
            pins.append(text)
        return await self.set_pins(conversation_id, pins)

    # ── Mutes ─────────────────────────────────────────────────

    async def get_mutes(self, conversation_id: str) -> list[str]:
        await self._ensure()
        try:
            cursor = await self.db.execute(
                "SELECT topic_mutes FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return []
            keys = row.keys()
            return _parse_list(row["topic_mutes"] if "topic_mutes" in keys else None)
        except Exception:
            return []

    async def set_mutes(self, conversation_id: str, mutes: list[str]) -> list[str]:
        await self._ensure()
        mutes = [m.strip().lower() for m in mutes if m and m.strip()][:40]
        try:
            await self.db.execute(
                "UPDATE conversations SET topic_mutes = ?, updated_at = datetime('now') WHERE id = ?",
                (json.dumps(mutes), conversation_id),
            )
            await self.db.commit()
        except Exception:
            pass
        return mutes

    async def add_mute(self, conversation_id: str, topic: str) -> list[str]:
        mutes = await self.get_mutes(conversation_id)
        topic = topic.strip().lower()
        if topic and topic not in mutes:
            mutes.append(topic)
        return await self.set_mutes(conversation_id, mutes)

    async def remove_mute(self, conversation_id: str, topic: str) -> list[str]:
        topic = topic.strip().lower()
        mutes = [m for m in await self.get_mutes(conversation_id) if m != topic]
        return await self.set_mutes(conversation_id, mutes)

    # ── Intensity ─────────────────────────────────────────────

    async def set_intensity(self, conversation_id: str, value: float) -> float:
        await self._ensure()
        value = max(0.0, min(1.0, float(value)))
        try:
            await self.db.execute(
                "UPDATE conversations SET emotion_intensity = ?, updated_at = datetime('now') WHERE id = ?",
                (value, conversation_id),
            )
            await self.db.commit()
        except Exception:
            pass
        return value

    # ── Prompt fragments ──────────────────────────────────────

    def intensity_prompt(self, value: Optional[float]) -> str:
        if value is None:
            value = 0.5
        if value < 0.25:
            return "EMOTIONAL INTENSITY: very low — calm, restrained, understated reactions."
        if value < 0.45:
            return "EMOTIONAL INTENSITY: mild — gentle feelings, soft delivery."
        if value < 0.6:
            return "EMOTIONAL INTENSITY: balanced — natural emotional range."
        if value < 0.8:
            return "EMOTIONAL INTENSITY: high — vivid feelings, stronger reactions."
        return "EMOTIONAL INTENSITY: peak — intense, charged, dramatic emotional beats."

    def mutes_prompt(self, mutes: list[str]) -> str:
        if not mutes:
            return ""
        return (
            "TOPIC MUTE LIST (do not bring these up or dwell on them unless the user insists): "
            + ", ".join(mutes)
        )

    def pins_prompt(self, pins: list[str]) -> str:
        if not pins:
            return ""
        lines = ["PINNED BEATS (must remain true; do not contradict):"]
        for p in pins[-15:]:
            lines.append(f"- {p}")
        return "\n".join(lines)

    def tone_prompt(self, tone: Optional[str]) -> str:
        if not tone:
            return ""
        tones = {
            "soft": "TONE SHIFT: softer, warmer, gentler wording and actions.",
            "sharp": "TONE SHIFT: sharper, colder, more cutting or confrontational.",
            "playful": "TONE SHIFT: more playful, teasing, light, witty.",
            "angsty": "TONE SHIFT: heavier emotional weight, tension, vulnerability.",
            "formal": "TONE SHIFT: more formal, composed, polite distance.",
        }
        return tones.get(tone.lower(), f"TONE SHIFT: {tone}")

    def triggers_prompt(self, triggers: list[dict], user_text: str) -> str:
        if not triggers or not user_text:
            return ""
        low = user_text.lower()
        hits = []
        for t in triggers:
            phrase = (t.get("phrase") or "").lower().strip()
            reaction = (t.get("reaction") or "").strip()
            if phrase and phrase in low and reaction:
                hits.append(
                    f'- User said something matching "{phrase}" → bias toward: {reaction}'
                )
        if not hits:
            return ""
        return "TRIGGER HITS:\n" + "\n".join(hits)
