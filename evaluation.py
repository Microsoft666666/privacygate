"""Exact-span evaluation against hand-authored synthetic annotations."""
from collections import Counter
from dataclasses import asdict, dataclass
import json
from typing import Callable
from detector import Finding, SensitivePhrase, detect

Span = tuple[str, int, int]


@dataclass(frozen=True)
class Case:
    name: str
    text: str
    expected: tuple[Span, ...]
    sensitive_phrases: tuple[SensitivePhrase, ...] = ()


def annotated(name: str, *parts: str | tuple[str, str], sensitive_phrases: tuple[SensitivePhrase, ...] = ()) -> Case:
    """Annotated fragments define ground truth independently of detector output."""
    text = ""
    spans = []
    for part in parts:
        if isinstance(part, tuple):
            category, value = part
            spans.append((category, len(text), len(text) + len(value)))
            text += value
        else:
            text += part
    return Case(name, text, tuple(spans), sensitive_phrases)


DATASET = [
    annotated("empty", ""),
    annotated("ordinary prose", "The garden helps our community."),
    annotated("year", "Graduating in 2026."),
    annotated("price", "Cost: $19.99 or $123.45."),
    annotated("date", "Meeting on 2026-11-15."),
    annotated("short ID", "Ticket 12345678."),
    annotated("ambiguous ten-digit ID", "Fictional inventory ID: 9495550199."),
    annotated("long invalid ID", "Reference 12345678901234567890."),
    annotated("invalid checksum", "Card 4111 1111 1111 1112."),
    annotated("zero run", "0000000000000000"),
    annotated("version", "Version 1.2.3.4"),
    annotated("plain email", ("EMAIL", "alex@example.com")),
    annotated("email punctuation", "Write (", ("EMAIL", "alex@example.com"), ")."),
    annotated("email tag", ("EMAIL", "alex+garden@example.org")),
    annotated("email subdomain", ("EMAIL", "alex@school.example.com")),
    annotated("email repeated", ("EMAIL", "alex@example.com"), " / ", ("EMAIL", "alex@example.com")),
    annotated("Unicode nearby", "你好 ", ("EMAIL", "alex@example.com"), " — welcome"),
    annotated("missing domain", "alex@"),
    annotated("missing suffix", "alex@example"),
    annotated("dashed phone", ("US_PHONE", "949-555-0134")),
    annotated("parenthesized phone", ("US_PHONE", "(949) 555-0134")),
    annotated("compact phone", ("US_PHONE", "9495550134")),
    annotated("country phone", ("US_PHONE", "+1 949 555 0134")),
    annotated("dotted phone", ("US_PHONE", "949.555.0134")),
    annotated("repeated phone", ("US_PHONE", "949-555-0134"), "; ", ("US_PHONE", "949-555-0134")),
    annotated("short phone", "949-555-013"),
    annotated("SSN shaped", "Fictional format: ", ("SSN", "000-12-3456")),
    annotated("SSN spaced", ("SSN", "000 12 3456")),
    annotated("SSN inconsistent", "000-12 3456"),
    annotated("card compact", ("PAYMENT_CARD", "4111111111111111")),
    annotated("card spaced", ("PAYMENT_CARD", "4111 1111 1111 1111")),
    annotated("card dashed", ("PAYMENT_CARD", "4111-1111-1111-1111")),
    annotated("second test card", ("PAYMENT_CARD", "5555 5555 5555 4444")),
    annotated("mixed multiline", "Email: ", ("EMAIL", "alex@example.com"), "\nPhone: ", ("US_PHONE", "949-555-0134")),
    annotated("mixed card SSN", ("PAYMENT_CARD", "4111111111111111"), "; ", ("SSN", "000-12-3456")),
    # Known misses deliberately prevent a misleading perfect synthetic score.
    annotated("nonbreaking phone spaces unsupported", ("US_PHONE", "+1 (949)\u00a0555\u00a00134")),
    annotated("quoted email unsupported", ("EMAIL", '"alex garden"@example.com')),
]


@dataclass(frozen=True)
class Metrics:
    tp: int
    fp: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if self.tp + self.fp else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if self.tp + self.fn else 0.0

    @property
    def f1(self) -> float:
        return 2 * self.tp / (2 * self.tp + self.fp + self.fn) if 2 * self.tp + self.fp + self.fn else 0.0

    def report(self) -> dict:
        return {**asdict(self), "precision": self.precision, "recall": self.recall, "f1": self.f1}


def score(predicted: list[Span], expected: list[Span]) -> Metrics:
    predictions, truth = Counter(predicted), Counter(expected)
    tp = sum((predictions & truth).values())
    return Metrics(tp, sum(predictions.values()) - tp, sum(truth.values()) - tp)


def evaluate(cases: list[Case] | None = None, detector: Callable = detect) -> dict:
    cases = DATASET if cases is None else cases
    rows, errors = [], []
    totals = [0, 0, 0]
    per_category: dict[str, list[int]] = {}
    for case in cases:
        findings = detector(case.text, case.sensitive_phrases) if case.sensitive_phrases else detector(case.text)
        predicted = [(f.category, f.start, f.end) for f in findings]
        expected = list(case.expected)
        metrics = score(predicted, expected)
        totals = [a + b for a, b in zip(totals, (metrics.tp, metrics.fp, metrics.fn))]
        for category in sorted({s[0] for s in predicted + expected}):
            measured = score([s for s in predicted if s[0] == category], [s for s in expected if s[0] == category])
            old = per_category.setdefault(category, [0, 0, 0])
            per_category[category] = [a + b for a, b in zip(old, (measured.tp, measured.fp, measured.fn))]
        for kind, spans in (("Missed", Counter(expected) - Counter(predicted)),
                            ("Incorrectly flagged", Counter(predicted) - Counter(expected))):
            for (category, start, end), count in spans.items():
                errors.append({"case": case.name, "error": kind, "category": category,
                               "start": start, "end": end, "count": count, "synthetic_text": case.text})
        rows.append({"case": case.name, **metrics.report(), "result": "PASS" if metrics.fp == metrics.fn == 0 else "FAIL"})
    return {"messages": len(cases), **Metrics(*totals).report(), "cases": rows,
            "per_category": {category: Metrics(*counts).report() for category, counts in sorted(per_category.items())},
            "errors": errors}


# Separate challenge set: hand-written strings/annotations, never derived from detect().
# Baseline DATASET above stays frozen, including its original category assumptions.
ADVERSARIAL = [
    annotated("angle email", "<", ("EMAIL", "garden@example.org"), ">"),
    annotated("bracket email", "[", ("EMAIL", "a+b@example.com"), "]"),
    annotated("uppercase email", ("EMAIL", "ALEX@EXAMPLE.COM")),
    annotated("email apostrophe", ("EMAIL", "o'fiction@example.org")),
    annotated("email unicode adjacency", "你好", ("EMAIL", "alex@example.com"), "界"),
    annotated("email repeated newlines", ("EMAIL", "a@example.com"), "\n", ("EMAIL", "a@example.com")),
    annotated("email malformed double dots", "alex..chen@example.com"),
    annotated("email trailing punctuation", ("EMAIL", "a@example.com"), "?!"),
    annotated("email quoted local part", ("EMAIL", '"fiction garden"@example.org')),
    annotated("email international domain", ("EMAIL", "alex@例子.测试")),
    annotated("phone country compact", ("US_PHONE", "+19495550134")),
    annotated("phone country parens", "Call ", ("US_PHONE", "+1 (949) 555-0134"), "."),
    annotated("phone Unicode adjacent", "你好", ("US_PHONE", "949-555-0134"), "界"),
    annotated("phone tab separators", ("US_PHONE", "949\t555\t0134")),
    annotated("phone NBSP separators", ("US_PHONE", "949\u00a0555\u00a00134")),
    annotated("phone extension", ("US_PHONE", "949-555-0134"), " ext. 204"),
    annotated("phone invalid area", "149-555-0134"),
    annotated("phone ID collision", "Inventory ID: 9495550188"),
    annotated("phone two space-separated", ("US_PHONE", "9495550134"), " ", ("US_PHONE", "9495550135")),
    annotated("phone repetition punctuation", ("US_PHONE", "(949) 555-0134"), " | ", ("US_PHONE", "(949) 555-0134")),
    annotated("card within parentheses", "(", ("PAYMENT_CARD", "4111-1111-1111-1111"), ")"),
    annotated("card 13 digit test", ("PAYMENT_CARD", "4222222222222")),
    annotated("card invalid length 12", "411111111111"),
    annotated("card invalid checksum long", "5555555555554445"),
    annotated("card excessive length", "41111111111111111111"),
    annotated("card tabs unsupported", ("PAYMENT_CARD", "4111\t1111\t1111\t1111")),
    annotated("card and phone punctuation", ("PAYMENT_CARD", "4111111111111111"), "; ", ("US_PHONE", "949-555-0134")),
    annotated("card Unicode adjacent", "界", ("PAYMENT_CARD", "4111111111111111"), "界"),
    annotated("SSN fictional zeros", ("SSN", "000-00-0000")),
    annotated("SSN spaced fiction", "ID: ", ("SSN", "000 99 0000")),
    annotated("SSN NBSP unsupported", ("SSN", "000\u00a012\u00a03456")),
    annotated("SSN short", "000-12-345"),
    annotated("SSN repeated", ("SSN", "000-12-3456"), " / ", ("SSN", "000-12-3456")),
    annotated("IP documentation net", "Host: ", ("IPV4", "192.0.2.15")),
    annotated("IP octet boundary", ("IPV4", "255.255.255.255")),
    annotated("IP zero boundary", ("IPV4", "0.0.0.0")),
    annotated("IP invalid octet", "256.1.2.3"),
    annotated("IP leading zero invalid", "192.000.2.1"),
    annotated("IP five components", "192.0.2.1.8"),
    annotated("IP sentence punctuation", "Host ", ("IPV4", "198.51.100.9"), "."),
    annotated("IP version collision", "Software version 2.3.4.5"),
    annotated("IP and email", ("EMAIL", "alex@example.com"), " at ", ("IPV4", "203.0.113.8")),
    annotated("year and room", "In 2026, meet in room 204 at 3:15."),
    annotated("prices and date", "$123.45 on 2026-11-15; discount 20%."),
    annotated("mixed Unicode multiline", "你好\n", ("EMAIL", "a@example.org"), "\n", ("US_PHONE", "949-555-0134")),
    annotated("confidential phrase repeat", ("USER_PHRASE", "Project Falcon"), " / ", ("USER_PHRASE", "Project Falcon"), sensitive_phrases=(SensitivePhrase("Project Falcon"),)),
    annotated("confidential literal punctuation", ("USER_PHRASE", "key.*+"), " remains private", sensitive_phrases=(SensitivePhrase("key.*+"),)),
    annotated("confidential absent negative", "Project Sparrow", sensitive_phrases=(SensitivePhrase("Project Falcon"),)),
    annotated("manual identifier", ("MANUAL_IDENTIFIER", "Alex Chen"), " volunteers", sensitive_phrases=(SensitivePhrase("Alex Chen", "MANUAL_IDENTIFIER"),)),
    annotated("manual address", "Address: ", ("MANUAL_ADDRESS", "123 Example Street"), sensitive_phrases=(SensitivePhrase("123 Example Street", "MANUAL_ADDRESS"),)),
    annotated("manual confidential", ("MANUAL_CONFIDENTIAL", "Student QX-204"), sensitive_phrases=(SensitivePhrase("Student QX-204", "MANUAL_CONFIDENTIAL"),)),
    annotated("partial marker", ("PARTIAL_DETAIL", "[PARTIAL_EMAIL_1: a•••m]")),
]
NEGATIVE_CONTROLS = [annotated(name, text) for name, text in [
    ("school question", "Can you explain photosynthesis for class 204?"),
    ("calendar", "November 15, 2026"), ("math", "2 + 2 = 4; 3.14159"),
    ("currency", "$1,234.56 and 12%"), ("short numeric ID", "ID 1234567"),
    ("count", "We planted 100 seeds and harvested 25 baskets."),
    ("IPv6 unsupported", "Documentation network 2001:db8::1"),
    ("invalid IPv4", "Host 999.999.999.999"),
    ("placeholder", "Contact [EMAIL_1] or [PHONE_1]."),
    ("names unmarked", "Fictional Alex Chen and Taylor Example met."),
]]


def reports() -> dict:
    return {"Baseline · original 37": evaluate(DATASET),
            "Adversarial · extended": evaluate(ADVERSARIAL),
            "Negative controls": evaluate(NEGATIVE_CONTROLS)}


def latency_sample() -> dict:
    from statistics import median
    from time import perf_counter_ns
    text = ("Fictional garden message alex@example.com; phone 949-555-0134. " * 20)[:1000]
    durations = []
    for _ in range(100):
        start = perf_counter_ns()
        detect(text)
        durations.append((perf_counter_ns() - start) / 1_000_000)
    return {"characters": len(text), "runs": len(durations), "median_ms": median(durations)}


if __name__ == "__main__":
    print(json.dumps({"datasets": reports(), "latency": latency_sample()}, indent=2))
