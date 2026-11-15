"""Exact-span corrective suggestions; never rewrite unrelated prose."""
from dataclasses import dataclass
import re
from categories import CATEGORY_META, DEFAULT_META
from detector import detect, resolve_overlaps

@dataclass(frozen=True)
class Suggestion:
    finding: object
    replacement: str


def suggest_fixes(text, rules=(), mapping=None, *, ner=None, style="Placeholder", ignore_values=()):
    mapping = dict(mapping or {})
    findings = [f for f in detect(text, rules, ner=ner) if f.matched_text not in ignore_values]
    for f in findings:
        key = (f.category, f.matched_text)
        if key not in mapping:
            label = CATEGORY_META.get(f.category, DEFAULT_META)['placeholder']
            n = 1
            while f'[{label}_{n}]' in mapping.values() or f'[{label}_{n}]' in text:
                n += 1
            placeholder = f'[{label}_{n}]'
            candidate = replacement_for(f, style, n, placeholder)
            # Ambiguous inverses cannot be restored safely. Fall back to a unique token.
            mapping[key] = placeholder if candidate in mapping.values() or candidate in text else candidate
    return [Suggestion(f, mapping[(f.category, f.matched_text)]) for f in findings], mapping


def replacement_for(finding, style, number, placeholder):
    category, value = finding.category, finding.matched_text
    if category in {'SSN','PAYMENT_CARD','NATIONAL_ID','SECRET','BANK_ACCOUNT'}:
        return placeholder
    if style == 'Plain description':
        simple = {'PERSON':'[name]', 'SCHOOL':'my school', 'EMAIL':'my email',
                  'US_PHONE':'my phone number', 'INTL_PHONE':'my phone number'}
        if category == 'STREET_ADDRESS':
            city = re.search(r',\s*([A-Z][A-Za-z .]+,\s*[A-Z]{2})\b', value)
            return city.group(1) if city else 'my home address'
        if category == 'DATE_OF_BIRTH':
            year = re.search(r'\b(?:19|20)\d{2}\b', value)
            return year.group() if year else placeholder
        return simple.get(category, placeholder)
    if style == 'Fictional look-alike':
        names = ['Jordan Lee','Sam Rivera','Taylor Kim','Alex Morgan','Casey Park']
        if category == 'PERSON':
            return names[number-1] if number <= len(names) else placeholder
        return {'SCHOOL':'Lakeview High School', 'EMAIL':f'student{number}@example.com',
                'US_PHONE':f'(555) 010-00{number:02d}', 'INTL_PHONE':f'(555) 010-00{number:02d}',
                'STREET_ADDRESS':'100 Example Street'}.get(category,placeholder)
    return placeholder


def apply_fixes(text, suggestions):
    findings = [s.finding for s in suggestions]
    for f in findings:
        if text[f.start:f.end] != f.matched_text:
            raise ValueError('Stale suggestion')
    replacements = {(s.finding.category, s.finding.matched_text): s.replacement for s in suggestions}
    for f in reversed(resolve_overlaps(findings)):
        text = text[:f.start] + replacements[(f.category, f.matched_text)] + text[f.end:]
    return text


def restore_reply(text, mapping):
    """Single-pass exact replacements; never recursively restore inserted originals."""
    import re
    inverse = {replacement: original for (_, original), replacement in mapping.items()}
    if not inverse:
        return text
    pattern = re.compile('|'.join(re.escape(value) for value in sorted(inverse, key=len, reverse=True)))
    return pattern.sub(lambda match: inverse[match.group()], text)
