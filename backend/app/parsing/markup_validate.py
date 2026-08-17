"""Validate/repair markup and force first-person voice before display."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarkupReport:
    ok: bool
    fixed_text: str
    issues: list[str]


_SPELL_FIXES = [
    (re.compile(r"\bteh\b", re.I), "the"),
    (re.compile(r"\brecieve\b", re.I), "receive"),
    (re.compile(r"\bdefinately\b", re.I), "definitely"),
    (re.compile(r"\boccured\b", re.I), "occurred"),
    (re.compile(r"\buntill\b", re.I), "until"),
    (re.compile(r"\s{3,}"), "  "),
    (re.compile(r" +([,.!?;:])"), r"\1"),
]


def polish_prose(text: str) -> str:
    out = text
    for pat, repl in _SPELL_FIXES:
        out = pat.sub(repl, out)
    return out



def force_first_person(text: str, char_name: Optional[str]) -> tuple[str, list[str]]:
    """Rewrite common third-person self-narration into first person."""
    if not text:
        return text, []
    issues: list[str] = []
    out = text
    name = (char_name or "").strip()

    def fix_i_verb(body: str) -> str:
        body = body.strip()
        body = re.sub(r"\bShe\b", "I", body)
        body = re.sub(r"\bshe\b", "I", body)
        body = re.sub(r"\bHer\b", "My", body)
        body = re.sub(r"\bher\b", "my", body)
        body = re.sub(r"\bherself\b", "myself", body)
        if not re.match(r"^(I|i|my|My)\b", body):
            body = f"I {body}"
        # I scoffs / I raises / I moves -> I scoff / I raise / I move
        def de_s(m: re.Match) -> str:
            verb = m.group(1)
            if verb.lower() in {"is", "was", "has", "does", "says"}:
                return m.group(0)
            return f"I {verb}"
        body = re.sub(r"^I\s+([A-Za-z]+)s\b", de_s, body)
        return body

    if name and len(name) >= 2:
        pat_action = re.compile(
            rf"\*\s*{re.escape(name)}\s+([^*\n]+)\*",
            re.IGNORECASE,
        )

        def repl_action(m: re.Match) -> str:
            issues.append("third_person_action")
            return f"*{fix_i_verb(m.group(1))}*"

        out = pat_action.sub(repl_action, out)

        pat_line = re.compile(
            rf"(^|\n)\s*{re.escape(name)}\s+([a-z][^\n]*)",
            re.IGNORECASE,
        )

        def repl_line(m: re.Match) -> str:
            issues.append("third_person_line")
            return f"{m.group(1)}{fix_i_verb(m.group(2))}"

        out = pat_line.sub(repl_line, out)

        out2 = re.sub(
            rf"\b{re.escape(name)}'s\b",
            "my",
            out,
            flags=re.IGNORECASE,
        )
        if out2 != out:
            issues.append("third_person_possessive")
            out = out2

    # *moves her hand...* without name — still third-ish; promote her/she inside actions
    def repl_bare_action(m: re.Match) -> str:
        inner = m.group(1)
        if re.search(r"\b(she|her|herself)\b", inner, re.I) and not re.search(
            r"\b(I|my|myself)\b", inner, re.I
        ):
            issues.append("third_person_pronoun_action")
            return f"*{fix_i_verb(inner)}*"
        return m.group(0)

    out = re.sub(r"\*([^*\n]+)\*", repl_bare_action, out)
    return out, issues


def humanize_narration(text: str) -> str:
    """Nudge common stiff narration toward first-person action beats."""
    if not text:
        return text
    out = text
    out = re.sub(r'\bMy expression turns to be more guarded\b', 'I grow more guarded', out, flags=re.I)
    out = re.sub(
        r'\bLeaning against the edge of my desk,\s*an expression softens\b',
        'I lean against the edge of my desk as my expression softens',
        out,
        flags=re.I,
    )
    out = re.sub(r'\bfolding arms tighter for emphasis\b', 'I fold my arms tighter for emphasis', out, flags=re.I)
    out = re.sub(r'\bfidgets slightly with sleeve cuffs\b', 'I fidget slightly with my sleeve cuffs', out, flags=re.I)
    out = re.sub(r'\bI Glance\b', 'I glance', out)
    out = re.sub(r'\s*->\s*' + chr(34) + r'[^' + chr(34) + r']*' + chr(34), '', out)
    out = re.sub(chr(34) + r'{2,}', chr(34), out)
    out = re.sub(r'\(I ([^)]+)\)', r'*I \1*', out)
    out = re.sub(r'\s*' + chr(8212) + r'a slight pause\s*' + chr(8212), '\n*I pause.*\n', out, flags=re.I)
    return out


def format_to_beats(text: str) -> str:
    """
    Prefer short *action* / — "dialogue" beats over dense prose paragraphs.
    Heuristic only — does not invent content.
    """
    if not text or not text.strip():
        return text
    # Already mostly beat-shaped
    if text.count("*") >= 2 or "— " in text or "– " in text:
        # Still split if one giant paragraph with an em-dash buried mid-sentence
        pass
    lines_out: list[str] = []
    for para in re.split(r"\n+", text.strip()):
        para = para.strip()
        if not para:
            continue
        # If line is already *...* or starts with em-dash dialogue, keep
        if para.startswith("*") or para.startswith("—") or para.startswith("–") or para.startswith("--"):
            lines_out.append(para)
            continue
        # Split dialogue quotes out of prose
        # Pattern: prose... "dialogue"...
        parts = re.split(r'([""][^""]+[""])', para)
        buf_prose = []
        for part in parts:
            if not part:
                continue
            if len(part) >= 2 and part[0] in "\"“" and part[-1] in "\"”":
                if buf_prose:
                    prose = " ".join(buf_prose).strip()
                    if prose:
                        # turn prose into a short action if long
                        if not prose.startswith("*"):
                            # drop leading "The " heavy narration slightly
                            lines_out.append(f"*{prose}*")
                        else:
                            lines_out.append(prose)
                    buf_prose = []
                inner = part[1:-1].strip()
                lines_out.append(f'— "{inner}"')
            else:
                buf_prose.append(part.strip())
        if buf_prose:
            prose = " ".join(buf_prose).strip()
            if prose:
                if not prose.startswith("*"):
                    lines_out.append(f"*{prose}*")
                else:
                    lines_out.append(prose)
    cleaned = []
    for ln in lines_out:
        ln = ln.strip()
        if not ln or ln in {"—", "–", "--", "*—*", "*–*"}:
            continue
        # remove trailing orphan em-dash inside actions
        ln = re.sub(r"\s*[—–]\s*\*$", "*", ln)
        ln = re.sub(r"\*\s*[—–]\s*", "*", ln)
        cleaned.append(ln)
    return "\n".join(cleaned) if cleaned else text


def validate_and_fix_markup(
    text: str,
    *,
    character_name: Optional[str] = None,
) -> MarkupReport:
    if not text:
        return MarkupReport(ok=True, fixed_text="", issues=[])

    issues: list[str] = []
    fixed = text

    if fixed.count("***") % 2 != 0:
        issues.append("unclosed_important_action")
        if fixed.rstrip().endswith("***"):
            fixed = fixed.rstrip()[:-3].rstrip()
        else:
            fixed = fixed + "***"

    lines = fixed.split("\n")
    new_lines = []
    for line in lines:
        if re.match(r"^\*\s+", line.strip()):
            new_lines.append(line)
            continue
        masked = line.replace("**", "\0\0")
        if masked.count("*") % 2 != 0:
            issues.append("unclosed_action_or_emphasis")
            if not line.rstrip().endswith("*"):
                line = line.rstrip() + "*"
        new_lines.append(line.replace("\0\0", "**"))
    fixed = "\n".join(new_lines)

    fixed_lines = []
    for line in fixed.split("\n"):
        t = line.strip()
        if re.match(r"^(?:—|–|--)\s*[\"“]", t):
            q = t.count('"') + t.count("“") + t.count("”")
            if q == 1:
                issues.append("unclosed_dialogue_quote")
                line = line.rstrip() + '"'
        fixed_lines.append(line)
    fixed = "\n".join(fixed_lines)

    if fixed.count("**") % 2 != 0:
        issues.append("unclosed_emphasis")
        fixed = fixed + "**"

    fixed, tp_issues = force_first_person(fixed, character_name)
    issues.extend(tp_issues)

    fixed = polish_prose(fixed)
    issues.append("prose_polish")
    fixed = humanize_narration(fixed)
    fixed = format_to_beats(fixed)
    issues.append("beat_format")
    ok = not any(i not in ("prose_polish",) and not i.startswith("third_person") for i in issues)
    return MarkupReport(ok=ok, fixed_text=fixed, issues=issues)
