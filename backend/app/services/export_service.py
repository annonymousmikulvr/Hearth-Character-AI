"""
Portable character (.char) and persona (.persona) ZIP packages.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from app.models.character import Character
from app.models.persona import Persona


def _character_dict(c: Character) -> dict[str, Any]:
    return {
        "format": "local-character-ai.character",
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "id": c.id,
        "name": c.name,
        "description": c.description,
        "system_prompt": c.system_prompt,
        "baseline_personality": c.baseline_personality,
        "scenario": c.scenario,
        "greeting": c.greeting,
        "example_dialogues": c.example_dialogues,
        "temperature": c.temperature,
        "top_p": c.top_p,
        "repetition_penalty": c.repetition_penalty,
        "context_window": c.context_window,
        "max_tokens": c.max_tokens,
        "model_name": c.model_name,
        "side_character_enabled": c.side_character_enabled,
        "side_character_instructions": c.side_character_instructions,
        "tags": c.tags,
        "version": c.version,
    }


def _persona_dict(p: Persona) -> dict[str, Any]:
    return {
        "format": "local-character-ai.persona",
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "id": p.id,
        "profile_name": p.profile_name,
        "chat_name": p.chat_name,
        "age": p.age,
        "pronouns": p.pronouns,
        "height": p.height,
        "build": p.build,
        "hair": p.hair,
        "eyes": p.eyes,
        "skin": p.skin,
        "clothing": p.clothing,
        "appearance_description": p.appearance_description,
        "traits": p.traits,
        "personality_description": p.personality_description,
        "likes": p.likes,
        "dislikes": p.dislikes,
        "habits": p.habits,
        "speaking_style": p.speaking_style,
        "biography": p.biography,
        "occupation": p.occupation,
        "location": p.location,
        "additional_facts": p.additional_facts,
        "how_they_act": p.how_they_act,
        "how_they_respond": p.how_they_respond,
        "custom_instructions": p.custom_instructions,
        "example_dialogues": p.example_dialogues,
        "tags": p.tags,
    }


def export_character_zip(character: Character) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        data = _character_dict(character)
        zf.writestr(
            "character.json",
            json.dumps(data, indent=2, ensure_ascii=False),
        )
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "type": "character",
                    "name": character.name,
                    "format_version": 1,
                    "files": ["character.json"],
                },
                indent=2,
            ),
        )
    return buf.getvalue()


def export_persona_zip(persona: Persona) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        data = _persona_dict(persona)
        zf.writestr(
            "persona.json",
            json.dumps(data, indent=2, ensure_ascii=False),
        )
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "type": "persona",
                    "name": persona.profile_name,
                    "format_version": 1,
                    "files": ["persona.json"],
                },
                indent=2,
            ),
        )
    return buf.getvalue()


def import_character_from_zip(data: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        names = zf.namelist()
        # Basic safety: reject path traversal
        for n in names:
            if n.startswith("/") or ".." in n:
                raise ValueError("Invalid package: unsafe path")
        if "character.json" not in names:
            raise ValueError("Invalid character package: missing character.json")
        raw = zf.read("character.json").decode("utf-8")
        obj = json.loads(raw)
        if not isinstance(obj, dict) or not obj.get("name"):
            raise ValueError("Invalid character.json")
        return obj


def import_persona_from_zip(data: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        names = zf.namelist()
        for n in names:
            if n.startswith("/") or ".." in n:
                raise ValueError("Invalid package: unsafe path")
        if "persona.json" not in names:
            raise ValueError("Invalid persona package: missing persona.json")
        raw = zf.read("persona.json").decode("utf-8")
        obj = json.loads(raw)
        if not isinstance(obj, dict) or not obj.get("profile_name"):
            raise ValueError("Invalid persona.json")
        return obj
