from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ExampleDialogueTurn(BaseModel):
    role: str
    content: str


class FamilyMember(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    relation: str = Field(..., max_length=120)  # mother, cousin, estranged uncle…
    generation: Optional[int] = Field(None, ge=-10, le=10)  # 0 = self gen, -1 parent, +1 child
    status: Optional[str] = Field(None, max_length=80)  # alive, deceased, missing
    estranged: bool = False
    notes: Optional[str] = Field(None, max_length=2000)


class RelationshipEntry(BaseModel):
    name: str = Field(..., max_length=120)
    relation: str = Field("", max_length=120)
    notes: Optional[str] = Field(None, max_length=2000)


def _listish(v: object) -> list:
    if v is None:
        return []
    if isinstance(v, str):
        return [s.strip() for s in v.split(",") if s.strip()]
    return list(v)  # type: ignore


class CharacterBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=4000)
    filter_level: str = Field("mature", pattern="^(strict|moderate|mature|unfiltered)$")

    system_prompt: Optional[str] = Field(None, max_length=16000)
    baseline_personality: Optional[str] = Field(None, max_length=8000)
    scenario: Optional[str] = Field(None, max_length=8000)
    greeting: Optional[str] = Field(None, max_length=8000)
    example_dialogues: list[ExampleDialogueTurn] = Field(default_factory=list)

    age: Optional[str] = Field(None, max_length=40)
    pronouns: Optional[str] = Field(None, max_length=40)
    height: Optional[str] = None
    build: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    appearance_description: Optional[str] = Field(None, max_length=4000)
    traits: list[str] = Field(default_factory=list)
    likes: list[str] = Field(default_factory=list)
    dislikes: list[str] = Field(default_factory=list)
    habits: list[str] = Field(default_factory=list)
    speaking_style: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    biography: Optional[str] = Field(None, max_length=8000)
    additional_facts: list[str] = Field(default_factory=list)
    how_they_act: Optional[str] = None
    how_they_respond: Optional[str] = None
    custom_instructions: Optional[str] = None
    family_tree: list[FamilyMember] = Field(default_factory=list)
    relationships: list[RelationshipEntry] = Field(default_factory=list)
    goals: Optional[str] = None
    fears: Optional[str] = None
    secrets: Optional[str] = None

    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    repetition_penalty: Optional[float] = Field(None, ge=0.5, le=2.0)
    context_window: Optional[int] = Field(None, ge=512, le=131072)
    max_tokens: Optional[int] = Field(None, ge=16, le=8192)
    model_profile_id: Optional[str] = None
    model_name: Optional[str] = Field(None, max_length=200)

    side_character_enabled: bool = True
    side_character_instructions: Optional[str] = Field(None, max_length=4000)
    image_gen_enabled: bool = False
    image_gen_style: Optional[str] = Field(None, max_length=2000)
    side_roster: list[dict] = Field(default_factory=list)
    mood_board: list[str] = Field(default_factory=list)
    trigger_phrases: list[dict] = Field(default_factory=list)

    tags: list[str] = Field(default_factory=list)

    @field_validator("tags", "traits", "likes", "dislikes", "habits", "additional_facts", mode="before")
    @classmethod
    def ensure_list(cls, v: object) -> list:
        return _listish(v)


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=4000)
    filter_level: Optional[str] = Field(None, pattern="^(strict|moderate|mature|unfiltered)$")
    system_prompt: Optional[str] = Field(None, max_length=16000)
    baseline_personality: Optional[str] = Field(None, max_length=8000)
    scenario: Optional[str] = Field(None, max_length=8000)
    greeting: Optional[str] = Field(None, max_length=8000)
    example_dialogues: Optional[list[ExampleDialogueTurn]] = None
    age: Optional[str] = None
    pronouns: Optional[str] = None
    height: Optional[str] = None
    build: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    appearance_description: Optional[str] = None
    traits: Optional[list[str]] = None
    likes: Optional[list[str]] = None
    dislikes: Optional[list[str]] = None
    habits: Optional[list[str]] = None
    speaking_style: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    biography: Optional[str] = None
    additional_facts: Optional[list[str]] = None
    how_they_act: Optional[str] = None
    how_they_respond: Optional[str] = None
    custom_instructions: Optional[str] = None
    family_tree: Optional[list[FamilyMember]] = None
    relationships: Optional[list[RelationshipEntry]] = None
    goals: Optional[str] = None
    fears: Optional[str] = None
    secrets: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    repetition_penalty: Optional[float] = Field(None, ge=0.5, le=2.0)
    context_window: Optional[int] = Field(None, ge=512, le=131072)
    max_tokens: Optional[int] = Field(None, ge=16, le=8192)
    model_profile_id: Optional[str] = None
    model_name: Optional[str] = None
    side_character_enabled: Optional[bool] = None
    side_character_instructions: Optional[str] = None
    image_gen_enabled: Optional[bool] = None
    image_gen_style: Optional[str] = None
    side_roster: Optional[list[dict]] = None
    mood_board: Optional[list[str]] = None
    trigger_phrases: Optional[list[dict]] = None
    tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None
    avatar_path: Optional[str] = None


class CharacterOut(CharacterBase):
    id: str
    avatar_path: Optional[str] = None
    version: int = 1
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    model_config = {"from_attributes": True}


class CharacterListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    avatar_path: Optional[str] = None
    filter_level: str = "mature"
    tags: list[str] = Field(default_factory=list)
    is_archived: bool = False
    updated_at: Optional[str] = None
    chat_count: int = 0
