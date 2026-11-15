import json
from pathlib import Path
from tools.export_policies import exported
from tools.export_patterns import exported as patterns
ROOT=Path(__file__).parents[1]/'extension'

def test_policy_exports_match_python():
    data=json.loads((ROOT/'policies.json').read_text())
    assert data == exported()
    assert (ROOT/'policies.js').read_text().split(' = ',1)[1].rstrip(';\n') == json.dumps(data,sort_keys=True,indent=2)

def test_pattern_export_matches_python():
    data=json.loads((ROOT/'patterns.js').read_text().split(' = ',1)[1].rstrip(';\n'))
    assert data == json.loads(json.dumps(patterns()))
