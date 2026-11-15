"""Offset-based selective redaction; no persistent original-value mapping."""
from dataclasses import dataclass
from detector import Finding, resolve_overlaps


@dataclass(frozen=True)
class RedactionResult:
    text: str
    replacements: int


def redact(text: str, findings: list[Finding], selected_indices: list[int] | None = None, mode: str = "Replace") -> RedactionResult:
    if mode not in {"Replace", "Mask", "Remove"}:
        raise ValueError("Unknown redaction mode.")
    for finding in findings:
        if not 0 <= finding.start < finding.end <= len(text) or text[finding.start:finding.end] != finding.matched_text:
            raise ValueError("Findings do not match this message. Scan again.")
    selected = set(range(len(findings)) if selected_indices is None else selected_indices)
    if any(i < 0 or i >= len(findings) for i in selected):
        raise ValueError("Invalid selected finding index.")
    counters: dict[str, int] = {}
    placeholders: dict[tuple[str, str], str] = {}
    # Assign across all findings first so toggling selections never renumbers values.
    for finding in sorted(findings, key=lambda f: (f.start, f.end, f.category)):
        key = (finding.category, finding.matched_text)
        if key not in placeholders:
            counters[finding.category] = counters.get(finding.category, 0) + 1
            label = "PHONE" if finding.category == "US_PHONE" else finding.category
            placeholders[key] = f"[{label}_{counters[finding.category]}]"
    chosen = resolve_overlaps(findings[i] for i in selected)
    result = text
    for finding in reversed(chosen):
        placeholder = placeholders[(finding.category, finding.matched_text)]
        replacement = placeholder
        if mode == "Remove":
            replacement = ""
        elif mode == "Mask":
            # Explicit marker keeps a partially disclosed value visible to final policy.
            value = finding.matched_text
            edge = lambda char: char if char.isalnum() else "?"
            preview = edge(value[0]) + "•••" + edge(value[-1]) if len(value) > 2 else "•••"
            replacement = f"[PARTIAL_{placeholder[1:-1]}: {preview}]"
        result = result[:finding.start] + replacement + result[finding.end:]
    return RedactionResult(result, len(chosen))
