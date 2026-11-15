"""CN resident ID shape and MOD 11-2 checksum, not identity verification."""
import re
from detector import Finding
PATTERN = re.compile(r'(?<![0-9A-Za-z])[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![0-9A-Za-z])')
WEIGHTS = (7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2)

def valid(value):
    return bool(PATTERN.fullmatch(value)) and '10X98765432'[sum(int(d)*w for d,w in zip(value[:17],WEIGHTS)) % 11] == value[-1].upper()

def find(text):
    return [Finding('NATIONAL_ID', m.start(), m.end(), m.group(), 'Matches a national ID format and checksum.', 'checksum-based') for m in PATTERN.finditer(text) if valid(m.group())]
