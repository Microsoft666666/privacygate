# Judge Q&A and code walkthrough

These are factual draft explanations of the current implementation. **[TODO: student — rewrite and practice in your own words. Do not claim you personally wrote or independently chose code that Codex produced.]** Use only claims you understand and can demonstrate. Competition timing/rubric still needs official confirmation.

## Short answers

**Why not just use Presidio?**

PrivacyGate does use Presidio with spaCy for names, places, and school-like organizations. It adds a student-facing review flow, destination rules, checksum/context recognizers, combination risk, reversible fixes, and final-check enforcement. Presidio itself already supports many detectors and anonymizers; do not describe it as incapable of those tasks. The difference here is the selected workflow and integration. See [recognizers/ner.py](../recognizers/ner.py) and [the sourced comparison](PITCH.md).

**Does my text leave my computer?**

- Public Streamlit demo: yes, the host receives and processes it. Use fictional text.
- Local Streamlit run: detection runs on the local server with installed dependencies; the app does not call an outside scanning API.
- Extension: scanning stays inside the browser page and only settings are stored by the extension. The chatbot page can already read its own composer; sending shares text with that provider. This is not protection from all page scripts or pre-send telemetry.

**What about false positives and false negatives?**

Both occur. Use the generated [benchmark tables](benchmark.md), naming the dataset and scoring rule. The realistic set is small and hand-authored; the external synthetic dataset has broader formats and different labels, and recall is much lower. Never translate these into a universal “accuracy” claim. No match is not a privacy guarantee.

**How do you know it works?**

Regression tests check exact spans, checksum validity, policy decisions, stale acknowledgements, blocked direct calls, reply restoration, escaping, and model failure. Shared fixtures compare Python and JavaScript examples. The generated report compares the frozen original detector and current modes. These do not substitute for live extension QA or real-world evaluation. Show [verification commands](VERIFICATION.md).

**What happens if the language model fails?**

Pattern/context/checksum detection continues. NER exceptions are caught without exposing input-bearing errors. A persistent warning says names, schools, and cities were not checked; the status displays a cross for that layer. This is intentionally degraded detection, not complete protection. See `ner_status()` and `find()` in [ner.py](../recognizers/ner.py) and [NER regression tests](../tests/test_ner.py).

**Why Streamlit?**

It lets the Python detector and review interface run together with session state and testable widgets. The tradeoffs are server processing, reruns, and a separate browser gesture for clipboard access. The public deployment receives messages remotely. [TODO: student — confirm this matches your actual reason for choosing it.]

**How would this reach real users?**

The app can be run locally or hosted. The unpacked extension beta explores reviewing directly in supported composers. Before wider distribution it needs reliable live-site tests, independent security/privacy review, accessibility testing, resource measurements, and user research. There is no Chrome Web Store release or adoption evidence to claim.

**What did you build versus what did AI write?**

OpenAI Codex assisted substantially with implementation, tests, and these drafts. Presidio, spaCy, phonenumbers, and Streamlit provide existing capabilities. [TODO: student — identify your own problem framing, design decisions, tests, debugging, and revisions honestly. Do not memorize an invented ownership claim.]

## If a judge points at the code

Start with: “This part takes ___, produces ___, and handles ___.” Then explain the reason and one limitation. The explanations below describe the implementation; they are not claims about who originally chose it.

| Code area | What it does | Why this design / tradeoff | Show this evidence |
| --- | --- | --- | --- |
| `Finding` in [detector.py](../detector.py) | Holds category, exact start/end offsets, value, reason and confidence | A shared shape lets rules, model, UI, and replacements work together; offsets must match the current text | [detector tests](../tests/test_detector.py) |
| `resolve_overlaps()` | Orders overlaps by category priority, length, then position | Prevents replacing the same characters twice; explicit national ID/secret/manual priorities win; lower-priority matches can be hidden | [national ID priority test](../tests/test_national_id.py), [redaction tests](../tests/test_redaction.py) |
| Registry in [recognizers/__init__.py](../recognizers/__init__.py) | Collects independently testable recognizer modules | New detection types can be added without putting every rule in one function; every category still needs metadata/policy/tests | [category tests](../tests/test_categories.py) |
| Regex plus `luhn_valid()` | Finds card-shaped runs and checks a digit checksum | Reduces arbitrary numeric matches; passing Luhn is not proof of a real card or permission to use one | [detector tests](../tests/test_detector.py) |
| `nearby()` in [ids.py](../recognizers/ids.py) | Requires labels near undashed SSNs, bank numbers, and birth dates | Context reduces false positives from ordinary numbers/dates; fixed windows can miss distant context or associate the wrong label | [ID tests](../tests/test_ids.py) |
| `valid()` in [national_id.py](../recognizers/national_id.py) | Checks a CN-shaped ID and MOD 11-2 digit | More precise than a raw 18-digit pattern; does not establish identity, issuance, or full date validity | [national ID tests](../tests/test_national_id.py) |
| `_engine()` in [ner.py](../recognizers/ner.py) | Loads the installed small English model once | Reusing the engine avoids repeated loading; messages/results are not cached across sessions. Availability is checked before use; no runtime model download | [NER tests](../tests/test_ner.py) |
| `POLICIES` and `evaluate_policy()` in [policy.py](../policy.py) | Maps categories to ALLOW/WARN/BLOCK and adds combination risk | A data table makes destinations auditable; unknown categories block. “Three types” is a chosen heuristic, not a measured identification probability | [combination tests](../tests/test_combination.py) |
| `review_fingerprint()` | Hashes exact review state including text, destination and policy | Acknowledgement cannot carry over to an edited message or policy. SHA-256 is used for binding, not encryption or anonymization | [service tests](../tests/test_submission_service.py), [style tests](../tests/test_styles.py) |
| `evaluate_submission()` in [submission_service.py](../submission_service.py) | Re-detects and evaluates on every final check | UI buttons alone are not an enforcement boundary; direct calls also block. Generic exceptions avoid echoing sensitive input | `test_blocked_direct_call_and_metadata_only`, `test_invalid_policy_fails_closed` |
| `apply_fixes()` in [suggestions.py](../suggestions.py) | Checks exact spans, then replaces from right to left | Replacing later spans first preserves earlier offsets. A stale suggestion raises rather than editing unrelated text | `test_stale_spans_rejected` in [redaction tests](../tests/test_redaction.py); [UI tests](../tests/test_simple_app.py) |
| Mapping key `(category, matched_text)` | Gives repeated values consistent replacements | It preserves consistency within a session. Collisions use unique placeholders. This is reversible pseudonymization, not irreversible anonymization | `test_sequential_fixes_preserve_distinct_and_repeated_tokens` |
| `ignore_values` | Exempts exact generated values after applying replacements | Fictional emails would otherwise trigger again. Exemptions are fingerprinted; a different real value still gets detected. A manually typed identical generated value is also exempt, an explicit limitation | `test_generated_values_are_exact_and_fingerprinted` |
| `restore_reply()` | Replaces exact known replacements in one pass | Prevents recursive substitution into newly inserted originals; some description-style replacements may still match ordinary reply wording | [restore tests](../tests/test_restore.py) |
| `findings_preview()` in [preview.py](../components/preview.py) | Escapes segments, adds text labels, masks secret previews | User markup must be rendered as text; labels help beyond color alone | [preview tests](../tests/test_preview.py) |
| `prepare_copy()` / clipboard component | Re-checks before mounting browser copy; checks pending editor values | A fresh server check and browser gesture serve different purposes; manual copying elsewhere can bypass this flow | `test_server_copy_callback_cannot_bypass_block` |
| `intercept()` / `permit` in [content.js](../extension/content.js) | Stops recognized risky sends; allows one exact-text override | Permission is temporary and text-bound, not a permanent bypass. Synthetic events and selectors may fail; live QA is required | [extension QA](../extension/QA.md), detector parity tests do **not** prove send interception |
| [selectors.js](../extension/selectors.js) | Keeps site-specific selectors in one place | Site DOMs change; isolated adapters make repair easier. The inactive badge exposes missing editors rather than implying coverage | Manual tests on each supported site |
| `overlap_score()` in [ai4privacy_eval.py](../benchmarks/ai4privacy_eval.py) | Matches predicted and annotated spans one-to-one | A long prediction cannot count as several true positives. Exact scoring remains visible because overlap alone can overstate quality | `test_overlap_matching_is_one_to_one_and_maximum` |

## Practice without memorizing

1. Load the coding demo and trace one SECRET from regex to policy to replacement.
2. Explain why the hosted banner says remote processing.
3. Change reviewed text after final check and show approval invalidation.
4. Explain one false negative from the benchmark and one reason a checksum is not identity verification.
5. Disable NER and show the honest warning.
6. Say exactly which parts you understand and which parts you still need to study. It is better to acknowledge a limit than invent a reason.
