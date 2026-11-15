# Manual browser QA — required before demonstrating

Status: **not yet performed on live sites**. Automated tests cover the shared detector fixtures and exported policies, not site compatibility. Repeat after site UI changes and record browser version, date, and results. Use only fictional text; sending a demo message sends it to the selected chatbot provider.

For **each** of ChatGPT (`chatgpt.com`), Claude (`claude.ai`), and Gemini (`gemini.google.com`):

- [ ] Open Chrome extensions, turn on Developer mode, choose **Load unpacked**, and select `extension/`.
- [ ] Open a new chat; confirm an active PrivacyGate badge. Record any missing composer/send selector.
- [ ] Type `Call 949-555-0134 and email alex@example.com.`; the badge says one blocked and one to review.
- [ ] Press Enter: the composer text remains, the message is not sent, and review opens.
- [ ] Close review; click the site's send control: it is blocked too.
- [ ] Choose **Fix all**: check the editor contains exact placeholders. If editing fails, **Copy fixed text** appears and works.
- [ ] Send the fixed fictional message normally.
- [ ] Type the fictional phone again; choose **Send anyway**: one unchanged-message send attempt is permitted. If synthetic Enter is ignored, test the site's send button and record the limitation.
- [ ] WARN-only `alex@example.com` requires **Send with warning**.
- [ ] Edit the message while review is open: the prior override is invalidated. A second send requires a new review.
- [ ] Shift+Enter inserts a newline. IME composition does not cause an interception.
- [ ] Start a new chat or navigate: changed editor nodes are detected.
- [ ] On a page without a composer/send control, verify **PrivacyGate inactive on this page**. Temporarily break an adapter in a development copy and reload to test failure.
- [ ] Disable the site in the popup: badge says disabled; re-enable restores checks. Only the enable setting is stored.
- [ ] Keyboard focus reaches badge, Fix, override, and Close. Labels remain understandable without color.
- [ ] No message content appears in extension storage, console logs, or extension-generated network traffic.

Known limitations: page scripts already have access to their editor, alternative send paths may bypass the extension, international phone checks are shape-only, no NER or image inspection, `execCommand` and synthetic events vary across editors. See [implementation details](README.md).
