import pytest
from detector import detect, luhn_valid
from recognizers.national_id import valid

@pytest.mark.parametrize('value',['110105200001010016','440304201003150026'])
def test_valid(value):
    assert valid(value)
    assert [f.category for f in detect(value,ner=False)] == ['NATIONAL_ID']

@pytest.mark.parametrize('value',['110105200001010017','110105200013010016','A110105200001010016'])
def test_invalid(value):
    assert not any(f.category == 'NATIONAL_ID' for f in detect(value,ner=False))

def test_priority_over_card():
    # Generate a fictional checksum intersection instead of assuming one.
    for serial in range(1000):
        stem = '11010520000101' + f'{serial:03d}'
        from recognizers.national_id import WEIGHTS
        value = stem + '10X98765432'[sum(int(d)*w for d,w in zip(stem,WEIGHTS)) % 11]
        if value.isdigit() and luhn_valid(value):
            assert [f.category for f in detect(value,ner=False)] == ['NATIONAL_ID']
            return
    pytest.fail('No checksum intersection fixture found')
