/* Site-owned selectors are volatile. Verify with extension/QA.md before each demo.
   These are candidate adapters, not a claim of live-site certification. */
globalThis.PrivacyGateSelectors = {
  'chatgpt.com': {composer:['#prompt-textarea','textarea[data-id="root"]'],send:['button[data-testid="send-button"]','button[aria-label="Send prompt"]']},
  'claude.ai': {composer:['div[contenteditable="true"][data-placeholder]','div.ProseMirror[contenteditable="true"]'],send:['button[aria-label="Send message"]','button[aria-label="Send Message"]']},
  'gemini.google.com': {composer:['rich-textarea div[contenteditable="true"]','div.ql-editor[contenteditable="true"]'],send:['button[aria-label="Send message"]','button.send-button']}
};
