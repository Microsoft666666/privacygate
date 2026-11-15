import pytest
from benchmarks.compare import comparison_reports
from detector import detect, luhn_valid
from redaction import redact


@pytest.mark.parametrize('text,expected', [
    ('Version 1.2.3.4', False), ('Software version: 2.3.4.5', False),
    ('v 1.2.3.4', False), ('v1.2.3.4', False), ('Build 1.2.3.4', False),
    ('Server IP: 1.2.3.4', True), ('Visit 192.168.1.1', True),
    ('IP version 1.2.3.4', True), ('Router version 192.0.2.1', True),
    ('Version notes. Host IP: 192.0.2.1', True),
    ('2026.11.15.1', False), ('1.2.3.4.5', False),
    ('192.0.2.256', False), ('Version 1.2.3.4\n192.0.2.1', True),
])
def test_ipv4_version_context(text, expected):
    assert any(f.category == 'IPV4' for f in detect(text)) == expected


def test_executable_regression_gate():
    reports = comparison_reports()
    baseline = reports['Original 37']
    assert baseline['v2']['fp'] == 2
    assert baseline['current']['fp'] == 1
    for result in reports.values():
        assert result['current']['tp'] >= result['v2']['tp']
        assert result['current']['fn'] <= result['v2']['fn']
        assert result['current']['fp'] < result['v2']['fp']


@pytest.mark.parametrize('text,category', [('4222222222222', 'PAYMENT_CARD'),
                                          ('4000000000000000006', 'PAYMENT_CARD'),
                                          ('000-00-0000', 'SSN')])
def test_format_boundaries(text, category):
    assert [f.category for f in detect(text)] == [category]


@pytest.mark.parametrize('text', ['411111111111', '41111111111111111111', '４１１１１１１１１１１１１１１１', '0000000000000000'])
def test_invalid_card_boundaries(text):
    assert not luhn_valid(text)


def test_unicode_whitespace_limit_is_explicit():
    assert not detect('949\u00a0555\u00a00134')
    assert detect('你好949-555-0134界')[0].matched_text == '949-555-0134'


def test_long_input_repeated_spans_and_redaction():
    text = ('Fictional garden prose. ' * 500) + ('alex@example.com; ' * 100)
    found = detect(text)
    assert len(found) == 100
    assert all(text[f.start:f.end] == f.matched_text for f in found)
    output = redact(text, found).text
    assert output.count('[EMAIL_1]') == 100
    assert not detect(output)
