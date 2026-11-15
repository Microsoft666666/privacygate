import pytest
from detector import Finding, detect, luhn_valid, resolve_overlaps


@pytest.mark.parametrize('value', ['949-555-0134', '(949) 555-0134', '9495550134', '+1 949 555 0134', '1-949-555-0134', '949.555.0134'])
def test_phone_formats(value):
    assert [(f.category, f.matched_text) for f in detect(value)] == [('US_PHONE', value)]


@pytest.mark.parametrize('value', ['alex@example.com', 'alex+tag@example.org', 'alex@school.example.com'])
def test_email_boundaries(value):
    text = f'你好 ({value}).'
    assert [(f.category, f.matched_text, f.start, f.end) for f in detect(text)] == [('EMAIL', value, 4, 4 + len(value))]


@pytest.mark.parametrize('value', ['000-12-3456', '000 12 3456'])
def test_ssn_is_format_only(value):
    finding, = detect(value)
    assert finding.category == 'SSN'
    assert 'does not confirm' in finding.reason


@pytest.mark.parametrize('value', ['4111111111111111', '4111 1111 1111 1111', '4111-1111-1111-1111', '5555555555554444'])
def test_card(value):
    assert luhn_valid(value)
    assert [f.category for f in detect(value)] == ['PAYMENT_CARD']


@pytest.mark.parametrize('value', ['', '2026-11-15', '$19.99', '4111 1111 1111 1112', '12345678901234567890', '0000000000000000', 'alex@', 'alex@example', '000-12 3456', '49495550134000'])
def test_benign_and_malformed(value):
    assert not detect(value)


def test_mixed_offsets_and_sorting():
    text = '你好 alex@example.com\n949-555-0134; 000-12-3456; 4111 1111 1111 1111.'
    found = detect(text)
    assert [f.category for f in found] == ['EMAIL', 'US_PHONE', 'SSN', 'PAYMENT_CARD']
    assert all(text[f.start:f.end] == f.matched_text for f in found)
    assert found == sorted(found, key=lambda f: (f.start, f.end, f.category))


def test_overlap_priority_and_longer_span():
    phone = Finding('US_PHONE', 0, 10, '9495550134', 'test')
    card = Finding('PAYMENT_CARD', 0, 16, '9495550134000000', 'test')
    short = Finding('PAYMENT_CARD', 0, 13, '9495550134000', 'test')
    assert resolve_overlaps([phone, short, card, card]) == [card]
