from pathlib import Path
from streamlit.testing.v1 import AppTest
from suggestions import suggest_fixes, apply_fixes

APP = str(Path(__file__).resolve().parents[1] / 'app.py')

def button(app,label):
    return next(b for b in app.button if b.label==label)

def start():
    app=AppTest.from_file(APP,default_timeout=15).run()
    button(app,'Try demo').click().run()
    button(app,'Check privacy').click().run()
    assert not app.exception
    return app

def test_focused_ui_and_blocked_copy():
    app=start()
    assert not app.tabs
    assert len([b for b in app.button if b.label=='Try demo'])==1
    assert len([b for b in app.button if b.label=='Check privacy'])==1
    assert not any('Submit' in b.label or 'simulation' in b.label for b in app.button)
    assert button(app,'Copy reviewed message').disabled
    assert any('Blocked' in m.value for m in app.markdown)
    assert any('Review recommended' in m.value for m in app.markdown)

def test_individual_fix_warn_ack_and_exact_copy():
    app=start()
    source=app.session_state['source']
    app.button(key='fix_1').click().run()
    assert '[PHONE_1]' in app.session_state['review']
    assert app.session_state['source']==source
    assert button(app,'Copy reviewed message').disabled
    app.checkbox(key='confirm').check().run()
    assert not button(app,'Copy reviewed message').disabled
    button(app,'Copy reviewed message').click().run()
    assert app.session_state['copy_ready']
    app.text_area(key='review').set_value('Call 949-555-0134').run()
    assert button(app,'Copy reviewed message').disabled
    assert 'copy_ready' not in app.session_state
    assert not app.exception

def test_batch_fix_manual_edit_and_clear():
    app=start()
    button(app,'Apply all recommended fixes').click().run()
    assert '[EMAIL_1]' in app.session_state['review']
    assert '[PHONE_1]' in app.session_state['review']
    assert not button(app,'Copy reviewed message').disabled
    app.text_input(key='manual_input').set_value('Alex').run()
    button(app,'Protect this phrase').click().run()
    assert button(app,'Copy reviewed message').disabled
    app.button(key='fix_0').click().run()
    assert '[MANUAL_CONFIDENTIAL_1]' in app.session_state['review']
    button(app,'Clear').click().run()
    assert app.session_state['source']==app.session_state['review']==''
    assert app.session_state['rules']==[]
    assert app.session_state['mapping']=={}
    assert not app.exception

def test_source_edit_revokes_copy_and_harmless_is_not_guaranteed():
    app=start()
    button(app,'Apply all recommended fixes').click().run()
    button(app,'Copy reviewed message').click().run()
    app.text_area(key='source').set_value('Community garden').run()
    assert not app.session_state['scanned']
    assert 'copy_ready' not in app.session_state
    button(app,'Check privacy').click().run()
    assert any('Detection can miss' in c.value for c in app.caption)
    assert not app.exception

def test_sequential_fixes_preserve_distinct_and_repeated_tokens():
    text='a@example.com b@example.com a@example.com'
    fixes,mapping=suggest_fixes(text)
    text=apply_fixes(text,[fixes[0]])
    fixes,mapping=suggest_fixes(text,mapping=mapping)
    result=apply_fixes(text,fixes)
    assert result=='[EMAIL_1] [EMAIL_2] [EMAIL_1]'

def test_existing_tokens_are_not_reused():
    fixes,_=suggest_fixes('[EMAIL_1] a@example.com')
    assert fixes[0].replacement=='[EMAIL_2]'

def test_server_copy_callback_cannot_bypass_block():
    app=start()
    # Forged stale client approval must not enable the public copy action.
    app.session_state['copy_ready']='forged'
    app.run()
    assert button(app,'Copy reviewed message').disabled
    app.text_area(key='review').set_value('alex@example.com').run()
    assert button(app,'Copy reviewed message').disabled
    app.checkbox(key='confirm').check().run()
    button(app,'Copy reviewed message').click().run()
    approved=app.session_state['copy_ready']
    app.text_area(key='review').set_value('other@example.com').run()
    assert 'copy_ready' not in app.session_state
    assert button(app,'Copy reviewed message').disabled
    assert approved
