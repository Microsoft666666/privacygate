# Evaluation methodology

The report compares the frozen v2 implementation (`benchmarks/detector_v2.py`), current patterns/context/checksums with NER disabled, and the current detector with installed English NER enabled. All modes receive identical independently authored annotations: original 37, adversarial 52, and realistic 60 messages. The realistic set has four scenarios and at least 20 negatives. Cases that need NER are tagged but are **not removed** from regex-only scoring.

A span is `(category, start, end)`. Exact matching requires identical category and character boundaries. Duplicate spans are counted with multiset semantics. Precision = TP/(TP+FP); recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN). A zero denominator yields zero. Per-category and overall totals are generated directly by code. Negative-message FPR is the fraction of messages with no annotations that produce any finding. It is not a token-level error rate.

The original datasets stay frozen. New model detections can be counted as false positives where the old annotations omitted names or places. This is disclosed rather than changing ground truth to improve scores. The realistic cases are synthetic regression examples, not a representative survey.

The external benchmark uses a fixed seeded sample of 1,000 English validation rows from AI4Privacy. It reports exact and maximum one-to-one same-category overlap matching. Read the [schema, mapping and license notes](ai4privacy.md). Unmapped annotations remain explicitly not covered; predictions without matched covered annotations count as false positives. Differing entity definitions and span boundaries limit comparability.

Latency uses fixed fictional 500- and 2,000-character messages, five warmups and 50 timed runs per mode/length. p50 is the median; p95 is the nearest-rank 95th percentile. Measurements exclude model startup, UI, network, and clipboard operations. The 300 ms p95 target is reported, not enforced as a brittle timing test. CPU/environment and dependency versions accompany the numbers.

Only aggregate external metrics are committed. Raw download caches stay ignored. No real user messages are used. The browser extension is assessed separately with shared fixtures and manual site QA; Python detector results do not prove send interception works on live sites.
