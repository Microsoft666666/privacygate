"""Session-only workflow state. All sensitive state is cleared on request."""
import streamlit as st
from legacy.demo_cases import DEMOS, DEMO_DESTINATIONS
from detector import SensitivePhrase, detect, mark_phrase
from redaction import redact

MANUAL_LABELS = {"Name": "MANUAL_IDENTIFIER", "Address": "MANUAL_ADDRESS",
                 "Student identifier": "MANUAL_IDENTIFIER", "Other private detail": "MANUAL_CONFIDENTIAL"}


def initialize() -> None:
    defaults = {"source": "", "review": "", "scanned": False, "confirm": False,
                "manual_rules": [], "keywords": "", "manual_input": "", "mode": "Replace",
                "demo": "Student essay", "navigation": "Workspace", "destination": "AI Chatbot",
                "source_stale": False, "transformed": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def invalidate() -> None:
    st.session_state.confirm = False
    for key in ("result", "approved_copy", "approval"):
        st.session_state.pop(key, None)


def clear_choices() -> None:
    for key in list(st.session_state):
        if key.startswith(("finding_", "reveal_")):
            del st.session_state[key]


def source_changed() -> None:
    invalidate()
    clear_choices()
    st.session_state.source_stale = True
    st.session_state.scanned = False
    st.session_state.transformed = False
    st.session_state.review = ""
    st.session_state.pop("mark_status", None)


def configured_rules() -> tuple[SensitivePhrase, ...]:
    return tuple(st.session_state.manual_rules) + tuple(
        SensitivePhrase(line) for line in st.session_state.keywords.splitlines() if line.strip())


def selection_changed() -> None:
    invalidate()
    if not st.session_state.scanned:
        return
    try:
        findings = detect(st.session_state.source, configured_rules())
        selected = [i for i in range(len(findings)) if st.session_state.get(f"finding_{i}", True)]
        st.session_state.review = redact(st.session_state.source, findings, selected, st.session_state.mode).text
        st.session_state.transformed = True
    except Exception:
        st.session_state.scanned = False
        st.session_state.review = ""
        st.session_state.source_stale = True


def rules_changed() -> None:
    invalidate()
    clear_choices()
    st.session_state.transformed = False
    st.session_state.review = st.session_state.source if st.session_state.scanned else ""


def scan() -> None:
    invalidate()
    clear_choices()
    st.session_state.scanned = True
    st.session_state.source_stale = False
    st.session_state.transformed = False
    st.session_state.review = st.session_state.source


def acknowledge() -> None:
    st.session_state.approval = st.session_state.pending_fingerprint if st.session_state.confirm else None


def reset_simulation() -> None:
    invalidate()
    st.session_state.pop("outbox", None)


def load_demo(name: str | None = None) -> None:
    name = name or st.session_state.demo
    source_changed()
    reset_simulation()
    st.session_state.update(source=DEMOS[name], destination=DEMO_DESTINATIONS[name], demo=name,
                            manual_rules=[], keywords="", manual_input="", mode="Replace",
                            navigation="Workspace", source_stale=False)


def load_failure(case) -> None:
    source_changed()
    reset_simulation()
    st.session_state.update(source=case.text, manual_rules=list(case.sensitive_phrases), keywords="",
                            manual_input="", mode="Replace", destination="AI Chatbot", navigation="Workspace")
    scan()


def clear_session() -> None:
    for key in list(st.session_state):
        del st.session_state[key]


def add_manual() -> None:
    try:
        rule = mark_phrase(st.session_state.source, st.session_state.manual_input,
                           MANUAL_LABELS[st.session_state.manual_label])
    except ValueError:
        st.session_state.mark_status = "That phrase is not in your message. Match the spelling, spacing and capital letters exactly."
        return
    if rule not in st.session_state.manual_rules:
        st.session_state.manual_rules = [*st.session_state.manual_rules, rule]
    rules_changed()
    st.session_state.scanned = True
    st.session_state.source_stale = False
    st.session_state.review = st.session_state.source
    st.session_state.mark_status = "Protected. Review matching occurrences on the right (below on small screens)."
    st.session_state.manual_input = ""


def clear_rules() -> None:
    st.session_state.manual_rules = []
    st.session_state.keywords = ""
    st.session_state.manual_input = ""
    st.session_state.pop("mark_status", None)
    rules_changed()


def toggle_reveal(key: str) -> None:
    st.session_state[key] = not st.session_state.get(key, False)


def show_help() -> None:
    st.session_state.navigation = "How it works"
