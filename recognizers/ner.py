"""Optional installed-only NER. Cache the engine, never messages or results."""
from contextvars import ContextVar
from functools import lru_cache
import importlib.util
import re

_FAILURE = ContextVar('privacygate_ner_failure', default=None)
REASON = 'Detected by a language model; it can be wrong. Check it yourself.'
SCHOOL = re.compile(r'\b(school|high|academy|university|college|middle|elementary|institute)\b', re.I)

@lru_cache(maxsize=1)
def _engine():
    # Presidio otherwise tries to download missing models at runtime.
    if importlib.util.find_spec('en_core_web_sm') is None:
        raise ImportError('Model is not installed')
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_analyzer.predefined_recognizers import SpacyRecognizer
    nlp = NlpEngineProvider(nlp_configuration={
        'nlp_engine_name': 'spacy',
        'models': [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}],
    }).create_engine()
    # Restrict the registry to the model; no API or URL-based recognizers.
    registry = RecognizerRegistry(recognizers=[SpacyRecognizer()])
    return AnalyzerEngine(nlp_engine=nlp, registry=registry, log_decision_process=False)


def ner_status():
    if _FAILURE.get():
        return ('unavailable', _FAILURE.get())
    try:
        _engine()
        return ('available', None)
    except Exception:
        _FAILURE.set('Name/place engine could not load.')
        return ('unavailable', _FAILURE.get())


def find(text):
    from detector import Finding
    if ner_status()[0] != 'available':
        return []
    try:
        results = _engine().analyze(text=text, language='en',
            entities=['PERSON', 'LOCATION', 'ORGANIZATION'], score_threshold=0.5)
        findings = []
        for result in results:
            value = text[result.start:result.end]
            category = result.entity_type
            if category == 'PERSON' and len(value) < 2:
                continue
            if category == 'ORGANIZATION':
                if not SCHOOL.search(value):
                    continue
                category = 'SCHOOL'
            if category in {'PERSON', 'LOCATION', 'SCHOOL'}:
                findings.append(Finding(category, result.start, result.end, value, REASON, 'model-based'))
        return findings
    except Exception:
        _FAILURE.set('Name/place analysis failed.')
        return []
