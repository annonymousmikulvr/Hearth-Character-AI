"""Infer side-character presence from chat text and keep soft roster facts."""

from __future__ import annotations

import re
from typing import Optional

# Common first names / capitalised tokens that look like people
_NAME = re.compile(
    r"\b([A-Z][a-z]{2,12})\b"
)

_STOP = {
    "The", "This", "That", "Then", "When", "What", "Where", "Who", "Why", "How",
    "And", "But", "You", "Your", "She", "He", "They", "His", "Her", "Their",
    "I", "My", "We", "Our", "It", "Its", "Not", "Yes", "No", "Ok", "Okay",
    "Later", "Time", "Skip", "Scene", "System", "User", "Char", "Character",
    "Honestly", "Really", "Maybe", "Just", "Even", "Still", "Only", "Also",
    "With", "From", "Into", "After", "Before", "About", "Because", "While",
}


def extract_candidate_names(
    texts: list[str],
    *,
    exclude: Optional[set[str]] = None,
) -> list[str]:
    exclude = {e.lower() for e in (exclude or set())}
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for m in _NAME.finditer(text):
            name = m.group(1)
            if name in _STOP:
                continue
            low = name.lower()
            if low in exclude or low in seen:
                continue
            # Prefer names that appear near people-ish verbs / pronouns context
            seen.add(low)
            found.append(name)
    return found[:12]


def gender_hint(name: str, context: str) -> str:
    """Rough gender cue from surrounding pronouns in context mentioning the name."""
    low = context.lower()
    n = name.lower()
    window = []
    for m in re.finditer(re.escape(n), low):
        start = max(0, m.start() - 80)
        end = min(len(low), m.end() + 80)
        window.append(low[start:end])
    blob = " ".join(window) if window else low
    she = len(re.findall(r"\b(she|her|hers|herself)\b", blob))
    he = len(re.findall(r"\b(he|him|his|himself)\b", blob))
    if she > he and she > 0:
        return "she/her"
    if he > she and he > 0:
        return "he/him"
    return "they/them"


def roster_prompt(
    names: list[str],
    context: str,
    *,
    primary_name: str,
) -> str:
    if not names:
        return ""
    lines = [
        "SIDE CHARACTERS IN / NEAR THIS SCENE (introduce or react naturally when relevant):"
    ]
    for n in names:
        if n.lower() == primary_name.lower():
            continue
        g = gender_hint(n, context)
        lines.append(
            f"- {n} ({g}). If they speak, use a separate beat or structured side turn; "
            f"do not speak as them in the primary character's voice."
        )
    lines.append(
        "When a side character should speak, prefer a clear line like: "
        f'*{names[0]} watches quietly.* — "..." as a side beat, or JSON side message if you use structured output.'
    )
    return "\n".join(lines)
