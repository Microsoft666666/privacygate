"""Context-qualified IDs and dates. No identity or account verification."""
import re
from datetime import datetime
from detector import Finding, luhn_valid

def aba_valid(value):
    if len(value) != 9 or not value.isascii() or not value.isdigit() or len(set(value)) == 1:
        return False
    return sum(int(d)*w for d,w in zip(value,(3,7,1)*3)) % 10 == 0

def iban_valid(value):
    value = value.replace(' ', '').upper()
    if not 15 <= len(value) <= 34 or not re.fullmatch(r'[A-Z]{2}[0-9]{2}[A-Z0-9]+',value):
        return False
    digits = ''.join(str(ord(c)-55) if c.isalpha() else c for c in value[4:]+value[:4])
    return int(digits) % 97 == 1

MONTH = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
DATE = re.compile(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})|'+MONTH+r' \d{1,2}, \d{4}|\d{1,2} '+MONTH+r' \d{4})\b', re.I)

def valid_date(value):
    for fmt in ('%Y-%m-%d','%m/%d/%Y','%m/%d/%y','%B %d, %Y','%d %B %Y'):
        try:
            datetime.strptime(value,fmt)
            return True
        except ValueError:
            pass
    return False

def nearby(text, start, end, keyword, distance, after=True):
    left = text[max(0,start-distance):start]
    right = '' if after else text[end:end+distance]
    return bool(re.search(keyword,left,re.I) or re.search(keyword,right,re.I))

def find(text):
    found=[]
    def add(cat,m,reason):
        found.append(Finding(cat,m.start(),m.end(),m.group(),reason,'context-based'))
    for m in re.finditer(r'(?<![\dA-Za-z])\d{6,17}(?![\dA-Za-z])',text):
        v=m.group()
        if len(v)==9 and nearby(text,m.start(),m.end(),r'\b(?:ssn|social security(?: number| no\.?)?)\b',32):
            if v[:3] not in ('000','666') and not v.startswith('9') and v[3:5]!='00' and v[5:]!='0000':
                add('SSN',m,'Nine-digit ID after a Social Security label.')
        if len(v)==9 and nearby(text,m.start(),m.end(),r'\b(?:routing|aba|rtn)\b',40,False) and aba_valid(v):
            add('BANK_ACCOUNT',m,'Routing-shaped number passes ABA checksum.')
        if nearby(text,m.start(),m.end(),r'\b(?:account|acct|a/c|checking|savings)\b',40,False) and not luhn_valid(v):
            add('BANK_ACCOUNT',m,'Number near a bank-account label.')
    for m in re.finditer(r'\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b',text):
        if iban_valid(m.group()):
            add('BANK_ACCOUNT',m,'IBAN-shaped account passes mod-97 checksum.')
    for m in DATE.finditer(text):
        if nearby(text,m.start(),m.end(),r'\b(?:born|birthday|dob|date of birth|b\.)',30) and valid_date(m.group()):
            add('DATE_OF_BIRTH',m,'Date follows a birth-related label.')
    return found
