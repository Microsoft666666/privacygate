import pytest
from detector import Finding, detect
from policy import evaluate_policy, review_fingerprint, submit_simulated
from redaction import redact


def test_destination_rules():
    assert evaluate_policy(detect('alex@example.com'), 'AI Chatbot').overall_action == 'WARN'
    assert evaluate_policy(detect('949-555-0134'), 'AI Chatbot').overall_action == 'BLOCK'
    assert evaluate_policy(detect('alex@example.com'), 'Public Forum').overall_action == 'BLOCK'
    assert evaluate_policy(detect('alex@example.com'), 'Personal Notes (local demo)').overall_action == 'ALLOW'


def test_blocked_path_cannot_be_overridden():
    text = '949-555-0134'
    assert not submit_simulated(text, 'AI Chatbot', review_fingerprint(text, 'AI Chatbot')).accepted


def test_redaction_changes_decision():
    text = 'alex@example.com; 949-555-0134'
    findings = detect(text)
    partial = redact(text, findings, [1]).text
    assert evaluate_policy(detect(partial), 'AI Chatbot').overall_action == 'WARN'
    cleaned = redact(text, findings).text
    assert submit_simulated(cleaned, 'Public Forum').accepted


def test_warning_requires_current_confirmation():
    text = 'alex@example.com'
    assert not submit_simulated(text, 'AI Chatbot').accepted
    assert submit_simulated(text, 'AI Chatbot', review_fingerprint(text, 'AI Chatbot')).accepted


@pytest.mark.parametrize('change', ['destination', 'output', 'source', 'selection'])
def test_changes_invalidate_approval(change):
    text, destination, context = 'alex@example.com; 949-555-0134', 'Personal Notes (local demo)', 'source one, selected 1'
    approval = review_fingerprint(text, destination, context)
    if change == 'destination':
        destination = 'AI Chatbot'
        text = 'alex@example.com'
    elif change == 'output':
        text += ' edited'
    else:
        context = change + ' changed'
    assert not submit_simulated(text, destination, approval, context).accepted


def test_destination_alone_invalidates_fingerprint():
    assert review_fingerprint('alex@example.com', 'AI Chatbot') != review_fingerprint('alex@example.com', 'Public Forum')


def test_unknown_finding_fails_closed():
    assert evaluate_policy([Finding('UNKNOWN', 0, 1, 'x', '')], 'AI Chatbot').overall_action == 'BLOCK'


def test_unknown_destination_rejected():
    assert not submit_simulated('hello', 'unknown').accepted
