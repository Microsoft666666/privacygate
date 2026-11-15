import pytest
from detector import Finding, detect
from redaction import redact


def test_stable_repeated_values_and_selection():
    text = 'alex@example.com; other@example.com; alex@example.com'
    findings = detect(text)
    assert redact(text, findings).text == '[EMAIL_1]; [EMAIL_2]; [EMAIL_1]'
    assert redact(text, findings, [1]).text == 'alex@example.com; [EMAIL_2]; alex@example.com'
    assert redact(text, findings, []).text == text


def test_offsets_preserve_neighbors():
    text = '你好(alex@example.com),\ncall 949-555-0134!'
    result = redact(text, detect(text))
    assert result.text == '你好([EMAIL_1]),\ncall [PHONE_1]!'
    assert not detect(result.text)
    assert result.replacements == 2


def test_overlap_replaced_once():
    text = '4111111111111111'
    findings = [Finding('US_PHONE', 0, 10, text[:10], ''), Finding('PAYMENT_CARD', 0, 16, text, '')]
    assert redact(text, findings).text == '[PAYMENT_CARD_1]'


def test_stale_spans_rejected():
    with pytest.raises(ValueError):
        redact('changed', detect('alex@example.com'))


def test_invalid_selection():
    with pytest.raises(ValueError):
        redact('', [], [0])
