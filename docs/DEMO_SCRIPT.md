# Three-minute demo draft

**[TODO: confirm time limit with official rubric.]** Rehearse this sequence with fictional data. Start the local app with the installed model. Confirm the status says names/places checked; if not, disclose that layer is unavailable. The public demo processes text remotely.

| Time | Action | Expected screen | Talking point |
| --- | --- | --- | --- |
| 0:00–0:20 | Introduce PrivacyGate and the hosting banner | “Review before sharing”; clear remote/local notice | “Catch the overshare before you hit send. Here is a fictional essay draft.” |
| 0:20–0:45 | Choose **College essay**, then **Check privacy** | Name, school, place, DOB, email, phone; **Combined details**; blocked by phone | “A name, school and city can identify someone together. This is a rule about co-occurrence, not identity verification.” |
| 0:45–1:10 | Keep **Placeholder**; click **Apply all recommended fixes** | Phone/email/name/school/DOB tokens; place may stay because it is optional for AI Chatbot | “The policy depends on where the message is going. Optional details are not included in Fix all.” |
| 1:10–1:25 | Click **Step 1 · Final check**, then **Step 2 · Copy to clipboard** | Browser copy confirmation or an honest manual-copy fallback | “The server checks the current text again; changing it revokes approval.” |
| 1:25–1:40 | Paste `I can help polish this essay. You can add [PHONE_1] at the end.` in **Paste the AI reply**; choose **Restore my details** | Restored code block includes `949-555-0134` | “The mapping stays in this session. This sample reply is staged; PrivacyGate does not call an AI.” |
| 1:40–2:00 | Choose **Coding help**, then **Check privacy** | SECRET cards, masked previews, blocked action | “An access key can grant account access. Patterns catch it even when it appears inside code.” |
| 2:00–2:30 | If live-site QA passed: show the installed extension in a new chatbot composer. Type `Call 949-555-0134`. Press Enter; use **Fix all**, then the site send control | Badge → blocked-send review → `[PHONE_1]` in editor → user sends revised text | “This beta tries to interrupt the send action on supported editors. It has no name/place model, and site changes can break it.” |
| 2:30–3:00 | Show the results slide and a limitation | Both hand-authored and external benchmark results, with scope | “The wider dataset is harder. I report the misses and false positives rather than claim complete protection.” |

Optional judge follow-up: **Public forum post** automatically selects Public Forum and blocks the address, phone, and email. **Harmless text** produces no supported matches; say “no match is not a guarantee.” Change the reviewed text after a successful final check to show that copy approval disappears.

## If something breaks

- Run locally using the README command. Use the installed model, and check the NER status before rehearsal.
- If NER fails, demonstrate the coding/contact patterns and explicitly say names, schools, and cities were not checked.
- If clipboard permission fails, use the approved-text fallback and explain the two-click design.
- If extension selectors fail, show the inactive badge; do not pretend it intercepted a send. Use the app's reviewed-copy workflow instead.
- [HUMAN] Record and test a backup demo video after passing the per-site QA checklist. No video has been recorded by this implementation.
- Use the screenshots linked from the README if available. Historical screenshots may show an earlier version; verify labels before presenting.

## Code handoff for judges

Keep `detector.py`, `policy.py`, `submission_service.py`, `suggestions.py`, and `recognizers/ner.py` open. Explain one path from input to decision before discussing individual regexes. For the extension, open `content.js` and explain the one-shot exact-message override and why site selectors are isolated.
