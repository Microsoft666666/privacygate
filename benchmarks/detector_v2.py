"""Local, rule-based detection. Findings are hints, never identity verification."""
from dataclasses import dataclass
import re
from ipaddress import IPv4Address
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    category: str
    start: int
    end: int
    matched_text: str
    reason: str
    confidence: str = "medium"
    origin: str = "automatic"


PRIORITY = {"MANUAL_IDENTIFIER": 8, "MANUAL_ADDRESS": 8, "MANUAL_CONFIDENTIAL": 8, "USER_PHRASE": 8, "PARTIAL_DETAIL": 7, "IPV4": 1, "PAYMENT_CARD": 4, "SSN": 3, "EMAIL": 2, "US_PHONE": 1}
EMAIL = re.compile(r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~@-])[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*\.[A-Za-z]{2,}(?![A-Za-z0-9_@-])")
PHONE = re.compile(r"(?<![0-9A-Za-z])(?:\+?1[ .-]?)?(?:\([2-9][0-9]{2}\)[ .-]?|[2-9][0-9]{2}[ .-]?)[2-9][0-9]{2}[ .-]?[0-9]{4}(?![0-9A-Za-z])")
SSN = re.compile(r"(?<![0-9])[0-9]{3}(?P<sep>[- ])[0-9]{2}(?P=sep)[0-9]{4}(?![0-9])")
NUMERIC_RUN = re.compile(r"(?<![0-9])[0-9](?:[ -]?[0-9]){12,}(?![0-9])")


def luhn_valid(value: str) -> bool:
    digits = value.replace(" ", "").replace("-", "")
    if not digits.isascii() or not digits.isdigit() or not 13 <= len(digits) <= 19:
        return False
    if len(set(digits)) == 1:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        number = int(digit)
        if index % 2:
            number *= 2
            number = number - 9 if number > 9 else number
        total += number
    return total % 10 == 0


def resolve_overlaps(findings: Iterable[Finding]) -> list[Finding]:
    """Prefer high-risk categories, then longer spans, then earliest position."""
    accepted: list[Finding] = []
    for finding in sorted(findings, key=lambda f: (-PRIORITY.get(f.category, 0), -(f.end-f.start), f.start, f.category)):
        if not any(finding.start < other.end and other.start < finding.end for other in accepted):
            accepted.append(finding)
    return sorted(accepted, key=lambda f: (f.start, f.end, f.category))


USER_CATEGORIES = {"MANUAL_IDENTIFIER", "MANUAL_ADDRESS", "MANUAL_CONFIDENTIAL", "USER_PHRASE"}
IPV4 = re.compile(r"(?<![0-9A-Za-z_.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9A-Za-z_]|\.[0-9])")
PARTIAL = re.compile(r"\[PARTIAL_[A-Z_]+_[0-9]+:[^\]\n]*\]")


@dataclass(frozen=True)
class SensitivePhrase:
    phrase: str
    category: str = "USER_PHRASE"

    def __post_init__(self) -> None:
        if not isinstance(self.phrase, str) or not self.phrase.strip() or self.category not in USER_CATEGORIES:
            raise ValueError("Enter a nonempty exact phrase and a supported sensitivity label.")


def mark_phrase(text: str, phrase: str, category: str) -> SensitivePhrase:
    rule = SensitivePhrase(phrase, category)
    if phrase not in text:
        raise ValueError("That exact phrase does not occur in the original message.")
    return rule


def detect(text: str, sensitive_phrases: tuple[SensitivePhrase, ...] = ()) -> list[Finding]:
    findings: list[Finding] = []
    runs = list(NUMERIC_RUN.finditer(text))
    patterns = [
        ("EMAIL", EMAIL, "Email-shaped contact information; not full RFC coverage.", "high"),
        ("US_PHONE", PHONE, "US phone-shaped number; unseparated digits can also be an ID.", "medium"),
        ("SSN", SSN, "SSN-like format; this does not confirm a real Social Security number.", "medium"),
    ]
    for category, pattern, reason, confidence in patterns:
        for match in pattern.finditer(text):
            if category in {"US_PHONE", "SSN"} and any(match.start() < run.end() and run.start() < match.end() for run in runs):
                continue
            findings.append(Finding(category, match.start(), match.end(), match.group(), reason, confidence))
    for match in runs:
        if luhn_valid(match.group()):
            findings.append(Finding("PAYMENT_CARD", match.start(), match.end(), match.group(), "13–19 digits pass Luhn; not proof of a genuine payment card.", "high"))
    for match in IPV4.finditer(text):
        try:
            IPv4Address(match.group())
        except ValueError:
            continue
        findings.append(Finding("IPV4", match.start(), match.end(), match.group(),
                                "Valid IPv4-shaped address; could also be a version number.", "format-based only"))
    for match in PARTIAL.finditer(text):
        findings.append(Finding("PARTIAL_DETAIL", match.start(), match.end(), match.group(),
                                "Partial masking retains characters. Review the remaining disclosure.", "format-based only"))
    for rule in sensitive_phrases:
        if not isinstance(rule, SensitivePhrase):
            raise ValueError("Invalid phrase configuration")
        start = text.find(rule.phrase)
        while start >= 0:
            findings.append(Finding(rule.category, start, start + len(rule.phrase), rule.phrase,
                                    "Exact phrase marked sensitive by you, not inferred by the detector.",
                                    "user-provided", "user-provided"))
            start = text.find(rule.phrase, start + 1)
    return resolve_overlaps(findings)
