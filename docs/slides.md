---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { background: #f6f5f0; color: #172b25; font-family: Arial, sans-serif; font-size: 30px; padding: 64px 78px; }
  h1 { color: #173f32; font-size: 52px; line-height: 1.12; letter-spacing: -1px; }
  h2 { color: #173f32; font-size: 42px; }
  strong { color: #17664e; }
  table { font-size: 27px; width: 100%; }
  th { background: #e2e9e1; }
  td, th { padding: 14px 18px; }
  blockquote { border-left: 5px solid #17664e; color: #304c40; }
  small { font-size: 22px; }
  section::after { color: #53675d; }
---

# PrivacyGate

Catch the overshare before you hit send.

[TODO: student name / team]

<!-- Draft: confirm official rubric and presentation time limit before use. -->

---

# Private details can travel with a useful question

An essay can include a name, school and city.

A debugging snippet can include an access key.

**The writer needs a chance to review those details.**

<!-- Intended users: students, with teachers and parents as potential supporters. No prevalence, interview, or adoption statistic is claimed. Student: explain your real inspiration. -->

---

# The review workflow

1. Load a fictional essay or coding question.
2. See the flagged details and their reasons.
3. Apply replacements and check the current text.
4. Copy it, then optionally restore a pasted reply.

<small>Live demo uses fictional data. Hosted processing is remote.</small>

<!-- Follow docs/DEMO_SCRIPT.md. Extension demonstration is conditional on completed live-site QA; do not imply that it runs the name model. -->

---

# Four detection layers

**Patterns + checksums** for structured details

**Context rules** for birth dates and labelled IDs

**Presidio + spaCy** for names, schools and places

**Combination risk** when identifying details co-occur

<!-- Source: detector.py, recognizers/, policy.py. NER is an installed English model, not a model trained by this project. Combination risk is a heuristic, not a measured identity probability. -->

---

# Approval applies to the current message

The server detects again before copy.

Editing the text or changing the destination revokes approval.

Unknown categories and validation errors block the action.

<small>Copying outside the app bypasses this workflow.</small>

<!-- Show submission_service.evaluate_submission and policy.review_fingerprint. Evidence: tests/test_submission_service.py and test_server_copy_callback_cannot_bypass_block in tests/test_simple_app.py. -->

---

# Performance depends on the dataset

| Detector | Hand-authored: 60 | External: 1,000 |
| --- | --- | --- |
| Frozen v2 | 0.475 | 0.294 |
| Expanded patterns | 0.861 | 0.324 |
| Patterns + NER | 0.966 | 0.377 |

<small>Exact-span F1. Synthetic data; not real-world accuracy.<br>External English validation sample, fixed seed. Full counts and limitations: docs/benchmark.md.</small>

<!-- Values copied by script from docs/benchmark_metrics.json. External data: AI4Privacy pii-masking-300k, academic/non-commercial use; https://huggingface.co/datasets/ai4privacy/pii-masking-300k. Entity definitions and span boundaries differ. Report both good and poor results. -->

---

# A review flow built around the writer

| Approach | Main role |
| --- | --- |
| PrivacyGate | Student review, destination rules and reversible fixes |
| Presidio | Detection and anonymization building blocks |
| PrivyGate | Organization-facing redaction and LLM processing |
| Manual review | The writer's own judgment and edits |

<!-- Sources: https://presidio.dataprivacystack.org/ and https://github.com/EuroShield-AI/PrivyGate, checked 2026-11-15. PrivacyGate uses Presidio. No competitor performance comparison was run; browser interception and API-base-URL claims for PrivyGate are unverified. -->

---

# A privacy check has limits

Names can be missed or wrongly flagged.

Stories, nicknames and images need more work.

The public demo receives text on a remote host.

The extension beta depends on changing site editors.

**No match is not a privacy guarantee.**

<!-- The extension has no NER; it cannot prevent the host page from reading its composer or control every send path. Clear removes session state, not clipboard/history or forensic memory traces. -->

---

# Next validation steps

Verify the extension on all three supported sites.

Measure cold start and hosted resource use.

Expand independent multilingual and contextual evaluation.

Test fictional workflows with consenting users.

<!-- These are planned activities, not completed user research or deployment certification. -->

---

# Thank you

**Catch the overshare before you hit send.**

[Project repository](https://github.com/Microsoft666666/privacygate)

<small>OpenAI Codex assisted with code, tests and drafts.<br>[TODO: student — describe your own contribution honestly.]</small>

<!-- Be ready to open docs/QA_PREP.md and explain a specific function. Confirm authorship, license, rubric and timing before presentation. -->
