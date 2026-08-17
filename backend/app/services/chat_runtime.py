"""
Chat runtime: safety → prompt compile → local inference → safety → persist.
Supports initial generation and regeneration (variants) with anti-repetition.
"""

from __future__ import annotations

import logging
from typing import Optional

import aiosqlite

from app.inference.base import GenerationRequest
from app.inference.ollama import get_ollama_provider
from app.models.conversation import Message
from app.parsing.structured_response import parse_structured_response
from app.safety import SAFE_FALLBACK, check_text
from app.services.character_service import CharacterService
from app.services.conversation_service import ConversationService
from app.services.persona_service import PersonaService
from app.services.prompt_compiler import compile_messages, resolve_generation_params
from app.services.settings_service import SettingsService
from app.services.character_state import CharacterStateService
from app.services.memory_service import MemoryService
from app.services.world_service import WorldService
from app.parsing.markup_validate import validate_and_fix_markup
from app.parsing.side_infer import extract_candidate_names, roster_prompt
from app.services.advanced_chat import AdvancedChatService
from app.schema_ensure import ensure_columns

logger = logging.getLogger(__name__)


class ChatRuntime:
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.conversations = ConversationService(db)
        self.characters = CharacterService(db)
        self.personas = PersonaService(db)
        self.settings = SettingsService(db)
        self.char_state = CharacterStateService(db)
        self.memories = MemoryService(db)
        self.worlds = WorldService(db)
        self.advanced = AdvancedChatService(db)

    async def _load_context(self, conversation_id: str):
        conv = await self.conversations.get(conversation_id)
        if conv is None:
            raise ValueError("Conversation not found")
        if conv.is_archived:
            raise ValueError("Cannot generate in an archived conversation")
        character = await self.characters.get(conv.character_id)
        if character is None:
            raise ValueError("Character not found")
        persona = await self.personas.get(conv.persona_id)
        if persona is None:
            raise ValueError("Persona not found")
        return conv, character, persona

    async def _resolve_params(self, conv, character, *, temperature_boost: float = 0.0):
        app_model = await self.settings.get("default_model") or ""
        app_temp = float(await self.settings.get("default_temperature") or "0.85")
        app_top_p = float(await self.settings.get("default_top_p") or "0.9")
        app_rep = float(await self.settings.get("default_repetition_penalty") or "1.1")
        app_max = int(await self.settings.get("default_max_tokens") or "512")
        params = resolve_generation_params(
            character,
            conv.temperature,
            conv.top_p,
            conv.repetition_penalty,
            conv.max_tokens,
            conv.model_name,
            app_default_temperature=app_temp,
            app_default_top_p=app_top_p,
            app_default_repetition_penalty=app_rep,
            app_default_max_tokens=app_max,
            app_default_model=app_model,
            temperature_boost=temperature_boost,
        )
        if not params["model"]:
            raise ValueError(
                "No model configured. Set a default model in Settings "
                "or on the character, and ensure Ollama has the model pulled."
            )
        return params

    async def _call_model(self, params, messages, ollama_base_url: Optional[str] = None):
        settings_ollama = await self.settings.get("ollama_base_url")
        base_url = ollama_base_url or settings_ollama or "http://127.0.0.1:11434"
        provider = get_ollama_provider(base_url)
        if not await provider.is_available():
            raise ValueError(
                f"Ollama is not reachable at {base_url}. "
                "Start Ollama and pull a model first."
            )
        speed = (await self.settings.get("generation_speed") or "balanced").lower()
        extra = {"keep_alive": "10m"}
        if speed == "fast":
            extra["num_ctx"] = int(await self.settings.get("fast_num_ctx") or "2048")
            # Cap tokens in fast mode
            params["max_tokens"] = min(params["max_tokens"], int(await self.settings.get("fast_max_tokens") or "256"))
        elif speed == "quality":
            extra["num_ctx"] = int(await self.settings.get("quality_num_ctx") or "8192")
        else:
            extra["num_ctx"] = int(await self.settings.get("balanced_num_ctx") or "4096")

        result = await provider.generate(
            GenerationRequest(
                model=params["model"],
                messages=messages,
                temperature=params["temperature"],
                top_p=params["top_p"],
                max_tokens=params["max_tokens"],
                repetition_penalty=params["repetition_penalty"],
                extra=extra,
            )
        )
        if not result.ok:
            raise ValueError(result.error or "Generation failed")
        return result

    async def _persist_turns(
        self,
        conversation_id: str,
        character,
        content: str,
        params: dict,
        model_name: str,
        *,
        parent_message_id: Optional[str] = None,
        variant_index: int = 0,
        is_selected_variant: bool = True,
    ) -> list[Message]:
        # Post-safety
        post = check_text(content)
        if not post.allowed:
            logger.info("Post-generation safety block on %s", conversation_id)
            content = SAFE_FALLBACK

        # Known side names from roster + history
        known = []
        if getattr(character, "side_roster", None):
            for item in character.side_roster:
                if isinstance(item, dict) and item.get("name"):
                    known.append(str(item["name"]))
        try:
            hist = await self.conversations.list_messages(conversation_id)
            for m in hist[-30:]:
                if m.speaker_type == "side" and m.speaker_name:
                    if m.speaker_name not in known:
                        known.append(m.speaker_name)
                # names mentioned in text
                from app.parsing.side_infer import extract_candidate_names
                for n in extract_candidate_names([m.raw_content or ""], exclude={character.name}):
                    if n not in known:
                        known.append(n)
        except Exception:
            pass

        content = validate_and_fix_markup(
            content, character_name=character.name
        ).fixed_text
        turns = parse_structured_response(
            content, primary_name=character.name, known_side_names=known
        )
        saved: list[Message] = []
        for i, turn in enumerate(turns):
            turn.text = validate_and_fix_markup(
                turn.text, character_name=turn.character if turn.speaker_type == "primary" else None
            ).fixed_text
            # Variants: only the first turn of a multi-speaker regen is linked as variant root;
            # side turns attach as normal selected messages under the same response group
            # by using the same parent for primary and None for side siblings in this phase.
            is_primary = turn.speaker_type == "primary"
            msg = await self.conversations._insert_message(
                conversation_id=conversation_id,
                role="assistant",
                speaker_type=turn.speaker_type,
                speaker_id=character.id if is_primary else None,
                speaker_name=turn.character,
                raw_content=turn.text,
                parent_message_id=parent_message_id if is_primary else None,
                variant_index=variant_index if is_primary else 0,
                is_selected_variant=is_selected_variant if is_primary else True,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                model_name=model_name,
            )
            saved.append(msg)
        # Soft-pin newly spoken proper names so the model keeps them
        try:
            import re
            blob = " ".join(s.raw_content for s in saved if s.speaker_type == "primary")
            for m in re.finditer(
                r"(?:named|name is|call(?:ed)?|he's|she's|it's)\s+([A-Z][a-z]{2,14})",
                blob,
                re.I,
            ):
                nm = m.group(1)
                if nm.lower() != character.name.lower():
                    await self.advanced.add_pin(
                        conversation_id,
                        f"Name established in scene: {nm}",
                    )
            for s in saved:
                if s.speaker_type == "side" and s.speaker_name:
                    await self.advanced.add_pin(
                        conversation_id,
                        f"Side character present: {s.speaker_name}",
                    )
        except Exception:
            pass
        return saved

    async def generate_reply(
        self,
        conversation_id: str,
        *,
        ollama_base_url: Optional[str] = None,
    ) -> list[Message]:
        conv, character, persona = await self._load_context(conversation_id)
        history = await self.conversations.list_messages(conversation_id)
        # Speed: limit history turns (settings: history_limit, default 24 messages)
        await ensure_columns(self.db)
        try:
            history_limit = int(await self.settings.get("history_limit") or "24")
        except ValueError:
            history_limit = 24
        if len(history) > history_limit:
            history = history[-history_limit:]

        last_user = next((m for m in reversed(history) if m.role == "user"), None)
        if last_user:
            verdict = check_text(last_user.raw_content)
            if not verdict.allowed:
                msg = await self.conversations._insert_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    speaker_type="primary",
                    speaker_id=character.id,
                    speaker_name=character.name,
                    raw_content=SAFE_FALLBACK,
                )
                return [msg]

        params = await self._resolve_params(conv, character)
        # Mid-chat filter override
        if getattr(conv, "filter_level", None):
            character.filter_level = conv.filter_level  # type: ignore
        active_filter = getattr(character, "filter_level", None) or "mature"
        state = await self.char_state.ensure(conversation_id, character.id)
        last_user = next((m for m in reversed(history) if m.role == "user"), None)
        if last_user:
            await self.memories.extract_from_user_message(
                text=last_user.raw_content,
                conversation_id=conversation_id,
                message_id=last_user.id,
                persona_id=persona.id,
                character_id=character.id,
            )
        mems = await self.memories.retrieve_for_prompt(
            conversation_id=conversation_id,
            character_id=character.id,
            persona_id=persona.id,
            world_id=conv.world_id,
            query_text=last_user.raw_content if last_user else "",
        )
        memory_block = self.memories.format_for_prompt(mems)
        world = None
        if conv.world_id:
            world = await self.worlds.get(conv.world_id)
        world_block = world.to_prompt_block() if world else None
        filter_reminder = (
            f"ACTIVE CONTENT FILTER FOR THIS CHAT: {active_filter}. "
            "Obey the filter guide in the system prompt strictly for this reply."
        )
        format_lock = (
            "FORMAT LOCK: Only short RP beats. "
            '*I action.* then — "spoken dialogue." ' 
            "Never novel paragraphs. Never write your own name as the subject. "
            "Never mix em-dash dialogue inside action asterisks."
        )
        intensity = getattr(conv, "emotion_intensity", None)
        if intensity is None:
            intensity = 0.5
        pins = await self.advanced.get_pins(conversation_id)
        live = await self._live_overrides(conversation_id)
        live_block = self._live_overrides_prompt(live, character.name)
        mutes = await self.advanced.get_mutes(conversation_id)
        triggers = []
        # Auto side roster from recent text
        recent_texts = [m.raw_content for m in history[-12:]]
        exclude = {character.name, persona.chat_name or '', persona.profile_name or '', conv.persona_display_name or ''}
        # include explicit side_roster names first
        roster_names = []
        if getattr(character, 'side_roster', None):
            for item in character.side_roster:
                if isinstance(item, dict) and item.get('name'):
                    roster_names.append(str(item['name']))
        inferred = extract_candidate_names(recent_texts, exclude=exclude)
        for n in inferred:
            if n not in roster_names:
                roster_names.append(n)
        side_block = roster_prompt(roster_names, '\n'.join(recent_texts), primary_name=character.name)
        if getattr(character, "trigger_phrases", None):
            triggers = character.trigger_phrases if isinstance(character.trigger_phrases, list) else []
        user_txt = last_user.raw_content if last_user else ""
        tone = None  # set by regenerate with tone param if present
        extra_parts = [
            p for p in (
                world_block,
                memory_block,
                filter_reminder,
                self.advanced.intensity_prompt(float(intensity) if intensity is not None else 0.5),
                self.advanced.pins_prompt(pins),
                self.advanced.mutes_prompt(mutes),
                self.advanced.triggers_prompt(triggers, user_txt),
                format_lock,
                live_block,
                side_block,
            ) if p
        ]
        extra = "\n\n".join(extra_parts) if extra_parts else None
        messages = compile_messages(
            character,
            persona,
            conv.persona_display_name,
            history,
            character_state=state,
            extra_instructions=extra,
            max_tokens=params.get("max_tokens"),
        )
        result = await self._call_model(params, messages, ollama_base_url)
        content = validate_and_fix_markup(result.content, character_name=character.name).fixed_text
        saved = await self._persist_turns(
            conversation_id, character, content, params, result.model
        )
        asst_text = "\n".join(m.raw_content for m in saved)
        await self.char_state.update_from_exchange(
            conversation_id,
            character.id,
            last_user.raw_content if last_user else "",
            asst_text,
        )
        return saved



    async def generate_user_hint(
        self,
        conversation_id: str,
        *,
        ollama_base_url: Optional[str] = None,
        count: int = 3,
    ) -> list[str]:
        """
        Suggest user-side replies based on persona, recent history, and last AI message.
        Returns plain strings the user can edit before sending — never auto-sent.
        """
        await ensure_columns(self.db)
        conv, character, persona = await self._load_context(conversation_id)
        history = await self.conversations.list_messages(conversation_id)
        last_ai = next(
            (m for m in reversed(history) if m.role == "assistant" and m.speaker_type != "system"),
            None,
        )
        last_user = next((m for m in reversed(history) if m.role == "user"), None)
        recent = history[-8:] if history else []
        transcript = []
        for m in recent:
            who = m.speaker_name or m.role
            transcript.append(f"{who}: {m.raw_content[:400]}")
        user_name = conv.persona_display_name or persona.chat_name or persona.profile_name
        persona_bits = []
        if persona.personality_description:
            persona_bits.append(persona.personality_description[:300])
        if persona.speaking_style:
            persona_bits.append(f"Speaking style: {persona.speaking_style}")
        if persona.traits:
            persona_bits.append("Traits: " + ", ".join(persona.traits[:8]))
        if persona.additional_facts:
            persona_bits.append("Facts: " + "; ".join(persona.additional_facts[:5]))

        prompt = (
            "You write SHORT suggested replies for the USER in a roleplay chat.\n"
            "The user will pick one and may edit it — you are not the character.\n"
            f"User persona name: {user_name}\n"
            f"Persona details:\n" + ("\n".join(persona_bits) or "(minimal)") + "\n"
            f"Character they are talking to: {character.name}\n"
            f"Last character message:\n{(last_ai.raw_content if last_ai else '(none)')[:800]}\n"
            f"Recent transcript:\n" + "\n".join(transcript) + "\n\n"
            f"Write {min(5, max(1, count))} different user reply options.\n"
            "Rules:\n"
            "- Write as the USER would speak (first person from user POV is fine for actions).\n"
            "- Match the persona's voice and knowledge.\n"
            "- Respond to the last character message naturally.\n"
            "- Keep each option 1–3 short lines max.\n"
            "- Optional light markup: *action* and plain dialogue (user lines do not need em-dash).\n"
            "- Number them 1) 2) 3) only. No intro text.\n"
        )
        params = await self._resolve_params(conv, character)
        model = params["model"]
        from app.inference.ollama import OllamaProvider
        from app.inference.base import GenerationRequest

        base = ollama_base_url or params.get("base_url") or "http://127.0.0.1:11434"
        # resolve base from settings
        try:
            base = (await self.settings.get("ollama_base_url")) or base
        except Exception:
            pass
        provider = OllamaProvider(base_url=str(base).rstrip("/"))
        result = await provider.generate(
            GenerationRequest(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=350,
            )
        )
        text = (result.content or "").strip()
        options: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # strip 1) 2. - prefixes
            import re
            line = re.sub(r"^\s*\d+[\).\-:]\s*", "", line)
            line = re.sub(r"^\s*[-*]\s*", "", line)
            if line and len(line) > 1:
                options.append(line)
        # fallback templates
        if not options:
            char = character.name
            if last_ai:
                options = [
                    f'*I hesitate, then look at {char}.* "I... do not know what to say."',
                    '"Can we slow down for a second?"',
                    '*I nod carefully.* "Okay. I am listening."',
                ]
            else:
                options = [
                    f'*I glance over at {char}.* "Hey."',
                    '"Got a minute?"',
                    '*I clear my throat.* "So... about earlier."',
                ]
        return options[: max(1, min(5, count))]

    async def continue_reply(
        self,
        conversation_id: str,
        *,
        ollama_base_url: Optional[str] = None,
    ) -> list[Message]:
        """
        Continue the scene without a new user line — model picks up from the last assistant beat.
        """
        await ensure_columns(self.db)
        conv, character, persona = await self._load_context(conversation_id)
        history = await self.conversations.list_messages(conversation_id)
        if not any(m.role == "assistant" for m in history):
            # Fall back to normal generate path requires user message; seed a soft continue cue
            pass
        # Inject ephemeral continue instruction as system message (not stored) via history append
        from app.models.message import Message as Msg

        cue = Msg(
            id="continue-cue",
            conversation_id=conversation_id,
            role="user",
            speaker_type="user",
            speaker_name="System",
            raw_content=(
                "[Continue] Keep roleplaying as the character. Do not repeat the last lines. "
                "Add new beats only. Stay in first person markup: *actions.* and — \"dialogue.\""
            ),
            content_format="plain",
            is_selected_variant=True,
        )
        # Build same path as generate but with cue appended and skip requiring last real user
        history = list(history) + [cue]
        try:
            history_limit = int(await self.settings.get("history_limit") or "24")
        except ValueError:
            history_limit = 24
        if len(history) > history_limit:
            history = history[-history_limit:]

        params = await self._resolve_params(conv, character)
        if getattr(conv, "filter_level", None):
            character.filter_level = conv.filter_level  # type: ignore
        active_filter = getattr(character, "filter_level", None) or "mature"
        state = await self.char_state.ensure(conversation_id, character.id)
        # Apply per-chat live overrides (age, clothes, side ages)
        live = await self._live_overrides(conversation_id)
        live_block = self._live_overrides_prompt(live, character.name)

        world_block = ""
        if conv.world_id:
            world = await self.worlds.get(conv.world_id)
            if world:
                world_block = world.to_prompt_block()
        memory_block = await self.memories.retrieve_for_prompt(
            character_id=character.id,
            persona_id=persona.id,
            conversation_id=conversation_id,
            world_id=conv.world_id,
            query_text=history[-2].raw_content if len(history) >= 2 else "",
        )
        pins = await self.advanced.get_pins(conversation_id)
        mutes = await self.advanced.get_mutes(conversation_id)
        intensity = getattr(conv, "emotion_intensity", None) or 0.5
        triggers = getattr(character, "trigger_phrases", None) or []
        extra_parts = [
            p for p in (
                world_block,
                memory_block,
                f"ACTIVE CONTENT FILTER: {active_filter}.",
                self.advanced.intensity_prompt(float(intensity)),
                self.advanced.pins_prompt(pins),
                self.advanced.mutes_prompt(mutes),
                self.advanced.triggers_prompt(list(triggers) if isinstance(triggers, list) else [], ""),
                live_block,
                "FORMAT: Short beats only. *I action.* then — \"dialogue.\" Never prose paragraphs. Never use your own name as subject.",
            )
            if p
        ]
        extra = "\n\n".join(extra_parts) if extra_parts else None
        messages = compile_messages(
            character,
            persona,
            history,
            living_state=state,
            persona_display_name=conv.persona_display_name,
            extra_instructions=extra,
            max_tokens=params.get("max_tokens"),
        )
        result = await self._generate(params, messages, ollama_base_url=ollama_base_url)
        return await self._persist_turns(
            conversation_id,
            character,
            result.content,
            params,
            params.get("model") or "",
        )

    async def _live_overrides(self, conversation_id: str) -> dict:
        try:
            cursor = await self.db.execute(
                "SELECT pinned_lines, topic_mutes FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            # store live overrides in a dedicated column if present
            cursor = await self.db.execute(
                "PRAGMA table_info(conversations)"
            )
            cols = {r[1] for r in await cursor.fetchall()}
            if "live_overrides" not in cols:
                try:
                    await self.db.execute(
                        "ALTER TABLE conversations ADD COLUMN live_overrides TEXT"
                    )
                    await self.db.commit()
                except Exception:
                    return {}
            cursor = await self.db.execute(
                "SELECT live_overrides FROM conversations WHERE id = ?",
                (conversation_id,),
            )
            row = await cursor.fetchone()
            if not row or not row[0]:
                return {}
            import json
            data = json.loads(row[0])
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _live_overrides_prompt(self, live: dict, char_name: str) -> str:
        if not live:
            return ""
        lines = ["PER-CHAT TEMPORARY STATE (this chat only, not permanent card changes):"]
        if live.get("age") is not None:
            lines.append(f"- {char_name} current age in this chat: {live['age']}")
        if live.get("clothes"):
            lines.append(f"- {char_name} currently wearing: {live['clothes']}")
        sides = live.get("sides") or {}
        if isinstance(sides, dict):
            for name, info in sides.items():
                if not isinstance(info, dict):
                    continue
                bit = []
                if info.get("age") is not None:
                    bit.append(f"age {info['age']}")
                if info.get("clothes"):
                    bit.append(f"wearing {info['clothes']}")
                if bit:
                    lines.append(f"- Side character {name}: " + ", ".join(bit))
        return "\n".join(lines) if len(lines) > 1 else ""

    async def regenerate(
        self,
        conversation_id: str,
        message_id: str,
        *,
        ollama_base_url: Optional[str] = None,
    ) -> list[Message]:
        """
        Create a new variant for an assistant message (or its variant root).
        Previous variants are kept; the new one becomes selected.
        Prompt includes prior variant texts so the model avoids repeating them.
        Temperature is nudged up slightly for variety.
        """
        conv, character, persona = await self._load_context(conversation_id)
        target = await self.conversations.get_message(message_id)
        if target is None:
            raise ValueError("Message not found")
        if target.conversation_id != conversation_id:
            raise ValueError("Message does not belong to this conversation")
        if target.role != "assistant":
            raise ValueError("Only assistant messages can be regenerated")

        # Resolve variant family root
        root_id = target.parent_message_id or target.id
        variants = await self.conversations.list_variants(root_id)
        avoid_texts = [v.raw_content for v in variants if v.raw_content.strip()]
        next_index = max((v.variant_index for v in variants), default=0) + 1

        # History up to (but excluding) the original assistant message and later
        all_msgs = await self.conversations.list_messages(
            conversation_id, selected_only=False
        )
        # Use timeline before the root message was created
        history = [
            m
            for m in all_msgs
            if m.created_at and target.created_at and m.created_at < target.created_at
            and (m.is_selected_variant or m.role == "user")
        ]
        # Fallback: everything before this message id order
        if not history:
            history = []
            for m in all_msgs:
                if m.id == root_id or m.id == target.id:
                    break
                if m.role == "user" or m.is_selected_variant:
                    history.append(m)

        params = await self._resolve_params(conv, character, temperature_boost=0.15)
        if getattr(conv, "filter_level", None):
            character.filter_level = conv.filter_level  # type: ignore
        params["repetition_penalty"] = min(2.0, params["repetition_penalty"] + 0.1)
        state = await self.char_state.ensure(conversation_id, character.id)
        messages = compile_messages(
            character,
            persona,
            conv.persona_display_name,
            history,
            character_state=state,
            avoid_texts=avoid_texts,
            max_tokens=params.get("max_tokens"),
        )
        result = await self._call_model(params, messages, ollama_base_url)
        content = validate_and_fix_markup(result.content, character_name=character.name).fixed_text

        # Deselect old variants in the family
        await self.conversations.deselect_variants(root_id)

        return await self._persist_turns(
            conversation_id,
            character,
            content,
            params,
            result.model,
            parent_message_id=root_id,
            variant_index=next_index,
            is_selected_variant=True,
        )
