"""Local credential patterns. Never log values or exception payloads."""
import re
from detector import Finding
PATTERNS = [
    (r'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}',0),
    (r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b',0),
    (r'\bgh[pousr]_[A-Za-z0-9]{36,}\b',0),
    (r'\bgithub_pat_[A-Za-z0-9_]{22,}',0),
    (r'\bAIza[0-9A-Za-z_-]{35}\b',0),
    (r'\bxox[abprs]-[A-Za-z0-9-]{10,}',0),
    (r'\b(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,}',0),
    (r'\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',0),
    (r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----',0),
    (r'(?i)\b(?:password|passwd|pwd|passcode)\s*(?:is|=|:|：)\s*(\S{4,})',1),
    (r'(?:密码|口令)\s*(?:是|为|:|：|=)\s*([^\s，。！？]{4,})',1),
    (r'\b[a-z][a-z0-9+.-]*://[^\s:/@]+:([^\s@/]+)@',1),
    (r'''(?i)\b(?:api[_-]?key|secret|token|access[_-]?key)\s*[:=]\s*['"]?([A-Za-z0-9_\-./+=]{16,})''',1),
]
COMPILED = [(re.compile(pattern),group) for pattern,group in PATTERNS]
REASON = 'Looks like a password or access key. Anyone who sees it may get into the account.'

def find(text):
    found=[]
    for pattern,group in COMPILED:
        for m in pattern.finditer(text):
            value=m.group(group)
            if 'password|passwd' in pattern.pattern:
                value=value.rstrip('.,;!?)"\'')
            if value:
                found.append(Finding('SECRET',m.start(group),m.start(group)+len(value),value,REASON,'pattern-based'))
    return found

def masked(value):
    return value[:2]+'…'+value[-2:] if len(value)>4 else '••••'
