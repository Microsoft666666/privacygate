"""Authoritative, fail-closed boundary shared by simulation and approved copy.

Decisions contain metadata only. No message, finding value, or error payload is logged.
"""
from dataclasses import dataclass
from detector import detect, ner_enabled
from policy import evaluate_policy, review_fingerprint


@dataclass(frozen=True)
class Decision:
    action: str
    accepted: bool
    categories: tuple[str, ...]
    reasons: tuple[str, ...]
    message: str
    fingerprint: str | None = None
    counts: tuple[tuple[str, int], ...] = ()
    combination: tuple[str, ...] = ()


def evaluate_submission(final_text: str, destination: str, confirmations: str | None = None,
                        context: str = "", sensitive_phrases: tuple = (), *, ner: bool | None = None, ignore_values=()) -> Decision:
    try:
        if not isinstance(final_text, str) or not isinstance(destination, str):
            raise ValueError("Invalid input")
        # Both operations run every time, including copy and direct backend calls.
        effective_ner = ner_enabled() if ner is None else ner
        findings = [f for f in detect(final_text, sensitive_phrases, ner=effective_ner) if f.matched_text not in ignore_values]
        decision = evaluate_policy(findings, destination)
        fingerprint = review_fingerprint(final_text, destination, context, sensitive_phrases, ner=effective_ner, ignore_values=ignore_values)
        categories = tuple(sorted({f.category for f in findings}))
        reasons = tuple(f"{action}: {', '.join(sorted({f.category for f in group}))}"
                        for action, group in decision.findings_by_action.items() if group)
        counts = tuple((action, len(group)) for action, group in decision.findings_by_action.items())
        accepted = decision.overall_action == "ALLOW" or (
            decision.overall_action == "WARN" and confirmations == fingerprint)
        message = decision.message
        if accepted:
            message = "Accepted by policy. Sent to local simulation only when you submit; no external transmission."
        elif decision.overall_action == "WARN":
            message = "Not sent — acknowledgement required. " + message
        else:
            message = "Not sent — policy blocked. " + message
        return Decision(decision.overall_action, accepted, categories, reasons, message, fingerprint, counts, decision.combination)
    except Exception:
        # Never display exception messages: third-party exceptions may echo input.
        return Decision("BLOCK", False, (), ("Validation unavailable",),
                        "Not sent — validation unavailable. Check the destination/rules and try again.")
