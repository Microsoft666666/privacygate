"""Data-driven destination policies and an independently enforced local submission."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from detector import Finding, detect

POLICY_VERSION = "3.0"

POLICIES = {
    "AI Chatbot": {"EMAIL": "WARN", "US_PHONE": "BLOCK", "SSN": "BLOCK", "PAYMENT_CARD": "BLOCK"},
    "Public Forum": {"EMAIL": "BLOCK", "US_PHONE": "BLOCK", "SSN": "BLOCK", "PAYMENT_CARD": "BLOCK"},
    "Personal Notes (local demo)": {"EMAIL": "ALLOW", "US_PHONE": "WARN", "SSN": "BLOCK", "PAYMENT_CARD": "BLOCK"},
}

for destination, rules in POLICIES.items():
    rules["IPV4"] = "BLOCK" if destination == "Public Forum" else "WARN"
    rules["PARTIAL_DETAIL"] = "BLOCK" if destination == "Public Forum" else "WARN"
    for category in ("MANUAL_IDENTIFIER", "MANUAL_ADDRESS", "MANUAL_CONFIDENTIAL", "USER_PHRASE"):
        rules[category] = "BLOCK"
REQUIRED_CATEGORIES = frozenset(next(iter(POLICIES.values())))



@dataclass(frozen=True)
class PolicyDecision:
    overall_action: str
    findings_by_action: dict[str, list[Finding]]
    message: str


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
    action = next((action for action in groups if groups[action]), "ALLOW")
    categories = ", ".join(sorted({f.category for f in groups[action]}))
    message = {
        "BLOCK": f"Blocked by policy: redact or edit {categories} before simulated submission.",
        "WARN": f"Confirmation required for: {categories}.",
        "ALLOW": "No policy rule prevents this simulation. This is not a guarantee of privacy.",
    }[action]
    return PolicyDecision(action, groups, message)


def review_fingerprint(text: str, destination: str, context: str = "", sensitive_phrases: tuple = ()) -> str:
    """Bind acknowledgement to exact output, source/selection context, and policy."""
    payload = json.dumps([text, destination, context, POLICY_VERSION, POLICIES[destination],
                          [asdict(rule) for rule in sensitive_phrases]], sort_keys=True)
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
