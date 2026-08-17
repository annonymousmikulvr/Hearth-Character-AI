from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    character_id: str
    persona_id: str
    persona_display_name: Optional[str] = Field(
        None,
        description="Override display name for this chat. Defaults to persona.chat_name.",
        max_length=80,
    )
    title: Optional[str] = Field(None, max_length=200)
    world_id: Optional[str] = None
    # Optional generation overrides for this conversation
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    repetition_penalty: Optional[float] = Field(None, ge=0.5, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=16, le=8192)
    model_name: Optional[str] = Field(None, max_length=200)
    seed_notes: Optional[str] = Field(
        None,
        max_length=8000,
        description="Optional custom backstory/seed injected as system context for this chat.",
    )
    is_custom: bool = False
    # Optional pre-seeded messages for custom chats: [{role, content}, ...]
    seed_messages: Optional[list[dict]] = None


class ConversationUpdate(BaseModel):
    filter_level: Optional[str] = Field(None, pattern='^(strict|moderate|mature|unfiltered)$')
    persona_id: Optional[str] = None
    persona_display_name: Optional[str] = Field(None, max_length=80)
    model_name: Optional[str] = Field(None, max_length=200)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=16, le=8192)
    title: Optional[str] = Field(None, max_length=200)
    persona_display_name: Optional[str] = Field(None, max_length=80)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    repetition_penalty: Optional[float] = Field(None, ge=0.5, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=16, le=8192)
    model_name: Optional[str] = Field(None, max_length=200)
    is_archived: Optional[bool] = None


class ConversationOut(BaseModel):
    filter_level: Optional[str] = None
    seed_notes: Optional[str] = None
    is_custom: bool = False
    id: str
    title: Optional[str] = None
    character_id: str
    persona_id: str
    persona_display_name: str
    world_id: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    repetition_penalty: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: Optional[str] = None
    is_archived: bool = False
    last_message_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    character_name: Optional[str] = None
    persona_profile_name: Optional[str] = None


class ConversationListItem(BaseModel):
    id: str
    title: Optional[str] = None
    character_id: str
    character_name: Optional[str] = None
    persona_id: str
    persona_display_name: str
    persona_profile_name: Optional[str] = None
    is_archived: bool = False
    last_message_at: Optional[str] = None
    updated_at: Optional[str] = None


class MessageCreate(BaseModel):
    """User-authored message (or system injection)."""

    role: str = Field("user", pattern="^(user|system)$")
    raw_content: str = Field(..., min_length=1, max_length=32000)
    content_format: str = Field("markup", pattern="^(markup|plain)$")


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    speaker_type: str
    speaker_id: Optional[str] = None
    speaker_name: str
    raw_content: str
    content_format: str = "markup"
    parent_message_id: Optional[str] = None
    variant_index: int = 0
    is_selected_variant: bool = True
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model_name: Optional[str] = None
    token_count: Optional[int] = None
    generation_ms: Optional[int] = None
    created_at: Optional[str] = None
