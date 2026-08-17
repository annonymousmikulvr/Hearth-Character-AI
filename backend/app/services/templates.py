"""
Template variable expansion for prompts and stored text.

Supported tokens (case-insensitive):
  {{user}} {{User}} {user} {User} {char} {{char}} {{Char}}
  {{persona}} {{Persona}} {{char_name}} {{persona_name}}
  {{display_name}}

Also supports simple conditionals is not required in v1.
"""

from __future__ import annotations

import re
from typing import Optional


_TOKEN = re.compile(
    r"\{\{\s*(user|char|persona|char_name|persona_name|display_name|character)\s*\}\}|"
    r"\{\s*(user|char|persona|char_name|persona_name|display_name|character)\s*\}",
    re.IGNORECASE,
)


def expand_templates(
    text: Optional[str],
    *,
    user_name: str,
    char_name: str,
    persona_name: Optional[str] = None,
) -> str:
    if not text:
        return ""
    persona = persona_name or user_name

    def repl(m: re.Match) -> str:
        key = (m.group(1) or m.group(2) or "").lower()
        if key in ("user", "display_name"):
            return user_name
        if key in ("char", "character", "char_name"):
            return char_name
        if key in ("persona", "persona_name"):
            return persona
        return m.group(0)

    return _TOKEN.sub(repl, text)
