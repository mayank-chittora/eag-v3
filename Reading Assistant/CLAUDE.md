# Reading Assistant — Project Instructions for Claude Code

## Project Overview
Reading Assistant is a Chrome Extension (Manifest V3) that enhances the reading experience on
any webpage. When a user selects text, a "Know More" button appears near the selection.
Clicking it calls the Google Gemini Flash 2.0 API with the selected text and surrounding context,
then displays the AI response as clean bullet points in a floating popup.

The extension is context-aware:
- Single word or phrase → definition, context, synonyms
- Sentence or entity name → contextual explanation, who/what it is
- Paragraph → summarised key points

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Extension platform | Chrome MV3 | Industry standard; MV2 deprecated |
| Scripting | Vanilla JavaScript (ES2020+) | No build step; lighter weight |
| AI API | Google Gemini Flash 2.0 (REST) | Fast, cost-effective, no SDK needed |
| UI isolation | Shadow DOM | Prevents CSS conflicts with host page |
| Key storage | chrome.storage.local | Secure, sandboxed per extension |
| Styles | Vanilla CSS (inside Shadow DOM) | No Tailwind — extension files must be self-contained |

## File Structure

```
Reading Assistant/
├── CLAUDE.md                    ← YOU ARE HERE
├── .claude/
│   ├── agents/
│   │   └── extension-agent.md  ← All extension implementation work
│   └── rules/
│       └── extension-development.md ← All code rules and constraints
├── manifest.json                ← MV3 manifest (root of the extension)
├── background/
│   └── service-worker.js        ← API calls, storage, message handling
├── content/
│   ├── content.js               ← Text selection detection, UI rendering
│   └── content.css              ← Popup + button styles (Shadow DOM scoped)
├── popup/
│   ├── popup.html               ← Extension settings page (API key entry)
│   ├── popup.js                 ← Save/load API key via chrome.storage
│   └── popup.css                ← Settings page styles
├── utils/
│   └── prompt-builder.js       ← Gemini prompt construction (pure function)
└── icons/
    └── icon{16,32,48,128}.png
```

## How to Use the Agent

For all implementation work — manifest changes, content script, service worker, prompt tuning,
CSS, or debugging — use:

```
@extension-agent [your task description]
```

The extension agent follows `.claude/rules/extension-development.md` automatically.

## How to Install & Test Locally

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle, top-right corner)
3. Click **Load unpacked**
4. Select the `Reading Assistant/` folder
5. The extension icon appears in the toolbar
6. Click the icon → enter your Gemini API key → click Save
7. Go to any webpage, select text, click "Know More"

### Getting a Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Copy it and paste it into the extension's settings popup

### After Any Code Change
- Go to `chrome://extensions`
- Click the **refresh icon** on the Reading Assistant card
- Reload the tab you are testing on
- Re-test the changed behaviour

## Critical Rules for Claude Code

1. **No build tools.** Never add `package.json`, `webpack.config.js`, or any build pipeline.
   The extension loads directly from source files.

2. **No eval() or inline scripts.** The CSP in `manifest.json` blocks both. Violations will
   cause the extension to fail silently in production.

3. **API calls only from `service-worker.js`.** The content script never makes `fetch()` calls.
   Use `chrome.runtime.sendMessage` / `sendResponse` pattern exclusively.

4. **Shadow DOM for all UI.** Never append extension elements directly to `document.body`.
   Use the shadow host in `content.js` exclusively.

5. **API key in `chrome.storage.local` only.** Never in `window.localStorage`, `sessionStorage`,
   or any DOM storage. Never logged to console.

6. **After any `manifest.json` change**, explicitly note in the response that the extension
   must be reloaded in `chrome://extensions` before the change takes effect.

7. **Test on edge cases.** After any `content.js` change, verify on: a plain Wikipedia article,
   a React SPA (like GitHub), and a page with iframes (like Google Docs).
