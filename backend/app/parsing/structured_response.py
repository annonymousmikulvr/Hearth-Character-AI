"""
Parse model output into primary + side speaker turns.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpeakerTurn:
    speaker_type: str  # primary | side
    character: str
    text: str


_FULL_JSON = re.compile(
    r"^\s*\{[\s\S]*\"messages\"\s*:\s*\[[\s\S]*\]\s*\}\s*$",
    re.MULTILINE,
)
_FENCED = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
_JSON_LINE = re.compile(
    r"^\s*[\{\}\[\],]*\s*$|"
    r'^\s*"(messages|speaker_type|character|text)"\s*:|'
    r'^\s*\{?\s*"speaker_type"|'
    r'^\s*"character"\s*:|'
    r'^\s*"text"\s*:',
    re.IGNORECASE,
)


def _try_parse_messages(candidate: str, primary_name: str) -> Optional[list]:
    try:
        data = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    messages = data.get("messages")
    if not isinstance(messages, list) or len(messages) == 0:
        return None
    turns: list[SpeakerTurn] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        speaker_type = str(item.get("speaker_type") or "primary").lower().strip()
        if speaker_type not in ("primary", "side"):
            speaker_type = "primary" if "primary" in speaker_type else "side"
        name = str(item.get("character") or "").strip()
        if not name or name.lower() in ("<unknown>", "unknown", "null", "none"):
            name = primary_name
        body = item.get("text")
        if body is None:
            continue
        body = str(body).strip()
        if not body or (body.startswith("{") and "speaker_type" in body):
            continue
        turns.append(SpeakerTurn(speaker_type=speaker_type, character=name, text=body))
    return turns if turns else None


def _strip_json_garbage(text: str) -> str:
    lines_out = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            lines_out.append(line)
            continue
        if _JSON_LINE.match(stripped):
            continue
        if re.match(
            r'^"?\s*(messages|speaker_type|character|text)\s*"?\s*:',
            stripped,
            re.I,
        ):
            continue
        symbol_ratio = sum(1 for c in stripped if c in '{}[]",:') / max(len(stripped), 1)
        if symbol_ratio > 0.4:
            continue
        lines_out.append(line)
    result = "\n".join(lines_out)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    return result.strip()



def _first_person_verb(action: str) -> str:
    action = action.strip()
    # smiles -> smile, waves -> wave, nods -> nod (simple heuristic)
    action = re.sub(
        r"\b(smiles|laughs|waves|nods|watches|looks|says|asks|shrugs|grins|stares|approaches|chuckles|giggles|frowns|glances|reaches|touches|hugs|points|whispers)\b",
        lambda m: {
            "smiles": "smile",
            "laughs": "laugh",
            "waves": "wave",
            "nods": "nod",
            "watches": "watch",
            "looks": "look",
            "says": "say",
            "asks": "ask",
            "shrugs": "shrug",
            "grins": "grin",
            "stares": "stare",
            "approaches": "approach",
            "chuckles": "chuckle",
            "giggles": "giggle",
            "frowns": "frown",
            "glances": "glance",
            "reaches": "reach",
            "touches": "touch",
            "hugs": "hug",
            "points": "point",
            "whispers": "whisper",
        }.get(m.group(1).lower(), m.group(1)),
        action,
        count=1,
        flags=re.I,
    )
    return action

def _normalize_name(name: str) -> str:
    return re.sub(r"[^A-Za-z]", "", name or "").lower()



def split_side_beats_from_prose(
    text: str,
    primary_name: str,
    known_names: Optional[list[str]] = None,
) -> list[SpeakerTurn]:
    """
    Split a reply so other people's actions/speech become side turns.

    Detects:
      Name: ...
      *Name does something*
      Name smiles / waves / says ...
      inline: "as Donivan smiles at you" (lifts the side clause when possible)
    """
    if not text or not text.strip():
        return [SpeakerTurn("primary", primary_name, "")]

    primary_norm = _normalize_name(primary_name)
    names: list[str] = []
    for n in known_names or []:
        if n and _normalize_name(n) != primary_norm:
            names.append(n)
    for m in re.finditer(r"\b([A-Z][a-z]{2,14})\b", text):
        n = m.group(1)
        if n.lower() in {
            "the", "this", "that", "then", "when", "what", "and", "but", "you",
            "she", "his", "her", "they", "with", "from", "into", "after", "before",
            "like", "exactly", "someone", "anyone", "line", "school", "week",
            "good", "okay", "well", "just", "even", "still", "only", "also",
            "here", "there", "maybe", "really", "honestly", "anyway",
        }:
            continue
        if _normalize_name(n) == primary_norm:
            continue
        if not any(_normalize_name(x) == _normalize_name(n) for x in names):
            names.append(n)
    names = sorted(names, key=len, reverse=True)
    if not names:
        return [SpeakerTurn("primary", primary_name, text.strip())]

    name_alt = "|".join(re.escape(n) for n in names)
    verbs = (
        r"smiles|smiled|laughs|laughed|waves|waved|nods|nodded|watches|watched|"
        r"looks|looked|says|said|asks|asked|shrugs|shrugged|grins|grinned|"
        r"stares|stared|approaches|approached|sits|sat|stands|stood|leans|leaned|"
        r"chuckles|chuckled|giggles|giggled|frowns|frowned|glances|glanced|"
        r"reaches|reached|touches|touched|hugs|hugged|points|pointed|"
        r"interrupts|interrupted|clears|cleared|whispers|whispered"
    )

    labeled = re.compile(rf"^\s*({name_alt})\s*:\s*(.*)$", re.I)
    starred = re.compile(rf"^\s*\*\s*({name_alt})\s+([^*]+)\*\s*$", re.I)
    narrated = re.compile(
        rf"^\s*({name_alt})\s+((?:{verbs})(?:\b|[^\n]*))$",
        re.I,
    )
    # Primary line that embeds side action: "... as Name verbs ..."
    embedded = re.compile(
        rf"^(?P<pre>.*?\b(?:as|while|and)\s+)(?P<name>{name_alt})\s+(?P<rest>(?:{verbs})\b.*)$",
        re.I,
    )

    primary_chunks: list[str] = []
    side_map: dict[str, list[str]] = {}
    current_side: Optional[str] = None

    def canon(name: str) -> str:
        return next(
            (n for n in names if _normalize_name(n) == _normalize_name(name)),
            name,
        )

    def add_side(name: str, body: str) -> None:
        nonlocal current_side
        c = canon(name)
        current_side = c
        body = body.strip()
        if not body:
            return
        # Prefer first-person-ish action for side readability
        if body.startswith("*") and not re.match(r"^\*\s*I\b", body, re.I):
            inner = body.strip("*").strip()
            if not re.match(r"^I\b", inner, re.I):
                body = f"*I {inner}*" if not inner.lower().startswith(("i ", "i'")) else f"*{inner}*"
        side_map.setdefault(c, []).append(body)

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if current_side is None:
                primary_chunks.append(line)
            continue

        m = labeled.match(stripped)
        if m:
            add_side(m.group(1), m.group(2) or stripped)
            continue

        m = starred.match(stripped)
        if m:
            add_side(m.group(1), f"*I {_first_person_verb(m.group(2))}*")
            continue

        m = narrated.match(stripped)
        if m:
            add_side(m.group(1), f"*I {_first_person_verb(m.group(2))}*")
            continue

        m = embedded.match(stripped)
        if m:
            pre = m.group("pre").strip()
            pre = re.sub(r"\b(?:as|while|and)\s*$", "", pre, flags=re.I).strip()
            pre = pre.rstrip(",;").strip().rstrip("*").strip()
            if pre:
                current_side = None
                if not (pre.startswith("*") or pre.startswith("—") or pre.startswith('"')):
                    pre = f"*{pre}*"
                elif pre.startswith("*") and not pre.endswith("*"):
                    pre = pre + "*"
                primary_chunks.append(pre)
            rest = m.group("rest").strip().rstrip("*").strip()
            # dialogue after side action on same line
            dlg = ""
            rest = m.group("rest").strip().rstrip("*").strip()
            dlg = ""
            dm = re.search(r'(?:\u2014|\u2013|-)\s*["\'](.+?)["\']\s*$', rest)
            if not dm:
                dm = re.search(r'["\'](.+?)["\']\s*$', rest)
            if dm:
                dlg = '\u2014 "' + dm.group(1) + '"'
                rest = rest[: dm.start()].strip().rstrip(",.;")
            add_side(m.group("name"), f"*I {_first_person_verb(rest)}*")
            if dlg:
                add_side(m.group("name"), dlg)
            continue

        # Continue side block for dialogue/actions without a name
        if current_side and (
            stripped.startswith("—")
            or stripped.startswith("–")
            or stripped.startswith("--")
            or stripped.startswith('"')
            or stripped.startswith("*")
        ):
            # Hand back to primary if strong first-person self-focus without side name
            if re.search(r"\bI\b", stripped) and not re.search(
                rf"\b{re.escape(current_side)}\b", stripped, re.I
            ):
                # side dialogue can still use I; keep on side if last side turn was dialogue-ish
                if stripped.startswith("—") or stripped.startswith('"'):
                    add_side(current_side, stripped)
                else:
                    current_side = None
                    primary_chunks.append(line)
            else:
                add_side(current_side, stripped)
            continue

        current_side = None
        primary_chunks.append(line)

    primary_text = "\n".join(primary_chunks).strip()
    # Clean empty action shells
    primary_text = re.sub(r"^\*\s*\*$", "", primary_text, flags=re.M).strip()

    turns: list[SpeakerTurn] = []
    if primary_text:
        turns.append(SpeakerTurn("primary", primary_name, primary_text))
    for name, chunks in side_map.items():
        body = "\n".join(chunks).strip()
        if body:
            turns.append(SpeakerTurn("side", name, body))
    if not turns:
        turns.append(SpeakerTurn("primary", primary_name, text.strip()))
    return turns


def parse_structured_response(
    raw: str,
    *,
    primary_name: str,
    known_side_names: Optional[list[str]] = None,
) -> list[SpeakerTurn]:
    text = (raw or "").strip()
    if not text:
        return [SpeakerTurn(speaker_type="primary", character=primary_name, text="")]

    # 1) Full JSON
    if _FULL_JSON.match(text):
        turns = _try_parse_messages(text, primary_name)
        if turns:
            return turns

    # 2) Fenced JSON
    for m in _FENCED.finditer(text):
        turns = _try_parse_messages(m.group(1).strip(), primary_name)
        if turns:
            return turns

    # 3) Dominant embedded JSON
    brace_match = re.search(
        r"\{[\s\S]*\"messages\"\s*:\s*\[[\s\S]*\][\s\S]*\}", text
    )
    if brace_match:
        candidate = brace_match.group(0)
        if len(candidate) >= len(text) * 0.55:
            turns = _try_parse_messages(candidate, primary_name)
            if turns:
                return turns

    recovered = _strip_json_garbage(text)
    if not recovered:
        recovered = "\n".join(
            ln for ln in text.splitlines() if not _JSON_LINE.match(ln)
        ).strip()
        recovered = _strip_json_garbage(recovered) or recovered
    if not recovered:
        recovered = f"*I pause, searching for the right words.*"

    return split_side_beats_from_prose(
        recovered, primary_name, known_names=known_side_names
    )
