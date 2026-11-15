"""International phones validated locally by libphonenumber metadata."""
import re
import phonenumbers
from detector import Finding

CN = re.compile(r'(?<!\d)1[3-9]\d(?:[ -]?\d{4}){2}(?!\d)')

def find(text):
    findings = []
    for match in phonenumbers.PhoneNumberMatcher(text, None):
        if match.number.country_code != 1 and text[match.start:match.end].startswith('+') and phonenumbers.is_valid_number(match.number):
            findings.append(Finding('INTL_PHONE', match.start, match.end, text[match.start:match.end], 'Valid international phone format.', 'format-based only'))
    for m in CN.finditer(text):
        number = phonenumbers.parse(m.group(), 'CN')
        if phonenumbers.is_valid_number(number):
            findings.append(Finding('INTL_PHONE', m.start(), m.end(), m.group(), 'Valid Chinese mobile phone format.', 'format-based only'))
    return findings
