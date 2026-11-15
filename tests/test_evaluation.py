from evaluation import DATASET, evaluate, score


def test_exact_matching_and_duplicate_predictions():
    a, b = ('EMAIL', 0, 4), ('SSN', 5, 16)
    metrics = score([a, a, ('SSN', 5, 15)], [a, b])
    assert (metrics.tp, metrics.fp, metrics.fn) == (1, 2, 1)
    assert metrics.precision == 1/3
    assert metrics.recall == 1/2


def test_zero_denominators():
    assert score([], []).precision == score([], []).recall == 0
    assert score([], [('EMAIL', 0, 5)]).fn == 1
    assert score([('EMAIL', 0, 5)], []).fp == 1


def test_dataset_is_annotated_and_evaluated():
    assert len(DATASET) >= 30
    assert all(0 <= start < end <= len(case.text) for case in DATASET for _, start, end in case.expected)
    report = evaluate()
    assert report['messages'] == len(DATASET)
    assert report['tp'] > 0
    assert report['fn'] >= 2  # Deliberately includes unsupported formats.
    assert report['tp'] + report['fn'] == sum(len(case.expected) for case in DATASET)
    assert evaluate([])['messages'] == 0


def test_extended_sets_counts_category_sums_and_f1():
    from evaluation import ADVERSARIAL, DATASET, NEGATIVE_CONTROLS, reports, Metrics
    assert len(DATASET) == 37
    assert len(ADVERSARIAL) >= 40
    assert len({c.text for c in ADVERSARIAL}) == len(ADVERSARIAL)
    for cases in (DATASET, ADVERSARIAL, NEGATIVE_CONTROLS):
        report = evaluate(cases)
        for key in ('tp', 'fp', 'fn'):
            assert report[key] == sum(v[key] for v in report['per_category'].values())
        assert report['tp'] + report['fn'] == sum(len(c.expected) for c in cases)
        assert sum(e['count'] for e in report['errors']) == report['fp'] + report['fn']
    assert evaluate(NEGATIVE_CONTROLS)['fp'] == 0
    assert len(reports()) == 3
    assert Metrics(1, 2, 1).f1 == 2/5
    assert Metrics(0, 0, 0).f1 == 0


def test_user_configured_category_evaluation_has_gold_coverage():
    from evaluation import ADVERSARIAL
    report = evaluate(ADVERSARIAL)
    for category in ('IPV4', 'USER_PHRASE', 'MANUAL_IDENTIFIER', 'MANUAL_ADDRESS', 'MANUAL_CONFIDENTIAL', 'PARTIAL_DETAIL'):
        assert report['per_category'][category]['tp'] > 0
