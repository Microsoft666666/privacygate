import pytest
from detector import detect

@pytest.mark.parametrize('text',['+44 20 7946 0958','+86 138 0013 8000','13800138000'])
def test_international_phones(text):
    assert any(f.category == 'INTL_PHONE' and f.matched_text == text for f in detect(text))

@pytest.mark.parametrize('text',['+1 949 555 0134','12345678901','Order 1380013800'])
def test_not_international(text):
    assert not any(f.category == 'INTL_PHONE' for f in detect(text))
