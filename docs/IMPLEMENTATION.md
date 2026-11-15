# Upgrade checkpoints

## 0 — baseline audit

Read all existing application modules, configuration, README and tests. Git contained untracked project files from initial creation; preserved that work. All 50 baseline tests passed. Existing final-text rescanning and acknowledgement invalidation were functional. Invalid destinations raised an exception rather than returning a readable rejection; scanner/configuration errors lacked a shared fail-closed service. Copy was unrestricted and no visible approved-message inbox existed.

## 1 — reliability

Changed `policy.py`, `app.py`, `tests/test_policy.py`; added `submission_service.py` and direct-service tests. Implemented one authoritative scanner/policy boundary, current-policy/version fingerprints, generic error rejection, gated copy, rejected attempts, session-only approved inbox and reset controls. 61 tests passed. The legacy invalid-destination test now asserts rejection instead of expecting KeyError because the new service deliberately returns a structured failure. Manual copying remains outside enforcement.

## 2 — differentiation

Extended `detector.py`, `redaction.py`, `policy.py`, `demo_cases.py`, `evaluation.py`; added `risk_cards.py` and detector/redaction extension tests. Added validated IPv4, exact phrases/manual labels, three redaction modes, partial-mask policy, and human explanations. 82 tests passed. Preserved original 37 annotations and added 52 hand-annotated adversarial cases plus 10 negative controls. New risk: IPv4-shaped version numbers are false positives; partial masks retain characters and their marker can be manually removed. Both are disclosed.

## 3 — presentation and integration

Updated `app.py` with three-stage workspace, before/after columns, manual marking, four presets, dedicated testing tab and clear privacy boundaries. Added interaction and scoring invariants; updated README and generated verification/error reports. 87 tests passed and compilation passed. Browser verification follows a fresh server restart (the old server retained stale imports after the code upgrade). Live browser checks passed for blocked → redact → warning → acknowledge → inbox flow. Layout was inspected at 1024×768 and 375×812. Screenshots contain only fictional demo data.

## Deliberately omitted optional scope

No P3 extension, international-phone dependency, automatic person-name/address inference, or remote secret validation. The completed local workflow is the deliverable; extension integration remains future work. No accounts, hardware, paid services, outbound transmission, or persistent message history were added.

## 4 — v3 UI, UX and quality upgrade

Preserved the service boundary and datasets. Split UI into `components/` for workflow, state callbacks, findings, safe preview rendering, evidence and help. Added a compact responsive light theme, one primary check action, immediate redaction updates, friendly exact-phrase marking, masked finding previews and escaped highlights. Final send/copy callbacks read live session values and recheck exact outgoing text; warning approval still binds all relevant context. Policy version is now 3.0.

Evaluation now formats percentages, uses N/A only in negative-only presentation, and offers score charts with a table alternative, executable previous/current comparison and loadable fictional failures. Archived the actual previous detector and UI before edits. Version-label context removes two documented false positives across the positive datasets without reducing existing true positives. No dataset annotations were changed.

125 tests and compilation pass. Live browser scenario, responsive sizes and keyboard spot checks are recorded in VERIFICATION.md. Optional extension remains future work. No external API, automatic name/address inference, remote submission or persistent user-message storage was added.

## 5 — simplified product redesign

The actual app entry point now renders `components/simple.py`: one demo, compose/review, exact-span suggested fixes, editable reviewed text and validated copy. Removed navigation, simulation and evaluation from the product imports. Retained previous UI only for explicit legacy regression coverage. Added `suggestions.py` and `components/clipboard.py`; centralized the provided portfolio CSS tokens without copying content or assets. The existing policy service remains authoritative. Browser clipboard success and permission-failure fallback are explicit; no outside protection is claimed. See current README and VERIFICATION.md for usage and checks.
