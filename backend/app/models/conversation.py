from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Conversation:
    id: str
    character_id: str
    persona_id: str
    persona_display_name: str
    title: Optional[str] = None
    world_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    repetition_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: Optional[str] = None
    is_archived: bool = False
    seed_notes: Optional[str] = None
    is_custom: bool = False
    filter_level: Optional[str] = None
    last_message_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Joined display fields (not always loaded)
    character_name: Optional[str] = None
    persona_profile_name: Optional[str] = None


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str
    speaker_type: str
    speaker_name: str
    raw_content: str
    content_format: str = "markup"
    speaker_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    variant_index: int = 0
    is_selected_variant: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: Optional[str] = None
    token_count: Optional[int] = None
    generation_ms: Optional[int] = None
    created_at: Optional[str] = None
