"""Exercise Streamlit's real widget/session flow without a network destination."""
from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'tests' / 'legacy' / 'app_v3.py')


def button(app, label):
    return next(widget for widget in app.button if widget.label == label)


def start_student():
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert not app.exception
    assert app.text_area(key='source').value == ''
    button(app, 'Student essay').click().run()
    button(app, 'Check privacy').click().run()
    assert not app.exception
    return app


def test_block_redact_submit_then_edit():
    app = start_student()
    assert button(app, 'Submit to simulated destination').disabled
    assert len(app.checkbox) == 2
    button(app, 'Redact selected').click().run()
    assert '[EMAIL_1]' in app.text_area(key='review').value
    assert not button(app, 'Submit to simulated destination').disabled
    button(app, 'Submit to simulated destination').click().run()
    assert 'Accepted by policy' in app.success[0].value
    app.text_area(key='review').set_value('949-555-0134').run()
    assert button(app, 'Submit to simulated destination').disabled
    assert not app.success
    assert not app.exception


def test_warning_and_destination_invalidation():
    app = start_student()
    app.checkbox(key='finding_0').uncheck().run()
    button(app, 'Redact selected').click().run()
    assert button(app, 'Submit to simulated destination').disabled
    app.checkbox(key='confirm').check().run()
    button(app, 'Submit to simulated destination').click().run()
    assert app.success
    app.selectbox(key='destination').select('Public Forum').run()
    assert button(app, 'Submit to simulated destination').disabled
    assert not app.success
    app.selectbox(key='destination').select('AI Chatbot').run()
    assert not app.checkbox(key='confirm').value
    assert not app.exception


def test_source_selection_and_review_changes_reset_confirmation():
    app = start_student()
    app.selectbox(key='destination').select('Personal Notes (local demo)').run()
    app.checkbox(key='confirm').check().run()
    app.checkbox(key='finding_0').uncheck().run()
    assert not app.session_state['confirm']
    app.text_area(key='review').set_value('949-555-0134').run()
    app.checkbox(key='confirm').check().run()
    app.text_area(key='review').set_value('Call 949-555-0134 today').run()
    assert not app.checkbox(key='confirm').value
    app.text_area(key='source').set_value('New text').run()
    assert not app.session_state['scanned']
    assert app.session_state['review'] == ''
    assert not app.exception


def test_clear_removes_session_and_all_demos_work():
    app = start_student()
    button(app, 'Redact selected').click().run()
    button(app, 'Submit to simulated destination').click().run()
    button(app, 'Clear session').click().run()
    assert app.text_area(key='source').value == ''
    assert app.session_state['review'] == ''
    assert not app.success
    assert not app.checkbox
    for demo in ['Payment info', 'Harmless text']:
        button(app, demo).click().run()
        button(app, 'Check privacy').click().run()
        assert button(app, 'Submit to simulated destination').disabled == (demo == 'Payment info')
    assert not app.exception


def test_rejected_attempt_never_adds_outbox_and_approved_copy_is_gated():
    app = start_student()
    assert button(app, 'Prepare approved copy').disabled
    button(app, 'Test rejected attempt').click().run()
    assert 'outbox' not in app.session_state
    assert any('Not sent — policy blocked' in e.value for e in app.error)
    app.checkbox(key='finding_0').uncheck().run()
    button(app, 'Redact selected').click().run()
    button(app, 'Test rejected attempt').click().run()
    assert 'outbox' not in app.session_state
    assert button(app, 'Prepare approved copy').disabled
    app.checkbox(key='confirm').check().run()
    button(app, 'Prepare approved copy').click().run()
    assert app.session_state['approved_copy']
    button(app, 'Submit to simulated destination').click().run()
    receipt = app.session_state['outbox']
    assert receipt['text'] == app.text_area(key='review').value
    assert '949-555-0134' not in receipt['text']
    app.text_area(key='review').set_value('949-555-0134').run()
    assert 'approved_copy' not in app.session_state
    button(app, 'Test rejected attempt').click().run()
    assert app.session_state['outbox'] == receipt
    assert not app.success
    button(app, 'Reset simulation').click().run()
    assert 'outbox' not in app.session_state
    assert not app.exception


def test_manual_marking_repeated_name_and_mode_changes():
    app = start_student()
    app.text_area(key='source').set_value('Alex Chen met Alex Chen.').run()
    button(app, 'Check privacy').click().run()
    app.text_input(key='manual_input').set_value('Alex Chen').run()
    button(app, 'Protect this phrase').click().run()
    assert len(app.checkbox) == 2
    assert button(app, 'Submit to simulated destination').disabled
    button(app, 'Redact selected').click().run()
    assert app.text_area(key='review').value == '[MANUAL_IDENTIFIER_1] met [MANUAL_IDENTIFIER_1].'
    app.selectbox(key='mode').select('Mask').run()
    button(app, 'Redact selected').click().run()
    assert 'PARTIAL_MANUAL_IDENTIFIER' in app.text_area(key='review').value
    assert button(app, 'Submit to simulated destination').disabled
    app.checkbox(key='confirm').check().run()
    app.selectbox(key='mode').select('Remove').run()
    assert not app.session_state['confirm']
    button(app, 'Redact selected').click().run()
    assert app.text_area(key='review').value == ' met .'
    assert not app.exception


def test_custom_rules_clear_and_demo_reset():
    app = start_student()
    app.text_area(key='keywords').set_value('garden').run()
    assert len(app.checkbox) == 3
    button(app, 'Social post').click().run()
    assert app.selectbox(key='destination').value == 'Public Forum'
    assert app.text_area(key='keywords').value == ''
    assert app.session_state['manual_rules'] == []
    button(app, 'Check privacy').click().run()
    assert button(app, 'Submit to simulated destination').disabled
    button(app, 'Clear session').click().run()
    assert app.session_state['manual_rules'] == []
    assert app.session_state['keywords'] == ''
    assert 'outbox' not in app.session_state
    assert not app.exception


def test_one_primary_scan_and_empty_stale_states():
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert [b.label for b in app.button].count('Check privacy') == 1
    assert not any(b.label == 'Scan message' for b in app.button)
    assert button(app, 'Check privacy').disabled
    app.text_area(key='source').set_value('Fictional benign draft').run()
    assert not button(app, 'Check privacy').disabled
    assert any('Message changed' in c.value for c in app.caption)
    button(app, 'Check privacy').click().run()
    assert not button(app, 'Submit to simulated destination').disabled
    app.text_area(key='source').set_value('949-555-0134').run()
    assert not app.session_state['scanned']
    assert not any(b.label == 'Submit to simulated destination' for b in app.button)
    assert not app.exception


def test_live_redaction_choices_rebuild_output_and_revoke_ack():
    app = start_student()
    app.checkbox(key='finding_0').uncheck().run()
    assert '[PHONE_1]' in app.text_area(key='review').value
    assert 'alex@example.com' in app.text_area(key='review').value
    app.checkbox(key='confirm').check().run()
    app.checkbox(key='finding_1').uncheck().run()
    assert '949-555-0134' in app.text_area(key='review').value
    assert not app.session_state['confirm']
    assert button(app, 'Submit to simulated destination').disabled
    assert not app.exception


def test_navigation_and_fictional_failure_reproduction():
    app = start_student()
    source = app.session_state['source']
    app.session_state['navigation'] = 'Evaluation'
    app.run()
    assert not app.exception
    assert any('N/A — no positive cases' in c.value for c in app.caption)
    assert app.text_area(key='source').value == source
    app.button(key='failure_0').click().run()
    assert app.session_state['navigation'] == 'Workspace'
    assert app.session_state['source'] != source
    assert app.session_state['scanned']
    button(app, 'Privacy details').click().run()
    assert app.session_state['navigation'] == 'How it works'
    assert not app.exception


def test_reveal_state_clears_on_source_change_and_session_clear():
    app = start_student()
    button(app, 'Reveal original values').click().run()
    assert app.session_state['reveal_original']
    app.text_area(key='source').set_value('New draft').run()
    assert 'reveal_original' not in app.session_state
    button(app, 'Clear session').click().run()
    assert app.session_state['navigation'] == 'Workspace'
    assert app.session_state['review'] == ''
    assert not app.exception
