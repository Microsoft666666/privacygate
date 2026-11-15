import pytest
import policy
import submission_service as service
from policy import review_fingerprint


def test_blocked_direct_call_and_metadata_only():
    text = '949-555-0134'
    result = service.evaluate_submission(text, 'AI Chatbot', review_fingerprint(text, 'AI Chatbot'))
    assert not result.accepted
    assert result.action == 'BLOCK'
    assert result.categories == ('US_PHONE',)
    assert text not in repr(result)


@pytest.mark.parametrize('destination', ['unknown', None, [], ''])
def test_invalid_destination_fails_closed(destination):
    result = service.evaluate_submission('hello', destination)
    assert not result.accepted
    assert 'validation unavailable' in result.message


def test_scanner_error_fails_closed_without_echo(monkeypatch):
    def broken(text):
        raise RuntimeError(text)
    monkeypatch.setattr(service, 'detect', broken)
    result = service.evaluate_submission('secret input', 'AI Chatbot')
    assert not result.accepted
    assert 'secret input' not in repr(result)


@pytest.mark.parametrize('rules', [{}, {'EMAIL': 'TYPO'}, None])
def test_invalid_policy_fails_closed(monkeypatch, rules):
    monkeypatch.setitem(policy.POLICIES, 'AI Chatbot', rules)
    assert not service.evaluate_submission('hello', 'AI Chatbot').accepted


def test_changed_policy_and_version_invalidate_acknowledgement(monkeypatch):
    text = 'alex@example.com'
    ack = review_fingerprint(text, 'AI Chatbot')
    assert service.evaluate_submission(text, 'AI Chatbot', ack).accepted
    monkeypatch.setattr(policy, 'POLICY_VERSION', 'changed')
    assert not service.evaluate_submission(text, 'AI Chatbot', ack).accepted
    ack = review_fingerprint(text, 'AI Chatbot')
    monkeypatch.setitem(policy.POLICIES['AI Chatbot'], 'US_PHONE', 'WARN')
    assert not service.evaluate_submission(text, 'AI Chatbot', ack).accepted


def test_edited_text_and_context_rejected():
    text = 'alex@example.com'
    ack = review_fingerprint(text, 'AI Chatbot', 'first')
    assert not service.evaluate_submission(text + '.', 'AI Chatbot', ack, 'first').accepted
    assert not service.evaluate_submission(text, 'AI Chatbot', ack, 'changed').accepted
    assert not service.evaluate_submission(text, 'Public Forum', ack, 'first').accepted
