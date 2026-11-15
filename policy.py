"""Data-driven destination policies and an independently enforced local submission."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from detector import Finding, detect, ner_enabled

POLICY_VERSION = "4.0"

POLICIES = {'AI Chatbot': {'EMAIL': 'WARN',
                'US_PHONE': 'BLOCK',
                'SSN': 'BLOCK',
                'PAYMENT_CARD': 'BLOCK',
                'IPV4': 'WARN',
                'PARTIAL_DETAIL': 'WARN',
                'MANUAL_IDENTIFIER': 'BLOCK',
                'MANUAL_ADDRESS': 'BLOCK',
                'MANUAL_CONFIDENTIAL': 'BLOCK',
                'USER_PHRASE': 'BLOCK',
                'INTL_PHONE': 'BLOCK',
                'BANK_ACCOUNT': 'BLOCK',
                'DATE_OF_BIRTH': 'WARN',
                'SECRET': 'BLOCK',
                'STREET_ADDRESS': 'BLOCK',
                'PERSON': 'WARN',
                'LOCATION': 'ALLOW',
                'SCHOOL': 'WARN',
                'NATIONAL_ID': 'BLOCK',
                'COMBINED_IDENTIFIERS': 'WARN'},
 'Public Forum': {'EMAIL': 'BLOCK',
                  'US_PHONE': 'BLOCK',
                  'SSN': 'BLOCK',
                  'PAYMENT_CARD': 'BLOCK',
                  'IPV4': 'BLOCK',
                  'PARTIAL_DETAIL': 'BLOCK',
                  'MANUAL_IDENTIFIER': 'BLOCK',
                  'MANUAL_ADDRESS': 'BLOCK',
                  'MANUAL_CONFIDENTIAL': 'BLOCK',
                  'USER_PHRASE': 'BLOCK',
                  'INTL_PHONE': 'BLOCK',
                  'BANK_ACCOUNT': 'BLOCK',
                  'DATE_OF_BIRTH': 'BLOCK',
                  'SECRET': 'BLOCK',
                  'STREET_ADDRESS': 'BLOCK',
                  'PERSON': 'WARN',
                  'LOCATION': 'WARN',
                  'SCHOOL': 'WARN',
                  'NATIONAL_ID': 'BLOCK',
                  'COMBINED_IDENTIFIERS': 'BLOCK'},
 'Personal Notes (local demo)': {'EMAIL': 'ALLOW',
                                 'US_PHONE': 'WARN',
                                 'SSN': 'BLOCK',
                                 'PAYMENT_CARD': 'BLOCK',
                                 'IPV4': 'WARN',
                                 'PARTIAL_DETAIL': 'WARN',
                                 'MANUAL_IDENTIFIER': 'BLOCK',
                                 'MANUAL_ADDRESS': 'BLOCK',
                                 'MANUAL_CONFIDENTIAL': 'BLOCK',
                                 'USER_PHRASE': 'BLOCK',
                                 'INTL_PHONE': 'WARN',
                                 'BANK_ACCOUNT': 'WARN',
                                 'DATE_OF_BIRTH': 'ALLOW',
                                 'SECRET': 'BLOCK',
                                 'STREET_ADDRESS': 'WARN',
                                 'PERSON': 'ALLOW',
                                 'LOCATION': 'ALLOW',
                                 'SCHOOL': 'ALLOW',
                                 'NATIONAL_ID': 'BLOCK',
                                 'COMBINED_IDENTIFIERS': 'ALLOW'}}

REQUIRED_CATEGORIES = frozenset(next(iter(POLICIES.values())))



@dataclass(frozen=True)
class PolicyDecision:
    overall_action: str
    findings_by_action: dict[str, list[Finding]]
    message: str
    combination: tuple[str, ...] = ()


def evaluate_policy(findings: list[Finding], destination: str) -> PolicyDecision:
    rules = POLICIES[destination]
    required = REQUIRED_CATEGORIES
    if not isinstance(rules, dict) or not required.issubset(rules) or any(
        value not in {"ALLOW", "WARN", "BLOCK"} for value in rules.values()
    ):
        raise ValueError("Invalid policy configuration")
    groups: dict[str, list[Finding]] = {action: [] for action in ("BLOCK", "WARN", "ALLOW")}
    for finding in findings:
        groups[rules.get(finding.category, "BLOCK")].append(finding)
    quasi = tuple(sorted({'PERSON', 'SCHOOL', 'LOCATION', 'DATE_OF_BIRTH'} & {f.category for f in findings}))
    combination = quasi if len(quasi) >= 3 else ()
    if combination:
        groups[rules.get('COMBINED_IDENTIFIERS', 'BLOCK')].append(
            Finding('COMBINED_IDENTIFIERS', 0, 0, '', 'Together these details can identify you.'))
    action = next((action for action in groups if groups[action]), "ALLOW")
    categories = ", ".join(sorted({f.category for f in groups[action]}))
    message = {
        "BLOCK": f"Blocked by policy: redact or edit {categories} before simulated submission.",
        "WARN": f"Confirmation required for: {categories}.",
        "ALLOW": "No policy rule prevents this simulation. This is not a guarantee of privacy.",
    }[action]
    return PolicyDecision(action, groups, message, combination)


def review_fingerprint(text: str, destination: str, context: str = "", sensitive_phrases: tuple = (), *, ner: bool | None = None, ignore_values=()) -> str:
    """Bind acknowledgement to exact output, source/selection context, and policy."""
    payload = json.dumps([text, destination, context, POLICY_VERSION, POLICIES[destination],
                          [asdict(rule) for rule in sensitive_phrases], ner_enabled() if ner is None else ner, sorted(ignore_values)], sort_keys=True)
    return sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class SubmissionResult:
    accepted: bool
    message: str


def submit_simulated(text: str, destination: str, approval: str | None = None, context: str = "") -> SubmissionResult:
    # Compatibility wrapper; all new callers use the structured service directly.
    from submission_service import evaluate_submission
    decision = evaluate_submission(text, destination, approval, context)
    return SubmissionResult(decision.accepted, decision.message)
