from html.parser import HTMLParser
import pytest
from components.inspector import original_preview, outgoing_preview, occurrence_count
from components.evidence import display_metrics, negative_pass_rate
from detector import Finding, SensitivePhrase, detect
from evaluation import NEGATIVE_CONTROLS, evaluate
from policy import POLICIES


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.attributes = []
    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attributes.extend(attrs)


@pytest.mark.parametrize('payload', ['<script>alert(1)</script>', '<img src=x onerror="alert(1)">',
                                     '<svg onload=alert(1)>', '\" onmouseover=\"x & < >',
                                     '</mark><iframe src="https://example.com"></iframe>'])
def test_previews_escape_every_user_supplied_fragment(payload):
    text = payload + ' alex@example.com'
    for html in (original_preview(text, detect(text), POLICIES['AI Chatbot']),
                 original_preview(text, detect(text), POLICIES['AI Chatbot'], True),
                 outgoing_preview(text)):
        parser = Tags()
        parser.feed(html)
        assert set(parser.tags) <= {'div', 'mark', 'span'}
        assert all(name == 'class' for name, _ in parser.attributes)
        assert payload not in html


def test_manual_values_and_category_labels_are_escaped():
    text = '<img src=x> & "secret"'
    found = detect(text, (SensitivePhrase(text),))
    assert '<img' not in original_preview(text, found, POLICIES['AI Chatbot'], True)
    assert text not in original_preview(text, found, POLICIES['AI Chatbot'])


def test_default_preview_masks_matches_and_marks_severity_with_words():
    text = 'alex@example.com; 949-555-0134'
    preview = original_preview(text, detect(text), POLICIES['AI Chatbot'])
    assert 'alex@example.com' not in preview and '949-555-0134' not in preview
    assert 'Review required' in preview and 'Cannot send' in preview
    assert 'alex@example.com' in original_preview(text, detect(text), POLICIES['AI Chatbot'], True)


def test_preview_rejects_stale_offsets_and_counts_literal_overlaps():
    with pytest.raises(ValueError):
        original_preview('changed', detect('alex@example.com'), {})
    assert occurrence_count('a.* a.*', 'a.*') == 2
    assert occurrence_count('aaaa', 'aaa') == 2
    assert occurrence_count('Alex Chen', 'alex chen') == 0
    assert occurrence_count('abc', '') == 0


def test_negative_metrics_keep_raw_convention_but_present_na():
    report = evaluate(NEGATIVE_CONTROLS)
    assert report['precision'] == report['recall'] == report['f1'] == 0
    assert all(v == 'N/A — no positive cases' for v in display_metrics(report).values())
    assert negative_pass_rate(report) == 1
    report['cases'][0]['result'] = 'FAIL'
    report['fp'] = 1
    assert negative_pass_rate(report) == .9
    assert display_metrics(report)['precision'] == 'N/A — no positive cases'


def test_percentage_presentation_is_readable():
    assert display_metrics({'tp':24, 'fn':2, 'precision':.96, 'recall':24/26, 'f1':48/51}) == {
        'precision':'96.0%', 'recall':'92.3%', 'f1':'94.1%'}
