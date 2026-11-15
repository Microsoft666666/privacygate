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
    requires_ner: bool = False


def annotated(name: str, *parts: str | tuple[str, str], sensitive_phrases: tuple[SensitivePhrase, ...] = (), requires_ner: bool = False) -> Case:
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
    return Case(name, text, tuple(spans), sensitive_phrases, requires_ner)


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


# Independent hand-authored ground truth. Keep misses; do not tune annotations to output.
REALISTIC = [
    annotated('essay/contact', 'Please edit my scholarship essay. My email is ', ('EMAIL','alex@example.com'), '; keep the ending warm.'),
    annotated('essay/callback', 'I led a garden project. The committee can call ', ('US_PHONE','949-555-0134'), ' for questions.'),
    annotated('essay/name', "My name is ", ('PERSON','Alex Chen'), ', and volunteering changed how I think about leadership.', requires_ner=True),
    annotated('essay/school', 'I organized a garden at ', ('SCHOOL','Northwood High School'), ' and trained new volunteers.', requires_ner=True),
    annotated('essay/city', 'I grew up in ', ('LOCATION','Irvine'), ' and want to study environmental engineering.', requires_ner=True),
    annotated('essay/birthday', 'I was born ', ('DATE_OF_BIRTH','March 7, 2009'), '. Should I remove that detail from my essay?'),
    annotated('essay/address', 'Please polish this draft. I live at ', ('STREET_ADDRESS','123 Main St, Irvine, CA 92618'), ' near our garden.'),
    annotated('essay/overseas', 'My mentor can reach me at ', ('INTL_PHONE','+44 20 7946 0958'), ' during the interview week.'),
    annotated('essay/two-contacts', 'Proofread this signature: ', ('EMAIL','garden@example.org'), ' | ', ('US_PHONE','949-555-0135'), '.'),
    annotated('essay/combination', "I'm ", ('PERSON','Alex Chen'), ' from ', ('SCHOOL','Northwood High School'), ' in ', ('LOCATION','Irvine'), '.', requires_ner=True),
    annotated('essay/negative-reflection', 'Helping others taught me patience. Please make this paragraph clearer without changing my voice.'),
    annotated('essay/negative-year', 'In 2026 our club planted 100 seeds and harvested 25 baskets.'),
    annotated('essay/negative-generic', 'The high school students planted tomatoes and shared the harvest.'),
    annotated('essay/negative-budget', 'We raised $1,234.56 and spent 20% on tools. Please shorten this sentence.'),
    annotated('essay/negative-story', 'My family faced a difficult year. I am proud that I kept showing up for others.'),
    annotated('homework/email', 'Can you explain this assignment? My class contact is ', ('EMAIL','student@example.org'), '.'),
    annotated('homework/phone', 'Help draft a study-group invitation with my number ', ('US_PHONE','(949) 555-0134'), '.'),
    annotated('homework/cn-phone', '请帮我整理学习计划。我的手机是 ', ('INTL_PHONE','138 0013 8000'), '。'),
    annotated('homework/date', 'Help me fill out this practice form: DOB: ', ('DATE_OF_BIRTH','2009-03-07'), '.'),
    annotated('homework/ssn', 'Explain why this sample form asks for SSN ', ('SSN','123456789'), '.'),
    annotated('homework/national-id', '这个练习表格中的身份证号是 ', ('NATIONAL_ID','110105200001010016'), '。请解释这个字段。'),
    annotated('homework/name', 'Write a polite tutoring request for ', ('PERSON','Jordan Lee'), '.', requires_ner=True),
    annotated('homework/school', 'Help me write an invitation for students at ', ('SCHOOL','Stanford University'), '.', requires_ner=True),
    annotated('homework/network', 'Explain this networking exercise: router ', ('IPV4','192.0.2.15'), ' cannot connect.'),
    annotated('homework/marked', 'Please summarize ', ('USER_PHRASE','Project Falcon'), ' but keep its name private.', sensitive_phrases=(SensitivePhrase('Project Falcon'),)),
    annotated('homework/negative-math', 'Explain why 2 + 2 = 4 and approximate pi as 3.14159.'),
    annotated('homework/negative-meeting', 'Our study group meets on 2026-11-15. Please suggest an agenda.'),
    annotated('homework/negative-room', 'Can you explain photosynthesis for class 204?'),
    annotated('homework/negative-account', 'What does the account settings page do? Explain in simple language.'),
    annotated('homework/negative-calendar', 'Make a revision plan for November 15, 2026, with 30-minute breaks.'),
    annotated('coding/openai', 'Why does this request fail? api_key = "', ('SECRET','sk-'+'ab'*15), '"'),
    annotated('coding/github', 'My CI config contains TOKEN="', ('SECRET','gh'+'p_'+'x'*36), '". Help debug authentication.'),
    annotated('coding/database', 'The connection string is postgres://app:', ('SECRET','pw'*5), '@localhost/app. Why is login failing?'),
    annotated('coding/password', 'The demo says password: ', ('SECRET','Hunter2'), '. Is the assignment syntax correct?'),
    annotated('coding/aws', 'The access key is ', ('SECRET','AK'+'IA'+'A1'*8), '. Why does my upload fail?'),
    annotated('coding/google', 'The browser script uses ', ('SECRET','AI'+'za'+'a'*35), ' as the credential.'),
    annotated('coding/private-key', 'Please explain this config:\n', ('SECRET','-----BEGIN '+'PRIVATE KEY-----\nfictional\n-----END '+'PRIVATE KEY-----')),
    annotated('coding/server', 'My service connects to ', ('IPV4','198.51.100.9'), '. Can you explain a timeout?'),
    annotated('coding/email-log', 'This sample error mentions user ', ('EMAIL','alex@example.org'), ' and status 403.'),
    annotated('coding/chinese-password', '我的密码是', ('SECRET','abcd1234'), '。这个设置为什么失败？'),
    annotated('coding/negative-version', 'After upgrading to version 1.2.3.4, the test exits with code 1.'),
    annotated('coding/negative-password-doc', 'Explain password hashing and why a salt should be random.'),
    annotated('coding/negative-token-doc', 'The token counter shows 128 tokens. Explain how the counter works.'),
    annotated('coding/negative-loop', 'for i in range(10): print(i) — why does the loop stop at 9?'),
    annotated('coding/negative-url', 'Use https://example.com/docs for the documentation link in the footer.'),
    annotated('forum/address', 'Please rewrite my lost-item post. Return it to ', ('STREET_ADDRESS','123 Main St'), '.'),
    annotated('forum/phone', 'Selling my old desk. Text ', ('US_PHONE','949-555-0134'), ' to arrange pickup.'),
    annotated('forum/email', 'Volunteers wanted! Email ', ('EMAIL','garden@example.com'), ' for details.'),
    annotated('forum/bank', 'The draft donation instructions say routing ', ('BANK_ACCOUNT','011000015'), ' and account ', ('BANK_ACCOUNT','000123456789'), '.'),
    annotated('forum/iban', 'Please shorten this donation post: IBAN ', ('BANK_ACCOUNT','GB82 WEST 1234 5698 7654 32'), '.'),
    annotated('forum/card', 'I accidentally put card ', ('PAYMENT_CARD','4111 1111 1111 1111'), ' in this support post. Help remove it.'),
    annotated('forum/national-id', '证件号码 ', ('NATIONAL_ID','440304201003150026'), ' 不应该出现在公开帖子里。'),
    annotated('forum/birthday', 'Please edit the party invite. My birthday is ', ('DATE_OF_BIRTH','7 March 2009'), '.'),
    annotated('forum/city', 'Recommend a community garden in ', ('LOCATION','London'), ' for my draft question.', requires_ner=True),
    annotated('forum/partial', 'Does this draft hide enough? Contact ', ('PARTIAL_DETAIL','[PARTIAL_EMAIL_1: a•••m]'), '.'),
    annotated('forum/negative-price', 'Selling a desk for $25. It is 120 cm wide and has two drawers.'),
    annotated('forum/negative-event', 'The cleanup starts on 2026-11-15. Bring gloves and a reusable bottle.'),
    annotated('forum/negative-short-id', 'The book club ticket is 12345678. Please make this post friendly.'),
    annotated('forum/negative-general', 'What are some beginner-friendly vegetables for a small balcony?'),
    annotated('forum/negative-time', 'The library opens at 9:30 and closes at 18:00. Please format this schedule.'),
]


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
