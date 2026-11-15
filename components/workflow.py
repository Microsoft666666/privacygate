"""Compose, review and simulation, with one authoritative submission service."""
from html import escape
import json
import streamlit as st
from components import state
from components.findings import render_findings
from components.inspector import original_preview, outgoing_preview, occurrence_count
from demo_cases import DEMOS
from detector import detect
from policy import POLICIES
from risk_cards import LABELS
from submission_service import Decision, evaluate_submission


def status_card(decision) -> None:
    if not decision.fingerprint:
        title, detail, kind = "Cannot send", "Validation is unavailable. Check the destination and rules, then try again.", "block"
    elif decision.action == "BLOCK":
        title, detail, kind = "Cannot send", "Replace or remove the details prohibited by this destination.", "block"
    elif not decision.accepted:
        title, detail, kind = "Review required", "Hide the remaining details or acknowledge this exact outgoing message.", "warn"
    else:
        title, detail, kind = "Meets selected demo policy", "No configured rule blocks this simulation. This is not a guarantee of privacy.", "ready"
    if decision.categories:
        detail += " Detected: " + ", ".join(LABELS.get(c, c).split(" · ")[0].lower() for c in decision.categories) + "."
    st.html(f'<div class="pg-status {kind}" role="status"><strong>{escape(title)}</strong>{escape(detail)}</div>')


def render_workspace() -> None:
    st.caption("TRY A FICTIONAL SCENARIO · loading never submits")
    with st.container(key="demo_strip"):
        for col, name in zip(st.columns(4), ("Student essay", "Payment info", "Harmless text", "Social post")):
            col.button(name, key=f"preset_{name}", on_click=state.load_demo, args=(name,), use_container_width=True)

    decision, context, rules = None, "", ()
    with st.container(key="workflow_columns"):
        compose, review = st.columns([1, 1.12], gap="medium")
        with compose, st.container(key="compose_panel"):
            st.subheader("1 · Compose")
            st.selectbox("Destination", list(POLICIES), key="destination", on_change=state.invalidate)
            st.text_area("Message to inspect", key="source", height=190, on_change=state.source_changed,
                         placeholder="Write a message, or try a fictional scenario above.")
            st.button("Check privacy", key="check_privacy", type="primary", use_container_width=True,
                      disabled=not st.session_state.source.strip(), on_click=state.scan)
            if st.session_state.source_stale:
                st.caption("Message changed — check privacy again. Earlier findings cannot authorize a send.")
            with st.expander("Add a missed sensitive detail"):
                st.caption("1 · Enter the exact phrase. Matching is literal and case-sensitive.")
                st.text_input("Exact phrase from the original message", key="manual_input", placeholder="Alex Chen")
                count = occurrence_count(st.session_state.source, st.session_state.manual_input)
                st.caption(f"{count} matching position(s). Overlapping matches are merged during review.")
                st.caption("2 · Choose what kind of detail it is.")
                st.selectbox("Sensitivity label", list(state.MANUAL_LABELS), key="manual_label")
                st.caption("3 · Protect the phrase, then choose occurrences to hide in Review.")
                st.button("Protect this phrase", on_click=state.add_manual)
                if "mark_status" in st.session_state:
                    st.info(st.session_state.mark_status)
            with st.expander("Advanced settings"):
                st.text_area("Sensitive keywords / phrases · one exact phrase per line", key="keywords", on_change=state.rules_changed,
                             help="Literal, case-sensitive matching. Session only; all destinations block these matches.")
                st.button("Clear phrase rules", on_click=state.clear_rules)
                st.caption(f"{len(st.session_state.manual_rules)} manual rule(s) active. Clearing rules changes what this app protects.")
            reset, clear = st.columns(2)
            reset.button("Reset demo", on_click=state.load_demo, use_container_width=True, help="Replace this draft with the last chosen preset and clear the local inbox.")
            clear.button("Clear session", on_click=state.clear_session, use_container_width=True, help="Clear draft, review, rules, results and inbox. Does not erase clipboard/history.")

        with review, st.container(key="review_panel"):
            st.subheader("2 · Review")
            rules = state.configured_rules()
            destination = st.session_state.destination
            if not st.session_state.scanned:
                st.html('<div class="pg-empty"><strong>Your checkpoint starts here</strong>Write or load a message, then choose Check privacy. You’ll see what was detected, why it matters, and exactly what would enter the local simulation.</div>')
                st.caption("No scan yet · nothing submitted")
            else:
                try:
                    with st.spinner("Checking local patterns…"):
                        findings = detect(st.session_state.source, rules)
                except Exception:
                    findings = None
                    st.error("Validation unavailable. Check privacy again before continuing.")
                if findings is not None:
                    raw = evaluate_submission(st.session_state.source, destination, sensitive_phrases=rules)
                    counts = dict(raw.counts)
                    st.caption(f"{len(findings)} found · {counts.get('BLOCK', 0)} block · {counts.get('WARN', 0)} require review · in the original")
                    # A compact outgoing status precedes potentially long finding lists.
                    status_slot = st.empty()
                    selected = render_findings(findings, destination, POLICIES.get(destination, {}))
                    if not findings:
                        st.info("No supported patterns detected. Not a guarantee of privacy.")
                    mode_col, action_col = st.columns([1, 1])
                    mode_col.selectbox("Redaction mode", ["Replace", "Mask", "Remove"], key="mode", on_change=state.selection_changed)
                    with action_col:
                        st.caption("Apply to checked details")
                        st.button("Redact selected", disabled=not selected, on_click=state.selection_changed, use_container_width=True)
                    if st.session_state.mode == "Mask":
                        st.caption("Partial masking keeps characters and still requires review (or blocks public posting). It is not anonymization.")
                    st.text_area("Reviewed message", key="review", height=150, on_change=state.invalidate,
                                 help="Exact outgoing text. Edits are rechecked; acknowledgement is cleared.")
                    st.caption("Changing a redaction choice rebuilds output from the original. Manual output edits are replaced by that action.")
                    context = json.dumps([st.session_state.source, selected, st.session_state.mode])
                    decision = evaluate_submission(st.session_state.review, destination, st.session_state.get("approval"), context, rules)
                    st.session_state.pending_fingerprint = decision.fingerprint
                    with status_slot.container():
                        status_card(decision)
                    if decision.action == "WARN":
                        st.checkbox("I reviewed the remaining details and acknowledge this exact outgoing message.",
                                    key="confirm", on_change=state.acknowledge)
                    st.button("Prepare approved copy", disabled=not decision.accepted, on_click=prepare_copy, use_container_width=True)
                    if st.session_state.get("approved_copy") == decision.fingerprint and decision.accepted:
                        st.caption("Use the copy icon. This permission applies only to this prepared copy; browser manual copy is not controlled.")
                        st.code(st.session_state.review, language=None)

    if st.session_state.scanned and decision is not None:
        with st.expander("Before / after inspector", expanded=True):
            st.caption("Detected values in the original are masked until revealed. Underlines and labels identify rule actions without relying on color.")
            st.button("Hide original values" if st.session_state.get("reveal_original") else "Reveal original values",
                      on_click=state.toggle_reveal, args=("reveal_original",))
            original, outgoing = st.columns(2)
            with original:
                st.write("**Original · never submitted automatically**")
                st.html(original_preview(st.session_state.source, findings, POLICIES.get(destination, {}), st.session_state.get("reveal_original", False)))
            with outgoing:
                st.write("**Outgoing · exact text checked again at send**")
                st.html(outgoing_preview(st.session_state.review))

    with st.container(key="simulation_panel"):
        st.subheader("3 · Simulated destination")
        st.caption(f"{st.session_state.destination} · LOCAL DEMO · no external sending")
        if decision is None:
            st.info("Check your message before submitting to the local simulation.")
        else:
            controls = st.columns([2, 1, 1])
            controls[0].button("Submit to simulated destination", type="primary", disabled=not decision.accepted,
                               on_click=send, use_container_width=True)
            if not decision.accepted:
                controls[1].button("Test rejected attempt", on_click=send, use_container_width=True)
                st.caption("Cannot submit until prohibited details are removed and any remaining warnings are acknowledged.")
            controls[2].button("Reset simulation", on_click=state.reset_simulation, use_container_width=True)
        if "result" in st.session_state:
            result = st.session_state.result
            if result.accepted:
                st.success("Accepted by policy · Local simulation only — nothing sent externally.")
            else:
                # One rejection card, and no pretend incoming message.
                st.error("Not sent — policy blocked." if result.action == "BLOCK" else "Not sent — acknowledgement required.")
        if "outbox" in st.session_state:
            received = st.session_state.outbox
            with st.container(border=True):
                st.write(f"**Incoming · {received['destination']} · SIMULATION**")
                st.text(received["text"])
                st.caption(f"Receipt: {received['classification']} at approval. Only the latest approved message is kept in session. This is not approval of the current draft.")
        else:
            st.html('<div class="pg-empty"><strong>Incoming · no approved message yet</strong>Check the draft, resolve its blockers, then submit. Rejected attempts leave this inbox empty.</div>')


def final_check() -> Decision:
    """Read current widget state in callbacks, never captured old rules/context."""
    try:
        if not st.session_state.scanned:
            raise ValueError("Stale source")
        rules = state.configured_rules()
        findings = detect(st.session_state.source, rules)
        selected = [i for i in range(len(findings)) if st.session_state.get(f"finding_{i}", True)]
        context = json.dumps([st.session_state.source, selected, st.session_state.mode])
        return evaluate_submission(st.session_state.review, st.session_state.destination,
                                   st.session_state.get("approval"), context, rules)
    except Exception:
        return Decision("BLOCK", False, (), ("Current scan required",), "Not sent — validation unavailable. Check privacy again.")


def prepare_copy() -> None:
    checked = final_check()
    if checked.accepted:
        st.session_state.approved_copy = checked.fingerprint
    else:
        st.session_state.pop("approved_copy", None)
        st.session_state.result = checked


def send() -> None:
    checked = final_check()
    st.session_state.result = checked
    if checked.accepted:
        st.session_state.outbox = {"destination": st.session_state.destination, "text": st.session_state.review,
                                   "classification": checked.action, "categories": checked.categories}
