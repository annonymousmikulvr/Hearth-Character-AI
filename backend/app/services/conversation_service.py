from __future__ import annotations

import uuid
from typing import Optional

import aiosqlite

from app.models.conversation import Conversation, Message
from app.services.templates import expand_templates
from app.schemas.conversation import ConversationCreate, ConversationUpdate, MessageCreate
from app.services.character_service import CharacterService
from app.services.persona_service import PersonaService


def _row_to_conversation(row: aiosqlite.Row) -> Conversation:
    keys = row.keys()
    return Conversation(
        id=row["id"],
        title=row["title"],
        character_id=row["character_id"],
        persona_id=row["persona_id"],
        persona_display_name=row["persona_display_name"],
        world_id=row["world_id"],
        temperature=row["temperature"],
        top_p=row["top_p"],
        repetition_penalty=row["repetition_penalty"],
        max_tokens=row["max_tokens"],
        model_name=row["model_name"],
        is_archived=bool(row["is_archived"]),
        last_message_at=row["last_message_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        character_name=row["character_name"] if "character_name" in keys else None,
        persona_profile_name=row["persona_profile_name"] if "persona_profile_name" in keys else None,
        seed_notes=row["seed_notes"] if "seed_notes" in keys else None,
        is_custom=bool(row["is_custom"]) if "is_custom" in keys else False,
        filter_level=row["filter_level"] if "filter_level" in keys else None,
    )


def _row_to_message(row: aiosqlite.Row) -> Message:
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        speaker_type=row["speaker_type"],
        speaker_id=row["speaker_id"],
        speaker_name=row["speaker_name"],
        raw_content=row["raw_content"],
        content_format=row["content_format"] or "markup",
        parent_message_id=row["parent_message_id"],
        variant_index=row["variant_index"] or 0,
        is_selected_variant=bool(row["is_selected_variant"]),
        temperature=row["temperature"],
        max_tokens=row["max_tokens"],
        model_name=row["model_name"],
        token_count=row["token_count"],
        generation_ms=row["generation_ms"],
        created_at=row["created_at"],
    )


class ConversationService:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db

    async def create(self, data: ConversationCreate) -> Conversation:
        # Validate character & persona exist
        char_svc = CharacterService(self.db)
        persona_svc = PersonaService(self.db)
        character = await char_svc.get(data.character_id)
        if character is None or character.is_archived:
            raise ValueError("Character not found or archived")
        persona = await persona_svc.get(data.persona_id)
        if persona is None or persona.is_archived:
            raise ValueError("Persona not found or archived")

        display_name = (data.persona_display_name or persona.chat_name or persona.profile_name).strip()
        if not display_name:
            raise ValueError("persona_display_name is required")

        # Inherit generation defaults from character when not supplied
        temperature = data.temperature if data.temperature is not None else character.temperature
        top_p = data.top_p if data.top_p is not None else character.top_p
        repetition_penalty = (
            data.repetition_penalty
            if data.repetition_penalty is not None
            else character.repetition_penalty
        )
        max_tokens = data.max_tokens if data.max_tokens is not None else character.max_tokens
        model_name = data.model_name or character.model_name

        title = data.title or f"Chat with {character.name}"

        conv_id = str(uuid.uuid4())
        seed_notes = getattr(data, "seed_notes", None)
        is_custom = 1 if getattr(data, "is_custom", False) else 0
        await self.db.execute(
            """
            INSERT INTO conversations (
                id, title, character_id, persona_id, persona_display_name, world_id,
                temperature, top_p, repetition_penalty, max_tokens, model_name,
                seed_notes, is_custom
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conv_id,
                title,
                data.character_id,
                data.persona_id,
                display_name,
                data.world_id,
                temperature,
                top_p,
                repetition_penalty,
                max_tokens,
                model_name,
                seed_notes,
                is_custom,
            ),
        )
        await self.db.commit()

        # Custom seed messages (user-authored history)
        seed_messages = getattr(data, "seed_messages", None) or []
        if seed_messages:
            for sm in seed_messages:
                role = (sm.get("role") or "user").lower()
                content = (sm.get("content") or sm.get("raw_content") or "").strip()
                if not content:
                    continue
                if role == "assistant":
                    await self._insert_message(
                        conversation_id=conv_id,
                        role="assistant",
                        speaker_type="primary",
                        speaker_id=character.id,
                        speaker_name=character.name,
                        raw_content=content,
                    )
                elif role == "system":
                    await self._insert_message(
                        conversation_id=conv_id,
                        role="system",
                        speaker_type="system",
                        speaker_name="System",
                        raw_content=content,
                    )
                else:
                    await self._insert_message(
                        conversation_id=conv_id,
                        role="user",
                        speaker_type="user",
                        speaker_id=persona.id,
                        speaker_name=display_name,
                        raw_content=content,
                    )
        # Greeting: always for standard chats; also when custom has no seed messages
        should_greet = bool(character.greeting and character.greeting.strip()) and (
            not is_custom or not seed_messages
        )
        if should_greet:
            greet = expand_templates(
                character.greeting.strip(),
                user_name=display_name,
                char_name=character.name,
                persona_name=persona.profile_name,
            )
            await self._insert_message(
                conversation_id=conv_id,
                role="assistant",
                speaker_type="primary",
                speaker_id=character.id,
                speaker_name=character.name,
                raw_content=greet,
            )

        # Inject seed_notes as a system message once
        if seed_notes and seed_notes.strip():
            notes = expand_templates(
                seed_notes.strip(),
                user_name=display_name,
                char_name=character.name,
                persona_name=persona.profile_name,
            )
            await self._insert_message(
                conversation_id=conv_id,
                role="system",
                speaker_type="system",
                speaker_name="System",
                raw_content=f"[Custom chat context]\n{notes}",
            )

        return await self.get(conv_id)  # type: ignore

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        cursor = await self.db.execute(
            """
            SELECT c.*,
                   ch.name AS character_name,
                   p.profile_name AS persona_profile_name
            FROM conversations c
            JOIN characters ch ON ch.id = c.character_id
            JOIN personas p ON p.id = c.persona_id
            WHERE c.id = ?
            """,
            (conversation_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_conversation(row)

    async def list(
        self,
        include_archived: bool = False,
        character_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conversation]:
        clauses = []
        params: list = []
        if not include_archived:
            clauses.append("c.is_archived = 0")
        if character_id:
            clauses.append("c.character_id = ?")
            params.append(character_id)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT c.*,
                   ch.name AS character_name,
                   p.profile_name AS persona_profile_name
            FROM conversations c
            JOIN characters ch ON ch.id = c.character_id
            JOIN personas p ON p.id = c.persona_id
            {where}
            ORDER BY COALESCE(c.last_message_at, c.updated_at) DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor = await self.db.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_conversation(r) for r in rows]

    async def update(
        self, conversation_id: str, data: ConversationUpdate
    ) -> Optional[Conversation]:
        existing = await self.get(conversation_id)
        if existing is None:
            return None
        fields = data.model_dump(exclude_unset=True)
        if not fields:
            return existing
        if "is_archived" in fields:
            fields["is_archived"] = 1 if fields["is_archived"] else 0
        # Ensure filter_level column exists (older DBs)
        cursor = await self.db.execute("PRAGMA table_info(conversations)")
        existing_cols = {row[1] for row in await cursor.fetchall()}
        if "filter_level" not in existing_cols:
            try:
                await self.db.execute(
                    "ALTER TABLE conversations ADD COLUMN filter_level TEXT"
                )
                await self.db.commit()
                existing_cols.add("filter_level")
            except Exception:
                pass
        fields = {k: v for k, v in fields.items() if k in existing_cols}
        if not fields:
            return existing
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [conversation_id]
        await self.db.execute(
            f"UPDATE conversations SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        await self.db.commit()
        return await self.get(conversation_id)

    async def delete(self, conversation_id: str, hard: bool = False) -> bool:
        if hard:
            cursor = await self.db.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
        else:
            cursor = await self.db.execute(
                "UPDATE conversations SET is_archived = 1, updated_at = datetime('now') WHERE id = ?",
                (conversation_id,),
            )
        await self.db.commit()
        return cursor.rowcount > 0

    # ── Messages ──────────────────────────────────────────────

    async def _insert_message(
        self,
        *,
        conversation_id: str,
        role: str,
        speaker_type: str,
        speaker_name: str,
        raw_content: str,
        speaker_id: Optional[str] = None,
        content_format: str = "markup",
        parent_message_id: Optional[str] = None,
        variant_index: int = 0,
        is_selected_variant: bool = True,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model_name: Optional[str] = None,
    ) -> Message:
        msg_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO messages (
                id, conversation_id, role, speaker_type, speaker_id, speaker_name,
                raw_content, content_format, parent_message_id, variant_index,
                is_selected_variant, temperature, max_tokens, model_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg_id,
                conversation_id,
                role,
                speaker_type,
                speaker_id,
                speaker_name,
                raw_content,
                content_format,
                parent_message_id,
                variant_index,
                1 if is_selected_variant else 0,
                temperature,
                max_tokens,
                model_name,
            ),
        )
        await self.db.execute(
            """
            UPDATE conversations
            SET last_message_at = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
            """,
            (conversation_id,),
        )
        await self.db.commit()
        cursor = await self.db.execute("SELECT * FROM messages WHERE id = ?", (msg_id,))
        row = await cursor.fetchone()
        return _row_to_message(row)  # type: ignore

    async def add_user_message(
        self, conversation_id: str, data: MessageCreate
    ) -> Message:
        conv = await self.get(conversation_id)
        if conv is None:
            raise ValueError("Conversation not found")
        if conv.is_archived:
            raise ValueError("Cannot post to an archived conversation")

        return await self._insert_message(
            conversation_id=conversation_id,
            role=data.role,
            speaker_type="user" if data.role == "user" else "system",
            speaker_id=conv.persona_id if data.role == "user" else None,
            speaker_name=conv.persona_display_name if data.role == "user" else "System",
            raw_content=data.raw_content,
            content_format=data.content_format,
        )

    async def list_messages(
        self,
        conversation_id: str,
        *,
        selected_only: bool = True,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Message]:
        clauses = ["conversation_id = ?"]
        params: list = [conversation_id]
        if selected_only:
            clauses.append("is_selected_variant = 1")
        where = " AND ".join(clauses)
        cursor = await self.db.execute(
            f"""
            SELECT * FROM messages
            WHERE {where}
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = await cursor.fetchall()
        return [_row_to_message(r) for r in rows]

    async def get_message(self, message_id: str) -> Optional[Message]:
        cursor = await self.db.execute(
            "SELECT * FROM messages WHERE id = ?", (message_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return _row_to_message(row)


    async def list_variants(self, root_message_id: str) -> list[Message]:
        """All variants in a family: the root itself + children with that parent."""
        cursor = await self.db.execute(
            """
            SELECT * FROM messages
            WHERE id = ? OR parent_message_id = ?
            ORDER BY variant_index ASC, created_at ASC
            """,
            (root_message_id, root_message_id),
        )
        rows = await cursor.fetchall()
        return [_row_to_message(r) for r in rows]

    async def deselect_variants(self, root_message_id: str) -> None:
        await self.db.execute(
            """
            UPDATE messages
            SET is_selected_variant = 0
            WHERE id = ? OR parent_message_id = ?
            """,
            (root_message_id, root_message_id),
        )
        await self.db.commit()

    async def select_variant(self, message_id: str) -> Optional[Message]:
        target = await self.get_message(message_id)
        if target is None:
            return None
        root_id = target.parent_message_id or target.id
        await self.deselect_variants(root_id)
        await self.db.execute(
            "UPDATE messages SET is_selected_variant = 1 WHERE id = ?",
            (message_id,),
        )
        await self.db.commit()
        return await self.get_message(message_id)

    async def edit_message(
        self, message_id: str, raw_content: str
    ) -> Optional[Message]:
        target = await self.get_message(message_id)
        if target is None:
            return None
        # Allow editing user messages and assistant messages (content fix)
        await self.db.execute(
            """
            UPDATE messages
            SET raw_content = ?,
                edited_at = datetime('now'),
                edit_count = COALESCE(edit_count, 0) + 1
            WHERE id = ?
            """,
            (raw_content, message_id),
        )
        await self.db.execute(
            """
            UPDATE conversations
            SET updated_at = datetime('now')
            WHERE id = ?
            """,
            (target.conversation_id,),
        )
        await self.db.commit()
        return await self.get_message(message_id)

    async def delete_message(self, message_id: str) -> bool:
        cursor = await self.db.execute(
            "DELETE FROM messages WHERE id = ?", (message_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0


    async def delete_message_family(self, conversation_id: str, message_id: str) -> bool:
        msg = await self.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            return False
        root = msg.parent_message_id or msg.id
        await self.db.execute(
            "DELETE FROM messages WHERE id = ? OR parent_message_id = ? OR id = ?",
            (message_id, root, root),
        )
        await self.db.commit()
        return True

    async def rewind_to_message(
        self,
        conversation_id: str,
        message_id: str,
        *,
        include_message: bool = True,
    ) -> int:
        msg = await self.get_message(message_id)
        if msg is None or msg.conversation_id != conversation_id:
            raise ValueError("Message not found")
        if include_message:
            cursor = await self.db.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ? AND created_at > ?
                """,
                (conversation_id, msg.created_at),
            )
        else:
            root = msg.parent_message_id or msg.id
            cursor = await self.db.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ?
                  AND (
                    created_at > ?
                    OR id = ?
                    OR parent_message_id = ?
                    OR id = ?
                    OR parent_message_id = ?
                  )
                """,
                (conversation_id, msg.created_at, message_id, message_id, root, root),
            )
        await self.db.commit()
        return cursor.rowcount
