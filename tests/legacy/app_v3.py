"""PrivacyGate: a local privacy checkpoint with a policy-enforced simulation."""
from pathlib import Path
import streamlit as st
from components import state
from components.workflow import render_workspace
from components.evidence import render_evidence
from components.help import render_help

st.set_page_config(page_title="PrivacyGate · Review before sharing", page_icon=":material/shield:", layout="wide")
state.initialize()
st.html(Path(__file__).resolve().parents[2] / 'styles' / 'theme.css')
st.html('''<header class="pg-brand"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6l-8-3Z"/><path d="m8 12 3 3 5-6"/></svg><h1>PrivacyGate</h1><span class="pg-badge">Local demo · No external sending</span></header><p class="pg-pitch">A privacy checkpoint before you share. Inspect, hide, and test your message.</p>''')
with st.container(key="privacy_strip"):
    brief, details = st.columns([4, 1])
    brief.caption("Local-server processing · Remote hosting sends text to that host · Manual copy bypasses this app")
    details.button("Privacy details", on_click=state.show_help, use_container_width=True)
workspace, evidence, help_tab = st.tabs(["Workspace", "Evaluation", "How it works"], key="navigation", on_change="rerun")
# Keep workspace widgets rendered so navigation never discards sensitive review state.
with workspace:
    render_workspace()
if evidence.open:
    with evidence:
        render_evidence()
if help_tab.open:
    with help_tab:
        render_help()
