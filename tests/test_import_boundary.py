import subprocess
import sys
from pathlib import Path

def test_product_does_not_import_legacy():
    root = Path(__file__).parents[1]
    result = subprocess.run([sys.executable, '-c', "from streamlit.testing.v1 import AppTest; import sys; a=AppTest.from_file('app.py').run(); assert not a.exception; assert not any(k.startswith('legacy.') for k in sys.modules)"], cwd=root, capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
