"""Focused compose → review → fix → copy workflow."""
from html import escape
import json
import os
from recognizers import ner as ner_engine
import streamlit as st
from detector import SensitivePhrase, mark_phrase
from policy import POLICIES
from submission_service import Decision, evaluate_submission
from suggestions import suggest_fixes, apply_fixes, restore_reply
from components.clipboard import render_copy
from components.preview import findings_preview

from demos import SCENARIOS, QUICK_CONTACT
DEMO = QUICK_CONTACT
from recognizers.secrets import masked
from categories import CATEGORY_META, DEFAULT_META


def initialize():
    for k, v in dict(source='', review='', scanned=False, confirm=False, rules=[], mapping={}, manual_input='', destination=next(iter(POLICIES)), style='Placeholder', generated_values=[], demo='Quick contact').items():
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
    st.session_state.generated_values = []
    st.session_state.pop('restored_reply', None)


def load_demo():
    selected = st.session_state.get('demo', 'Quick contact')
    scenario = SCENARIOS[selected]
    clear()
    initialize()
    st.session_state.demo = selected
    st.session_state.source = scenario['text']
    st.session_state.destination = scenario['destination']


def clear():
    for k in list(st.session_state):
        del st.session_state[k]


def scan():
    invalidate()
    st.session_state.review = st.session_state.source
    st.session_state.scanned = True
    st.session_state.mapping = {}
    st.session_state.generated_values = []
    st.session_state.pop('restored_reply', None)


def check():
    try:
        if not st.session_state.scanned:
            raise ValueError('Scan required')
        context = json.dumps([st.session_state.source, 'focused-copy'])
        return evaluate_submission(st.session_state.review, st.session_state.destination, st.session_state.get('approval'), context, tuple(st.session_state.rules), ignore_values=st.session_state.generated_values)
    except Exception:
        return Decision('BLOCK', False, (), ('Validation unavailable',), 'Check privacy again.')


def acknowledge():
    st.session_state.pop('copy_ready', None)
    st.session_state.approval = check().fingerprint if st.session_state.confirm else None


def fix(index=None):
    invalidate()
    try:
        suggestions, mapping = suggest_fixes(st.session_state.review, tuple(st.session_state.rules), st.session_state.mapping, style=st.session_state.style, ignore_values=st.session_state.generated_values)
        selected = [s for s in suggestions if POLICIES[st.session_state.destination].get(s.finding.category, 'BLOCK') != 'ALLOW'] if index is None else [suggestions[index]]
        st.session_state.review = apply_fixes(st.session_state.review, selected)
        st.session_state.generated_values = list(set(st.session_state.generated_values) | {s.replacement for s in selected})
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


def restore():
    st.session_state.restored_reply = restore_reply(st.session_state.ai_reply, st.session_state.mapping)


def prepare_copy():
    decision = check()  # Never trust a previous button-enabled state.
    st.session_state.copy_ready = decision.fingerprint if decision.accepted else None


def render():
    initialize()
    st.info('Your text is processed by the server running this app. On the public demo that is a remote server — use fictional text. For real messages, run PrivacyGate locally (see README).')
    st.html('<nav class="pg-nav"><strong>PrivacyGate</strong><span>Review before sharing</span></nav><div class="pg-intro"><h1>Make sure your message<br>is ready to share.</h1><p>Find private details and fix them before copying.</p></div>')
    st.selectbox('Demo scenario', list(SCENARIOS), key='demo', on_change=load_demo)
    st.button('Try demo', on_click=load_demo, help='Load one fictional message. Nothing is scanned or shared automatically.')
    with st.container(key='workflow_columns'):
        left, right = st.columns(2, gap='large')
        with left, st.container(key='compose_panel'):
            st.subheader('01  Compose')
            st.text_area('Your message', key='source', height=230, on_change=source_changed, placeholder='Paste or write the message you want to review…')
            st.radio('Destination', list(POLICIES), key='destination', horizontal=True, on_change=invalidate, format_func=lambda d: {'AI Chatbot':'AI chatbot','Public Forum':'Public forum','Personal Notes (local demo)':'Personal notes'}[d])
            st.radio('Replace with:', ['Placeholder','Plain description','Fictional look-alike'], key='style', on_change=source_changed)
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
                    suggestions, mapping = suggest_fixes(st.session_state.review, tuple(st.session_state.rules), st.session_state.mapping, style=st.session_state.style, ignore_values=st.session_state.generated_values)
                    st.session_state.mapping = mapping
                    title = 'Ready to copy' if decision.accepted else ('Some details need fixing' if decision.action == 'BLOCK' else 'Review the remaining warning')
                    st.html(f'<div class="pg-status {decision.action.lower() if not decision.accepted else "ready"}" role="status" aria-live="polite" aria-atomic="true">{escape(title)}</div>')
                    if decision.combination:
                        st.markdown('**Combined details · ' + ('Blocked' if POLICIES[st.session_state.destination]['COMBINED_IDENTIFIERS'] == 'BLOCK' else 'Review recommended') + '**')
                        st.caption('Together, these can identify you: ' + ' + '.join(CATEGORY_META[c]['label'].lower() for c in decision.combination) + '.')
                    if not suggestions:
                        st.caption('No supported sensitive patterns found. Detection can miss private details.')
                    with st.expander("Highlighted findings"):
                        st.html(findings_preview(st.session_state.review, [s.finding for s in suggestions]))
                    for i, s in enumerate(suggestions):
                        f = s.finding
                        action = POLICIES[st.session_state.destination].get(f.category, 'BLOCK')
                        label = {'BLOCK': 'Blocked', 'WARN': 'Review recommended', 'ALLOW': 'Optional'}[action]
                        st.markdown(f'**{CATEGORY_META.get(f.category, DEFAULT_META)["label"]} · {label}**')
                        st.caption(CATEGORY_META.get(f.category, DEFAULT_META)['reason'])
                        st.caption(f'{action.title()} under the {st.session_state.destination} policy.' + (' Keep only after acknowledging the warning below.' if action == 'WARN' else ''))
                        # Native text rendering escapes the matched value.
                        st.text(f'Replace {masked(f.matched_text) if f.category == "SECRET" else f.matched_text} with {s.replacement}')
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
            st.caption('Two clicks: first re-check the current message on the server, then grant browser clipboard access with a fresh click.')
            st.button('Step 1 · Final check', disabled=not decision.accepted, on_click=prepare_copy, type='primary')
            if decision.accepted and st.session_state.get('copy_ready') == decision.fingerprint:
                render_copy(st.session_state.review, decision.fingerprint)
    if st.session_state.scanned:
        st.subheader('03 Restore AI reply (optional)')
        st.text_area('Paste the AI reply', key='ai_reply')
        st.button('Restore my details', on_click=restore)
        st.caption('Restoring happens in this session only. Share only the revised text if you want to keep the original details out of the AI conversation.')
        if 'restored_reply' in st.session_state:
            st.code(st.session_state.restored_reply, language=None)
    available = os.environ.get('PRIVACYGATE_NER') != '0' and ner_engine.ner_status()[0] == 'available'
    if not available:
        st.warning('Name/place detection is unavailable right now — names, schools and cities were NOT checked.')
    st.caption('Checked: patterns ✓ · names/places ' + ('✓' if available else '✗') if st.session_state.scanned else 'Check privacy to scan this message.')
    st.button('Clear', on_click=clear)
    st.caption('Text is processed on the server hosting this app · No external scanning API')
    with st.expander('About privacy'):
        st.write('When Streamlit runs on your computer, processing stays local. A remote deployment sends your text to that host. No external scanning API or message storage is used.')
        st.write('This checks selected patterns and optional model findings under your selected destination policy. It can miss private information. You can manually copy unreviewed text; PrivacyGate cannot protect sharing outside this workflow. Clear removes session-held text, not clipboard contents or browser history.')

    with st.expander('How it works'):
        st.markdown('Four layers check patterns and checksums, nearby context, model-based names/places/schools, and combinations of identifying details. Model availability is shown above.\n\nBefore copying, the server re-checks the current text. Warning acknowledgement is tied to the exact text, destination, and rules. No message logging, persistent message storage, or outside scanning APIs; text and mappings live in this session. Hosted processing happens on the remote server.\n\nDetection can miss personal stories, nicknames, and images. Copying outside this app bypasses its checks. No match is not a privacy guarantee.\n\n[See detection coverage](https://github.com/Microsoft666666/privacygate#what-it-detects)')
