import pytest
from detector import SensitivePhrase, detect, mark_phrase
from policy import POLICIES
from redaction import redact
from submission_service import evaluate_submission


@pytest.mark.parametrize('value', ['192.0.2.1', '198.51.100.255', '203.0.113.0', '0.0.0.0', '255.255.255.255'])
def test_ipv4_offsets(value):
    text = f'Network ({value}).'
    found, = detect(text)
    assert found.category == 'IPV4'
    assert text[found.start:found.end] == value


@pytest.mark.parametrize('value', ['256.0.0.1', '192.0.2.999', '01.2.3.4', '1.2.3', '1.2.3.4.5', 'x192.0.2.1', '192.0.2.1x'])
def test_ipv4_invalid_boundaries(value):
    assert not detect(value)


def test_manual_name_all_or_chosen_occurrences():
    text = 'Alex Chen met Alex Chen. Alex stayed.'
    rule = mark_phrase(text, 'Alex Chen', 'MANUAL_IDENTIFIER')
    found = detect(text, (rule,))
    assert len(found) == 2
    assert all(f.origin == 'user-provided' for f in found)
    assert redact(text, found).text == '[MANUAL_IDENTIFIER_1] met [MANUAL_IDENTIFIER_1]. Alex stayed.'
    assert redact(text, found, [0]).text == '[MANUAL_IDENTIFIER_1] met Alex Chen. Alex stayed.'
    assert not evaluate_submission(text, 'AI Chatbot', sensitive_phrases=(rule,)).accepted
    assert evaluate_submission(redact(text, found).text, 'AI Chatbot', sensitive_phrases=(rule,)).accepted


@pytest.mark.parametrize('phrase,category', [('', 'MANUAL_IDENTIFIER'), ('missing', 'MANUAL_IDENTIFIER'), ('Alex', 'UNKNOWN')])
def test_invalid_marks(phrase, category):
    with pytest.raises(ValueError):
        mark_phrase('Alex Chen', phrase, category)


def test_keywords_literal_overlap_unicode_and_policy():
    rules = (SensitivePhrase('Project.*'), SensitivePhrase('Project.* Falcon'))
    text = '你好Project.* Falcon! Project.*'
    found = detect(text, rules)
    assert len(found) == 2
    assert found[0].matched_text == 'Project.* Falcon'
    assert redact(text, found).text == '你好[USER_PHRASE_1]! [USER_PHRASE_2]'
    for dest in POLICIES:
        assert not evaluate_submission(text, dest, sensitive_phrases=rules).accepted


def test_manual_overlaps_auto_without_leaking_neighbors():
    text = 'Contact alex@example.com now.'
    rule = SensitivePhrase('Contact alex@example.com', 'MANUAL_CONFIDENTIAL')
    assert redact(text, detect(text, (rule,))).text == '[MANUAL_CONFIDENTIAL_1] now.'


def test_manual_changes_invalidate_warning_confirmation():
    text = 'alex@example.com'
    initial = evaluate_submission(text, 'AI Chatbot')
    changed = evaluate_submission(text, 'AI Chatbot', initial.fingerprint,
                                  sensitive_phrases=(SensitivePhrase('unused'),))
    assert not changed.accepted


def test_redaction_modes_and_mask_is_never_silently_allowed():
    text = '你好(alex@example.com)!'
    found = detect(text)
    masked = redact(text, found, mode='Mask').text
    assert masked == '你好([PARTIAL_EMAIL_1: a•••m])!'
    assert evaluate_submission(masked, 'Public Forum').action == 'BLOCK'
    decision = evaluate_submission(masked, 'AI Chatbot')
    assert decision.action == 'WARN' and not decision.accepted
    assert evaluate_submission(masked, 'AI Chatbot', decision.fingerprint).accepted
    assert redact(text, found, mode='Remove').text == '你好()!'
    assert redact('alex@example.com', detect('alex@example.com'), mode='Remove').text == ''


def test_unknown_mode_rejected():
    with pytest.raises(ValueError):
        redact('', [], mode='unknown')
