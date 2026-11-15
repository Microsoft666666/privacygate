"""Exact-span corrective suggestions; never rewrite unrelated prose."""
from dataclasses import dataclass
from detector import detect, resolve_overlaps

@dataclass(frozen=True)
class Suggestion:
    finding: object
    replacement: str


def suggest_fixes(text, rules=(), mapping=None):
    mapping = dict(mapping or {})
    findings = detect(text, rules)
    for f in findings:
        key = (f.category, f.matched_text)
        if key not in mapping:
            label = 'PHONE' if f.category == 'US_PHONE' else f.category
            n = 1
            while f'[{label}_{n}]' in mapping.values() or f'[{label}_{n}]' in text:
                n += 1
            mapping[key] = f'[{label}_{n}]'
    return [Suggestion(f, mapping[(f.category, f.matched_text)]) for f in findings], mapping


def apply_fixes(text, suggestions):
    findings = [s.finding for s in suggestions]
    for f in findings:
        if text[f.start:f.end] != f.matched_text:
            raise ValueError('Stale suggestion')
    replacements = {(s.finding.category, s.finding.matched_text): s.replacement for s in suggestions}
    for f in reversed(resolve_overlaps(findings)):
        text = text[:f.start] + replacements[(f.category, f.matched_text)] + text[f.end:]
    return text
