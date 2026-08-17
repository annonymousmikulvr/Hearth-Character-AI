from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Character:
    id: str
    name: str
    description: Optional[str] = None
    avatar_path: Optional[str] = None
    filter_level: str = "mature"  # strict | moderate | mature | unfiltered

    system_prompt: Optional[str] = None
    baseline_personality: Optional[str] = None
    scenario: Optional[str] = None
    greeting: Optional[str] = None
    example_dialogues: list[dict[str, str]] = field(default_factory=list)

    # Deep profile (parity with persona)
    age: Optional[str] = None
    pronouns: Optional[str] = None
    height: Optional[str] = None
    build: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    skin: Optional[str] = None
    clothing: Optional[str] = None
    appearance_description: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)
    habits: list[str] = field(default_factory=list)
    speaking_style: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    biography: Optional[str] = None
    additional_facts: list[str] = field(default_factory=list)
    how_they_act: Optional[str] = None
    how_they_respond: Optional[str] = None
    custom_instructions: Optional[str] = None
    family_tree: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)
    goals: Optional[str] = None
    fears: Optional[str] = None
    secrets: Optional[str] = None

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    repetition_penalty: Optional[float] = None
    context_window: Optional[int] = None
    max_tokens: Optional[int] = None
    model_profile_id: Optional[str] = None
    model_name: Optional[str] = None

    side_character_enabled: bool = True
    side_character_instructions: Optional[str] = None
    image_gen_enabled: bool = False
    image_gen_style: Optional[str] = None
    side_roster: list = field(default_factory=list)
    mood_board: list = field(default_factory=list)
    trigger_phrases: list = field(default_factory=list)

    tags: list[str] = field(default_factory=list)
    version: int = 1
    is_archived: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_deep_prompt_block(self) -> str:
        lines = [f"=== CHARACTER PROFILE: {self.name} ==="]
        if self.age:
            lines.append(f"Age: {self.age}")
        if self.pronouns:
            lines.append(f"Pronouns: {self.pronouns}")
        if self.appearance_description:
            lines.append(f"Appearance: {self.appearance_description}")
        else:
            parts = [p for p in [self.height, self.build, self.hair, self.eyes, self.skin, self.clothing] if p]
            if parts:
                lines.append("Appearance: " + ", ".join(parts))
        if self.baseline_personality:
            lines.append(f"Personality: {self.baseline_personality}")
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
        if self.occupation:
            lines.append(f"Occupation: {self.occupation}")
        if self.location:
            lines.append(f"Location: {self.location}")
        if self.biography:
            lines.append(f"Biography: {self.biography}")
        if self.goals:
            lines.append(f"Goals: {self.goals}")
        if self.fears:
            lines.append(f"Fears: {self.fears}")
        if self.secrets:
            lines.append(f"Secrets (know but do not volunteer unless relevant): {self.secrets}")
        if self.additional_facts:
            lines.append("Important facts:")
            for f in self.additional_facts:
                if f and str(f).strip():
                    lines.append(f"  - {f}")
        if self.family_tree:
            lines.append("Family tree:")
            for m in self.family_tree:
                if not isinstance(m, dict):
                    continue
                name = m.get("name") or "?"
                rel = m.get("relation") or "relative"
                status = m.get("status") or ""
                notes = m.get("notes") or ""
                estranged = " (estranged)" if m.get("estranged") else ""
                gen = m.get("generation")
                gen_s = f" [gen {gen}]" if gen is not None else ""
                lines.append(f"  - {name}: {rel}{estranged}{gen_s}" + (f" — {notes}" if notes else "") + (f" [{status}]" if status else ""))
        if self.relationships:
            lines.append("Other relationships:")
            for r in self.relationships:
                if isinstance(r, dict):
                    lines.append(f"  - {r.get('name', '?')}: {r.get('relation', '')} — {r.get('notes', '')}")
                else:
                    lines.append(f"  - {r}")
        if self.how_they_act:
            lines.append(f"How they act: {self.how_they_act}")
        if self.how_they_respond:
            lines.append(f"How they respond: {self.how_they_respond}")
        if self.custom_instructions:
            lines.append(f"Custom instructions: {self.custom_instructions}")
        lines.append("=== END CHARACTER PROFILE ===")
        return "\n".join(lines)

    def filter_prompt_block(self) -> str:
        level = (self.filter_level or "mature").lower()
        guides = {
            "strict": (
                "CONTENT FILTER: strict. Keep language clean. No sexual content, "
                "graphic violence, or strong profanity. Fade to black on sensitive topics."
            ),
            "moderate": (
                "CONTENT FILTER: moderate. Mild language ok. Avoid explicit sexual detail "
                "and extreme gore. Romantic tension allowed."
            ),
            "mature": (
                "CONTENT FILTER: mature. Adult themes, violence, and romance allowed as "
                "fitting the character. Still avoid illegal sexual content involving minors."
            ),
            "unfiltered": (
                "CONTENT FILTER: unfiltered for fictional adult roleplay. Still forbid any "
                "sexual content involving minors (17 or under) and real-world criminal how-to."
            ),
        }
        return guides.get(level, guides["mature"])
