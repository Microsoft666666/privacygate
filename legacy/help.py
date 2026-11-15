"""Dense rules and explanations live outside the primary workflow."""
import streamlit as st
from legacy.demo_cases import DEMO_GUIDES
from policy import POLICIES


def render_help() -> None:
    st.subheader("How the checkpoint works")
    st.write("Compose → local pattern detection → selected redaction → fresh final-text check → local simulated inbox.")
    st.caption("The same authoritative service validates both simulated send and approved copy. Button styling is never the enforcement layer.")
    st.subheader("Processing & privacy boundaries", anchor="privacy-boundaries")
    st.write("**Local server.** Your browser transmits text to Streamlit. Running both on your computer keeps processing local. Remote hosting sends the text to that host.")
    st.write("**What this cannot protect.** Native copying, screenshots, clipboard history, other websites and external submissions remain outside this prototype. Prepared copy is gated; manual copying is not.")
    st.write("**Temporary session state.** Draft, output, phrase rules and the latest approved inbox message live in browser/server session memory. The app does not write these values to files, logs, analytics, a database or persistent caches. Streamlit usage telemetry is disabled in project configuration.")
    st.write("**Clearing.** Clear session removes app-held sensitive state. Reset simulation clears the inbox and approvals. Reset demo replaces the draft with the last selected preset. None securely erases OS/browser memory, history or clipboard copies.")
    st.subheader("What a finding means")
    st.write("Patterns cover common email/US phone formats, SSN-like shapes, Luhn-valid card candidates and validated IPv4 octets. Format/checksum matches do not verify real people or accounts. Confidence labels are heuristic, not probabilities. User-provided phrases are literal and case-sensitive; names are never inferred automatically.")
    st.write("IPv4 version filtering uses an immediate version/build/release/v label unless nearby IP/network wording takes precedence. An actual IP mislabeled as a version can be missed. Internationalized emails, nonbreaking/tab phone spacing, names and contextual secrets still have coverage gaps.")
    st.write("Replace uses stable placeholders. Mask retains limited characters plus a marker that requires review or blocks public posting; deleting the marker can defeat that warning. Remove deletes only selected spans and preserves neighboring text. Selection/mode changes rebuild from the original and replace manual outgoing edits.")
    st.info("No supported matches does not mean no private data. This is not an independently audited security product or a replacement for established DLP tools.")
    with st.expander("Destination policy matrix"):
        st.dataframe([{"Destination": d, **rules} for d, rules in POLICIES.items()], hide_index=True)
        st.caption("Cannot send = BLOCK. Review required = WARN. No configured rule blocks this = ALLOW. Warnings bind to exact text, destination, policy version, rules and review context.")
    st.subheader("Demo guide · fictional examples only")
    for name, guide in DEMO_GUIDES.items():
        with st.expander(name):
            st.write(guide.replace('Scan', 'Check privacy'))
    st.write("**90 seconds:** explain accidental student-data disclosure → load Student essay → Check privacy → Test rejected attempt → uncheck email to redact phone → acknowledge email → simulate → show evidence and remaining errors.")
    st.caption("Optional browser-extension integration is future work, not a working feature. Built with Codex, Python, Streamlit and pytest; present the implementation in your own words and follow organizer disclosure requirements.")
