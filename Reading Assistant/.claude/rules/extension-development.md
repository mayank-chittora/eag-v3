# Reading Assistant — Extension Development Rules

## 1. Project Structure

```
Reading Assistant/
├── manifest.json              ← MV3 manifest. Root of the extension.
├── background/
│   └── service-worker.js     ← Handles API calls, storage access, message routing
├── content/
│   ├── content.js             ← Injected into every page. UI logic only.
│   └── content.css            ← Scoped to Shadow DOM. No impact on host page.
├── popup/
│   ├── popup.html             ← Extension action popup (API key settings)
│   ├── popup.js               ← Options page logic
│   └── popup.css              ← Options page styles
├── utils/
│   └── prompt-builder.js     ← Pure function: (text, context, type) → prompt string
└── icons/
    ├── icon16.png
    ├── icon32.png
    ├── icon48.png
    └── icon128.png
```

## 2. Permissions Policy

| Permission | Reason | Avoid |
|---|---|---|
| `activeTab` | Content script access to page | `tabs` (broader, not needed) |
| `storage` | Store API key securely | `cookies`, `unlimitedStorage` |
| `host_permissions: generativelanguage.googleapis.com` | Service worker fetch to Gemini | `<all_urls>` in host_permissions |

**Rule**: Request the minimum permissions. Each additional permission triggers a more alarming install dialog.

## 3. Content Script Rules

1. All DOM elements created by the extension go into a **Shadow DOM** with `mode: 'closed'`.
2. Append the shadow host to `document.documentElement`, not `document.body` — survives SPA navigation.
3. All event listeners attached to `document` must be removed when the popup is dismissed.
4. The content script must **never** directly call `chrome.storage` — send a message to the service worker.
5. Use a 200ms debounce on `mouseup` to prevent firing on every tiny mouse movement during selection.
6. Clamp button position to viewport edges: `Math.max(8, Math.min(computedLeft, window.innerWidth - 136))`.
7. Never use `document.write()`, `innerHTML` on host page elements, or `eval()`.
8. The content script handles UI only. No business logic, no API calls, no storage access.
9. Skip rendering when `document.activeElement` is an INPUT, TEXTAREA, or SELECT.

## 4. Service Worker Rules

1. Service workers in MV3 are ephemeral — they terminate after ~30 seconds of inactivity.
2. Always `return true` in `onMessage.addListener` when the callback is asynchronous.
3. Retrieve `geminiApiKey` from `chrome.storage.local` on every API call — never cache in memory.
4. Map every Gemini API HTTP error code to a user-friendly, non-technical error message.
5. Gemini API endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent`
6. Do not use the Gemini JavaScript SDK — use the REST API directly via `fetch()`.
7. Never log the API key to `console`.

## 5. CSS Isolation Rules

1. All extension CSS is defined in `content.css` and loaded inside the Shadow DOM only.
2. All extension CSS class names and IDs are prefixed with `ra-` to avoid conflicts.
3. Use `font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` — no Google Fonts loaded into host pages.
4. Never use `!important` unless overriding a browser default inside Shadow DOM.
5. All `position: absolute` elements are positioned relative to the shadow host (which is `position: fixed`).

## 6. Security Rules

1. **No eval()** — CSP blocks it; hard rule even without CSP.
2. **No inline scripts** in `popup.html` — use `popup.js` exclusively.
3. **API key validation**: Before saving, check that the key starts with `AIza`.
4. **No key logging**: Never log `geminiApiKey` to console. Mask it in UI with `type="password"`.
5. **Content Security Policy**: `script-src 'self'; object-src 'self'` enforced in `manifest.json`.
6. The extension must not exfiltrate any browsing data. The service worker only sends `selectedText` and `surroundingText` (max 500 chars) to Gemini — never page URLs, cookies, or metadata.

## 7. Performance Rules

1. Debounce `mouseup` at 200ms — no processing on rapid selection changes.
2. Limit `surroundingText` to 500 characters to minimize prompt tokens and API latency.
3. Limit `maxOutputTokens` to 400 in Gemini config — sufficient for 5-6 bullets.
4. The content script is loaded on `document_idle` — after page load completes.
5. Clean up all event listeners and DOM state when the popup is dismissed.
6. Never poll or use `setInterval` in the content script.

## 8. Gemini Prompt Rules

1. The prompt in `utils/prompt-builder.js` is the single source of truth for AI behaviour.
2. Response format instructions (bullet point rules) must be at the **end** of the prompt.
3. The `selectionType` classification (`word_or_phrase` | `phrase_or_sentence` | `paragraph`) is determined by word count in the content script, not inferred by the model.
   - `word_or_phrase`: ≤ 2 words
   - `phrase_or_sentence`: 3–15 words
   - `paragraph`: > 15 words
4. Always include `surroundingText` in the prompt when available — context prevents misclassification.
5. Never ask the model to include URLs, citations, or external links in its response.
6. Keep prompt total length under 1200 tokens to maintain fast response times with Flash 2.0.

## 9. Manual Testing Checklist

Before any release, test all of the following scenarios:

**Text Selection**
- [ ] Single word: gets definition + synonyms
- [ ] Person name (e.g., "Elon Musk"): gets brief bio/context
- [ ] Organisation name (e.g., "NASA"): gets company/agency description
- [ ] Technical term (e.g., "photosynthesis"): gets explanation
- [ ] Full sentence: gets contextual explanation
- [ ] Full paragraph: gets summary bullets
- [ ] Selection across two paragraphs: handles gracefully

**UI Behaviour**
- [ ] Button appears near selection, within viewport, not clipped
- [ ] Button disappears when clicking elsewhere
- [ ] Popup appears when "Know More" is clicked
- [ ] Loading skeleton visible while fetching
- [ ] Escape key dismisses popup
- [ ] Clicking outside popup dismisses it
- [ ] Making a new selection dismisses old popup
- [ ] Works on: Wikipedia, BBC News, GitHub, Google.com
- [ ] No visible layout damage to host page

**Error States**
- [ ] No API key set: shows "click extension icon to add key" message
- [ ] Invalid API key: shows "invalid API key" message
- [ ] Rate limited: shows "wait and try again" message
- [ ] Network offline: shows "check your connection" message

**Edge Cases**
- [ ] Select text in an `<input>` or `<textarea>`: button should NOT appear
- [ ] Very long selection (500+ words): truncated gracefully, prompt still works
- [ ] Rapid multiple selections: only latest selection processed

## 10. File Responsibility Matrix

| File | Owns | Never Accesses |
|---|---|---|
| `content.js` | DOM manipulation, selection capture, UI state, message send | `fetch()`, `chrome.storage`, business logic |
| `service-worker.js` | API calls, storage read/write, message receive/respond | DOM, `document`, `window` |
| `popup.js` | Extension settings UI, `chrome.storage` write | DOM of host pages |
| `prompt-builder.js` | Prompt string construction | Chrome APIs, DOM |
| `content.css` | Extension UI visual styles | Host page elements |
