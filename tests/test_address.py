import pytest
from detector import detect

@pytest.mark.parametrize('text,value',[('I live at 123 Main St, Irvine, CA 92618.','123 Main St, Irvine, CA 92618'),('Apt 4B, 77 Ocean View Dr','77 Ocean View Dr')])
def test_address_spans(text,value):
    fs=[f for f in detect(text) if f.category=='STREET_ADDRESS']
    assert len(fs)==1 and fs[0].matched_text==value

@pytest.mark.parametrize('text',['We grew 25 Tomato Plants','Route 66 trip','Main Street businesses donated'])
def test_address_negatives(text):
    assert 'STREET_ADDRESS' not in {f.category for f in detect(text)}
