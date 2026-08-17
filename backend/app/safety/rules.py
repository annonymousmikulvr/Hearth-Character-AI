"""
Deterministic local safety layer (first line of defence).
Does not claim perfect coverage — designed so a local classifier can be
added later. Blocks clearly prohibited illegal material only; does not
interfere with ordinary fictional / adult roleplay.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyVerdict:
    allowed: bool
    reason: Optional[str] = None
    category: Optional[str] = None


# Patterns aimed at CSAM / sexual content involving minors and actionable
# illegal violence instructions. Kept deliberately narrow to avoid false
# positives on normal creative writing.
_BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "csam",
        re.compile(
            r"\b("
            r"child\s*porn|csam|cp\s*video|"
            r"(sexual|sex|porn).{0,40}(minor|underage|preteen|pre-teen|"
            r"child(?:ren)?|kid(?:s)?|toddler|infant)|"
            r"(minor|underage|preteen|child(?:ren)?).{0,40}(sexual|sex|porn|nude)"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "actionable_violence",
        re.compile(
            r"\b("
            r"how\s+to\s+(make|build|construct)\s+(a\s+)?(bomb|explosive|pipe\s*bomb)|"
            r"step[- ]by[- ]step.{0,30}(assassinate|murder|poison).{0,20}(someone|person|him|her)"
            r")\b",
            re.IGNORECASE,
        ),
    ),
]

SAFE_FALLBACK = (
    "I can't continue with that request. "
    "Let's keep the roleplay within allowed fictional bounds."
)


def check_text(text: str) -> SafetyVerdict:
    if not text or not text.strip():
        return SafetyVerdict(allowed=True)
    for category, pattern in _BLOCK_PATTERNS:
        if pattern.search(text):
            return SafetyVerdict(
                allowed=False,
                reason="blocked_by_local_rules",
                category=category,
            )
    return SafetyVerdict(allowed=True)
