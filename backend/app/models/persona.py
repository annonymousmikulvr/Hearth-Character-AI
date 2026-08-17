from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Persona:
    id: str
    profile_name: str
    chat_name: str
    age: Optional[int] = None
    pronouns: Optional[str] = None

    height: Optional[str] = None
    build: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    appearance_description: Optional[str] = None

    traits: list[str] = field(default_factory=list)
    personality_description: Optional[str] = None
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    habits: list[str] = field(default_factory=list)
    speaking_style: Optional[str] = None

    biography: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    additional_facts: list[str] = field(default_factory=list)

    how_they_act: Optional[str] = None
    how_they_respond: Optional[str] = None
    custom_instructions: Optional[str] = None

    example_dialogues: list[dict[str, str]] = field(default_factory=list)
    family_tree: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    modes: list[dict] = field(default_factory=list)
    active_mode: Optional[str] = None

    avatar_path: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_prompt_block(self, display_name: Optional[str] = None) -> str:
        name = display_name or self.chat_name or self.profile_name
        lines = [
            "=== USER PERSONA (the human you are talking to) ===",
            f"Name in chat: {name}",
        ]
        if self.profile_name and self.profile_name != name:
            lines.append(f"Full name: {self.profile_name}")
        if self.age is not None:
            lines.append(f"Age: {self.age}")
        if self.pronouns:
            lines.append(f"Pronouns: {self.pronouns}")

        if self.appearance_description:
            lines.append(f"Appearance: {self.appearance_description}")
        else:
            parts = [p for p in [self.height, self.build, self.hair, self.eyes, self.skin, self.clothing] if p]
            if parts:
                lines.append("Appearance: " + ", ".join(parts))

        if self.personality_description:
            lines.append(f"Personality: {self.personality_description}")
        if self.traits:
            lines.append("Traits: " + ", ".join(self.traits))
        if self.speaking_style:
            lines.append(f"Speaking style: {self.speaking_style}")

        if self.likes:
            lines.append("Likes: " + ", ".join(self.likes))
        if self.dislikes:
            lines.append("Dislikes: " + ", ".join(self.dislikes))
        if self.habits:
            lines.append("Habits: " + ", ".join(self.habits))

        if self.biography:
            lines.append(f"Biography: {self.biography}")
        if self.occupation:
            lines.append(f"Occupation: {self.occupation}")
        if self.location:
            lines.append(f"Location: {self.location}")

        if self.additional_facts:
            lines.append("IMPORTANT facts about this person (remember and use when relevant):")
            for fact in self.additional_facts:
                fact = (fact or "").strip()
                if fact:
                    lines.append(f"  - {fact}")
        if self.family_tree:
            lines.append("Family tree:")
            for m in self.family_tree:
                if not isinstance(m, dict):
                    continue
                name = m.get("name") or "?"
                rel = m.get("relation") or "relative"
                estranged = " (estranged)" if m.get("estranged") else ""
                notes = m.get("notes") or ""
                gen = m.get("generation")
                gen_s = f" [gen {gen}]" if gen is not None else ""
                lines.append(f"  - {name}: {rel}{estranged}{gen_s}" + (f" — {notes}" if notes else ""))
        if self.relationships:
            lines.append("Other relationships:")
            for r in self.relationships:
                if isinstance(r, dict):
                    lines.append(f"  - {r.get('name', '?')}: {r.get('relation', '')} — {r.get('notes', '')}")

        if self.how_they_act:
            lines.append(f"How they act: {self.how_they_act}")
        if self.how_they_respond:
            lines.append(f"How they respond: {self.how_they_respond}")
        if self.custom_instructions:
            lines.append(f"Custom instructions: {self.custom_instructions}")

        lines.append(
            "When the user asks about their own life, family, preferences, or facts listed above, "
            "answer using this persona data. Do not invent conflicting details."
        )
        lines.append("=== END USER PERSONA ===")
        return "\n".join(lines)
