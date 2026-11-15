"""Compact risk cards with plain-language actions and deliberate disclosure."""
import streamlit as st
from components import state
from components.inspector import ACTION_LABELS
from redaction import redact
from risk_cards import LABELS, explanation


def render_findings(findings: list, destination: str, policy: dict) -> list[int]:
    selected = []
    for i, finding in enumerate(findings):
        action = policy.get(finding.category, "BLOCK")
        with st.container(border=True):
            label = LABELS.get(finding.category, "Sensitive detail").split(" · ")[0]
            if st.checkbox(f"Hide {label.lower()} · {ACTION_LABELS.get(action, 'Cannot send')}",
                           value=True, key=f"finding_{i}", on_change=state.selection_changed):
                selected.append(i)
            st.caption(f"{'Marked by you' if finding.origin == 'user-provided' else 'Pattern detected'} · •••• · item {i + 1}")
            if action == "BLOCK":
                st.write(f"Your {destination} policy does not allow this detail. Replace or remove it to continue.")
            elif action == "WARN":
                st.write("Replace this detail, or explicitly acknowledge the remaining disclosure before simulating.")
            else:
                st.write("This destination permits this category. You can still choose to hide it.")
            with st.expander("Why this matters & technical details"):
                st.write(explanation(finding.category, destination))
                st.text(f"Category: {finding.category}\nOffsets: [{finding.start}, {finding.end})\nRule: {finding.reason}\nHeuristic confidence: {finding.confidence}; not a statistical probability.")
                if st.button("Reveal this match", key=f"reveal_button_{i}", on_click=state.toggle_reveal, args=(f"reveal_value_{i}",)):
                    pass
                if st.session_state.get(f"reveal_value_{i}"):
                    st.code(finding.matched_text, language=None)
    return selected
