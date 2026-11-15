# PrivacyGate extension beta

Load this folder unpacked in Chrome's extension developer mode. No build or npm packages are needed. Only the `storage` permission is used, for per-site enable switches. Message content stays in tab memory; no network requests, analytics, or message logging.

The manifest targets ChatGPT, Claude, and Gemini. Candidate selectors live in `selectors.js`; **live-site compatibility has not yet been certified**. The badge reports inactive when the composer or send control is missing. Names, schools, cities, and combination risk are not inferred here. International phone detection is shape-only; Python uses phonenumbers validation. Shared fixtures establish selected examples, not universal parity.

Enter without Shift and clicks on the recognized send control are intercepted in capture phase. BLOCK and WARN require explicit override; the SHA-256-bound one-shot override is valid only for unchanged text and one synchronous send replay. Some sites ignore synthetic keyboard events; use the site's send control again and review again. Other send paths and page scripts may bypass interception. This is a review aid, not a security boundary against the chatbot site itself.

Fix uses a native textarea setter or `execCommand('insertText')` for contenteditable editors, with verified text equality and a manual-copy fallback. `execCommand` is deprecated and editor compatibility varies. No response restoration is implemented in this beta.

Policy and regex files are bundled scripts to avoid runtime resource fetches. Regenerate with `python -m tools.export_policies` and `python -m tools.export_patterns`; Python tests detect drift.

Implementation references: [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts), [Chrome storage](https://developer.chrome.com/docs/extensions/reference/api/storage), [MDN execCommand limitations](https://developer.mozilla.org/en-US/docs/Web/API/Document/execCommand).
