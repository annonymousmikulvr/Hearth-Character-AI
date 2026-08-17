from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ExampleDialogue(BaseModel):
    user: str
    persona: str


class PersonaBase(BaseModel):
    profile_name: str = Field(..., min_length=1, max_length=120)
    chat_name: str = Field(..., min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=200)
    pronouns: Optional[str] = Field(None, max_length=40)

    height: Optional[str] = Field(None, max_length=40)
    build: Optional[str] = Field(None, max_length=80)
    hair: Optional[str] = Field(None, max_length=120)
    eyes: Optional[str] = Field(None, max_length=80)
    skin: Optional[str] = Field(None, max_length=80)
    clothing: Optional[str] = Field(None, max_length=200)
    appearance_description: Optional[str] = Field(None, max_length=2000)

    traits: list[str] = Field(default_factory=list)
    personality_description: Optional[str] = Field(None, max_length=4000)
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    habits: list[str] = Field(default_factory=list)
    speaking_style: Optional[str] = Field(None, max_length=1000)

    biography: Optional[str] = Field(None, max_length=8000)
    occupation: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    additional_facts: list[str] = Field(default_factory=list)
    family_tree: list[dict[str, Any]] = Field(default_factory=list)
    modes: list[dict[str, Any]] = Field(default_factory=list)
    active_mode: Optional[str] = None
    relationships: list[dict[str, Any]] = Field(default_factory=list)

    how_they_act: Optional[str] = Field(None, max_length=2000)
    how_they_respond: Optional[str] = Field(None, max_length=2000)
    custom_instructions: Optional[str] = Field(None, max_length=4000)

    example_dialogues: list[ExampleDialogue] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    @field_validator("traits", "likes", "dislikes", "habits", "additional_facts", "tags", mode="before")
    @classmethod
    def ensure_list(cls, v: object) -> list:
        if v is None:
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return list(v)  # type: ignore


class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(BaseModel):
    """All fields optional for PATCH-style updates."""

    profile_name: Optional[str] = Field(None, min_length=1, max_length=120)
    chat_name: Optional[str] = Field(None, min_length=1, max_length=80)
    age: Optional[int] = Field(None, ge=0, le=200)
    pronouns: Optional[str] = Field(None, max_length=40)

    height: Optional[str] = Field(None, max_length=40)
    build: Optional[str] = Field(None, max_length=80)
    hair: Optional[str] = Field(None, max_length=120)
    eyes: Optional[str] = Field(None, max_length=80)
    skin: Optional[str] = Field(None, max_length=80)
    clothing: Optional[str] = Field(None, max_length=200)
    appearance_description: Optional[str] = Field(None, max_length=2000)

    traits: Optional[list[str]] = None
    personality_description: Optional[str] = Field(None, max_length=4000)
    likes: Optional[list[str]] = None
    dislikes: Optional[list[str]] = None
    habits: Optional[list[str]] = None
    speaking_style: Optional[str] = Field(None, max_length=1000)

    biography: Optional[str] = Field(None, max_length=8000)
    occupation: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    additional_facts: Optional[list[str]] = None
    family_tree: Optional[list[dict[str, Any]]] = None
    modes: Optional[list[dict[str, Any]]] = None
    active_mode: Optional[str] = None
    relationships: Optional[list[dict[str, Any]]] = None

    how_they_act: Optional[str] = Field(None, max_length=2000)
    how_they_respond: Optional[str] = Field(None, max_length=2000)
    custom_instructions: Optional[str] = Field(None, max_length=4000)

    example_dialogues: Optional[list[ExampleDialogue]] = None
    tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None


class PersonaOut(PersonaBase):
    id: str
    avatar_path: Optional[str] = None
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class PersonaListItem(BaseModel):
    id: str
    profile_name: str
    chat_name: str
    avatar_path: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_archived: bool = False
    updated_at: Optional[str] = None
