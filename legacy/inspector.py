"""Pure, escaped read-only previews. Never use raw user strings as HTML."""
from html import escape
import re
from detector import Finding, resolve_overlaps
from legacy.risk_cards import LABELS

ACTION_LABELS = {"BLOCK": "Cannot send", "WARN": "Review required", "ALLOW": "Permitted by this rule"}


def original_preview(text: str, findings: list[Finding], rules: dict[str, str], reveal: bool = False) -> str:
    pieces, cursor = [], 0
    for finding in resolve_overlaps(findings):
        if not 0 <= finding.start < finding.end <= len(text) or text[finding.start:finding.end] != finding.matched_text:
            raise ValueError("Preview findings do not match the message")
        action = rules.get(finding.category, "BLOCK")
        if action not in ACTION_LABELS:
            action = "BLOCK"
        pieces.append(escape(text[cursor:finding.start], quote=True))
        value = finding.matched_text if reveal else "••••"
        label = f"{LABELS.get(finding.category, 'Sensitive detail')} · {ACTION_LABELS[action]}"
        pieces.append(f'<mark class="{action.lower()}">{escape(value, quote=True)} <span class="pg-annotation">[{escape(label, quote=True)}]</span></mark>')
        cursor = finding.end
    pieces.append(escape(text[cursor:], quote=True))
    return '<div class="pg-preview">' + ''.join(pieces) + '</div>'


def outgoing_preview(text: str) -> str:
    pieces, cursor = [], 0
    for match in re.finditer(r"\[(?:[A-Z_]+_[0-9]+)\]", text):
        pieces.append(escape(text[cursor:match.start()], quote=True))
        pieces.append('<mark class="replacement">' + escape(match.group(), quote=True) + '</mark>')
        cursor = match.end()
    pieces.append(escape(text[cursor:], quote=True))
    return '<div class="pg-preview">' + ''.join(pieces) + '</div>'


def occurrence_count(text: str, phrase: str) -> int:
    if not phrase or not phrase.strip():
        return 0
    return sum(1 for _ in re.finditer(f"(?={re.escape(phrase)})", text))
