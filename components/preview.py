"""Escaped, text-labelled highlights; credential previews remain masked."""
from html import escape
from categories import CATEGORY_META, DEFAULT_META
from detector import resolve_overlaps
from recognizers.secrets import masked

def findings_preview(text, findings):
    parts, cursor = [], 0
    for finding in resolve_overlaps(findings):
        parts.append(escape(text[cursor:finding.start]))
        label = CATEGORY_META.get(finding.category, DEFAULT_META)['label']
        value = masked(finding.matched_text) if finding.category == 'SECRET' else finding.matched_text
        parts.append('<mark>⟦' + escape(label) + '⟧ ' + escape(value) + '</mark>')
        cursor = finding.end
    parts.append(escape(text[cursor:]))
    return '<div style="white-space:pre-wrap;overflow-wrap:anywhere" aria-label="Finding preview">' + ''.join(parts) + '</div>'
