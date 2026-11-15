# Reproducing verification

Use Python 3.11 or 3.12 from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
PRIVACYGATE_NER=1 python -m pytest -q -m ner
node --test extension/tests/
python -m tools.export_policies
python -m tools.export_patterns
python -m pytest -q tests/test_extension_exports.py
python -m benchmarks.ai4privacy_eval --n 1000
python -m benchmarks.report
python -m streamlit run app.py --server.address 127.0.0.1
```

On Windows, activate with `.venv\Scripts\activate`; set `PRIVACYGATE_NER` using the shell's environment syntax. Node 20+ is required for extension tests. The test suite disables NER for existing deterministic tests; marked NER tests explicitly enable the installed model. Missing-model tests skip with an explicit reason. A release should run them with the model installed, not treat skips as evidence.

The external command downloads licensed synthetic data for academic/non-commercial use; see [AI4Privacy notes](ai4privacy.md). After the first successful download, an offline rerun is possible with `HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1` before the command. No dataset rows or caches belong in Git.

`docs/benchmark.md` and `docs/benchmark_metrics.json` are generated together. Never edit measured numbers by hand. `tests/test_benchmark_report.py` checks that the markdown matches its aggregate JSON. Regenerate after changing detector code. The external report is generated separately and should also be refreshed after detector changes.

CI runs Python 3.11/3.12 and the Node suite. Local test success does not establish that remote CI has run or the hosted app has redeployed. Complete [extension manual QA](../extension/QA.md) and the student checklist before presenting.
