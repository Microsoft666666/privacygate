"""Conservative US street address shape; does not infer residence."""
import re
from detector import Finding
PATTERN = re.compile(r"\b\d{1,6}\s+(?:[A-Z][a-z0-9]*\.?\s+){1,4}(?:St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Dr|Drive|Ln|Lane|Way|Ct|Court|Pl|Place|Pkwy|Parkway|Cir|Circle|Ter|Terrace|Hwy|Highway)\b\.?(?:\s*(?:Apt|Unit|Suite|Ste|#)\s*[A-Za-z0-9-]+)?(?:,\s*[A-Z][A-Za-z .]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)?")

def find(text):
    return [Finding('STREET_ADDRESS',m.start(),m.end(),m.group(),'Looks like a US street address.','pattern-based') for m in PATTERN.finditer(text)]
