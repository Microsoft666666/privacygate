"""Focused compose → review → fix → copy workflow."""
from html import escape
import json
import streamlit as st
from detector import SensitivePhrase, mark_phrase
from policy import POLICIES
from submission_service import Decision, evaluate_submission
from suggestions import suggest_fixes, apply_fixes
from components.clipboard import render_copy

DEMO = "Hi, I'm Alex. Please help improve this scholarship essay. I volunteered at our community garden and organized weekend activities. If you need to reach me, my email is alex@example.com and my phone number is 949-555-0134."
LABELS = {'US_PHONE': 'Phone number', 'EMAIL': 'Email address', 'PAYMENT_CARD': 'Payment card', 'SSN': 'SSN-like number', 'IP_ADDRESS': 'IP address'}
REASONS = {'US_PHONE': 'May reveal a personal contact number.', 'EMAIL': 'May identify or contact you.', 'PAYMENT_CARD': 'A card-like number passed checksum validation.', 'SSN': 'Matches a sensitive ID format.', 'IP_ADDRESS': 'May expose a network address.'}


def initialize():
    for k, v in dict(source='', review='', scanned=False, confirm=False, rules=[], mapping={}, manual_input='').items():
        st.session_state.setdefault(k, v)


def invalidate():
    st.session_state.confirm = False
    st.session_state.pop('approval', None)
    st.session_state.pop('copy_ready', None)


def source_changed():
    invalidate()
    st.session_state.scanned = False
    st.session_state.review = ''
    st.session_state.mapping = {}


def load_demo():
    clear()
    initialize()
    st.session_state.source = DEMO


def clear():
    for k in list(st.session_state):
        del st.session_state[k]


def scan():
    invalidate()
    st.session_state.review = st.session_state.source
    st.session_state.scanned = True
    st.session_state.mapping = {}


def check():
    try:
        if not st.session_state.scanned:
            raise ValueError('Scan required')
        context = json.dumps([st.session_state.source, 'focused-copy'])
        return evaluate_submission(st.session_state.review, 'AI Chatbot', st.session_state.get('approval'), context, tuple(st.session_state.rules))
    except Exception:
        return Decision('BLOCK', False, (), ('Validation unavailable',), 'Check privacy again.')


def acknowledge():
    st.session_state.pop('copy_ready', None)
    st.session_state.approval = check().fingerprint if st.session_state.confirm else None


def fix(index=None):
    invalidate()
    try:
        suggestions, mapping = suggest_fixes(st.session_state.review, tuple(st.session_state.rules), st.session_state.mapping)
        selected = suggestions if index is None else [suggestions[index]]
        st.session_state.review = apply_fixes(st.session_state.review, selected)
        st.session_state.mapping = mapping
    except Exception:
        st.session_state.scanned = False


def protect():
    try:
        rule = mark_phrase(st.session_state.review, st.session_state.manual_input, 'MANUAL_CONFIDENTIAL')
    except ValueError:
        st.session_state.mark_error = 'Enter an exact phrase from the reviewed message.'
        return
    invalidate()
    if rule not in st.session_state.rules:
        st.session_state.rules = [*st.session_state.rules, rule]
    st.session_state.manual_input = ''
    st.session_state.pop('mark_error', None)


def prepare_copy():
    decision = check()  # Never trust a previous button-enabled state.
    st.session_state.copy_ready = decision.fingerprint if decision.accepted else None


def render():
    initialize()
    st.html('<nav class="pg-nav"><strong>PrivacyGate</strong><span>Review before sharing</span></nav><div class="pg-intro"><h1>Make sure your message<br>is ready to share.</h1><p>Find private details and fix them before copying.</p></div>')
    st.button('Try demo', on_click=load_demo, help='Load one fictional message. Nothing is scanned or shared automatically.')
    with st.container(key='workflow_columns'):
        left, right = st.columns(2, gap='large')
        with left, st.container(key='compose_panel'):
            st.subheader('01  Compose')
            st.text_area('Your message', key='source', height=230, on_change=source_changed, placeholder='Paste or write the message you want to review…')
            st.button('Check privacy', key='check_privacy', type='secondary' if st.session_state.scanned else 'primary', disabled=not st.session_state.source.strip(), on_click=scan, use_container_width=True)
        with right, st.container(key='review_panel'):
            st.subheader('02  Review')
            if not st.session_state.scanned:
                st.html('<div class="pg-empty">No scan yet. Check your message to see suggestions.</div>')
            else:
                decision = check()
                if not decision.fingerprint:
                    st.error('Validation unavailable. Check privacy again.')
                else:
                    suggestions, mapping = suggest_fixes(st.session_state.review, tuple(st.session_state.rules), st.session_state.mapping)
                    st.session_state.mapping = mapping
                    title = 'Ready to copy' if decision.accepted else ('Some details need fixing' if decision.action == 'BLOCK' else 'Review the remaining warning')
                    st.html(f'<div class="pg-status {decision.action.lower() if not decision.accepted else "ready"}" role="status" aria-live="polite" aria-atomic="true">{escape(title)}</div>')
                    if not suggestions:
                        st.caption('No supported sensitive patterns found. Detection can miss private details.')
                    for i, s in enumerate(suggestions):
                        f = s.finding
                        action = POLICIES['AI Chatbot'].get(f.category, 'BLOCK')
                        label = 'Blocked' if action == 'BLOCK' else 'Review recommended'
                        st.markdown(f'**{LABELS.get(f.category, "Protected detail")} · {label}**')
                        st.caption(REASONS.get(f.category, 'You chose to protect this phrase.'))
                        st.caption('Blocked for AI-chatbot sharing under this policy.' if action == 'BLOCK' else 'Keep only after acknowledging the warning below.')
                        # Native text rendering escapes the matched value.
                        st.text(f'Replace {f.matched_text} with {s.replacement}')
                        st.button('Apply fix', key=f'fix_{i}', on_click=fix, args=(i,))
                    if len(suggestions) > 1:
                        st.button('Apply all recommended fixes', on_click=fix, type='primary', use_container_width=True)
                    with st.expander("Didn't detect something?"):
                        st.text_input('Exact phrase in reviewed message', key='manual_input')
                        st.button('Protect this phrase', on_click=protect)
                        if st.session_state.get('mark_error'):
                            st.error(st.session_state.mark_error)
    if st.session_state.scanned:
        with st.container(key='output_panel'):
            st.subheader('Reviewed message')
            st.text_area('Edit the revised text', key='review', height=160, on_change=invalidate, help='Manual edits are rechecked and reset warning acknowledgement.')
            decision = check()
            if decision.action == 'WARN':
                st.checkbox('Keep with warning — I acknowledge the remaining details in this exact message.', key='confirm', on_change=acknowledge)
            # Native server button validates fresh widget state before clipboard data is mounted.
            st.button('Copy reviewed message', disabled=not decision.accepted, on_click=prepare_copy, type='primary')
            if decision.accepted and st.session_state.get('copy_ready') == decision.fingerprint:
                render_copy(st.session_state.review, decision.fingerprint)
    st.button('Clear', on_click=clear)
    st.caption('Text is processed on the server hosting this app · No external scanning API')
    with st.expander('About privacy'):
        st.write('When Streamlit runs on your computer, processing stays local. A remote deployment sends your text to that host. No external scanning API or message storage is used.')
        st.write('This checks selected patterns under an AI-chatbot policy. It can miss private information. You can manually copy unreviewed text; PrivacyGate cannot protect sharing outside this workflow. Clear removes session-held text, not clipboard contents or browser history.')
