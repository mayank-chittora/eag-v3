# Reading Assistant

A Chrome extension that provides instant AI-powered explanations for any text you select on a webpage. Highlight a word, phrase, sentence, or paragraph — click **Know More** — and get a concise, context-aware explanation powered by Google Gemini.

---

## Use Cases

- **Learning while reading** — Select an unfamiliar word or acronym and instantly get a definition, domain context, and synonyms without leaving the page.
- **Research** — Highlight a person's name, organisation, or event to get a quick factual summary.
- **Technical reading** — Select a technical term or concept (e.g. "attention mechanism", "margin call") to get a plain-English breakdown.
- **News and long-form articles** — Select a dense paragraph to get a distilled summary of the key points.
- **Language learning** — Select phrases in a foreign language (with surrounding English context) to get a contextual translation and explanation.

---

## Features

- Context-aware responses — the AI adapts its answer based on whether you selected a word, sentence, or paragraph
- Floating button appears near your selection — no page navigation required
- Clean bullet-point format — scannable, non-technical explanations
- Isolated UI — Shadow DOM prevents any style or script conflicts with the host page
- Model selector — choose from multiple Gemini models (stable and preview)
- Privacy-first — only the selected text (≤ 500 char context) is sent to the API; no URLs, cookies, or page metadata

---

## Setup

### 1. Get a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **Create API key**
4. Copy the key (it starts with `AIza...`)

### 2. Install the Extension

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `Reading Assistant/` folder
5. The Reading Assistant icon appears in your Chrome toolbar

### 3. Configure the Extension

1. Click the Reading Assistant icon in the toolbar
2. Paste your Gemini API key into the **Gemini API Key** field
3. Select your preferred **Gemini Model** from the dropdown (defaults to Gemini 2.5 Flash)
4. Click **Save Settings**

### 4. Use It

1. Go to any webpage
2. Select any text
3. A floating panel shows the AI explanation as bullet points
4. Click anywhere else or press **Escape** to dismiss

---

## Supported Gemini Models

| Model | Description |
|---|---|
| **Gemini 2.5 Flash** *(default)* | Best price-performance; low latency, high throughput |
| **Gemini 2.5 Flash Lite** | Fastest and most cost-efficient |
| **Gemini 2.5 Pro** | Most capable; best for complex or technical content |
| Gemini 3.1 Pro Preview | Frontier reasoning, preview access |
| Gemini 3 Flash Preview | Frontier-class speed, preview access |
| Gemini 3.1 Flash Lite Preview | Cost-optimised frontier model, preview access |

Preview models may require billing to be enabled on your Google Cloud project.

---

## Implementation

### Tech Stack

| Component | Technology |
|---|---|
| Extension platform | Chrome Manifest V3 |
| Scripting | Vanilla JavaScript (ES2020+, no build step) |
| AI backend | Google Gemini REST API |
| UI isolation | Shadow DOM (`mode: 'closed'`) |
| Settings storage | `chrome.storage.local` |
| Styles | Vanilla CSS (scoped inside Shadow DOM) |

### File Structure

```
Reading Assistant/
├── manifest.json                 # MV3 manifest — permissions, CSP, entry points
├── background/
│   └── service-worker.js         # All API calls and storage access
├── content/
│   ├── content.js                # Text selection detection and floating UI
│   └── content.css               # Extension UI styles (Shadow DOM scoped)
├── popup/
│   ├── popup.html                # Settings page — API key + model picker
│   ├── popup.js                  # Save/load settings via chrome.storage
│   └── popup.css                 # Settings page styles
├── utils/
│   └── prompt-builder.js         # Constructs context-aware Gemini prompts
└── icons/
    └── icon{16,32,48,128}.png
```

### How It Works

#### 1. Text Selection (`content.js`)

The content script listens for `mouseup` events (debounced at 200ms) on every page. When the user releases the mouse after selecting text:

- The selection length is checked — ignored if empty or inside an `<input>` / `<textarea>`
- The selected text and up to 500 characters of surrounding context are captured
- The word count classifies the selection:
  - ≤ 2 words → `word_or_phrase`
  - 3–15 words → `phrase_or_sentence`
  - > 15 words → `paragraph`
- A **Know More** button is rendered inside a Shadow DOM host, positioned near the selection and clamped to viewport edges

#### 2. Message Passing

When the user clicks **Know More**, the content script sends a message to the service worker via `chrome.runtime.sendMessage`:

```
{ type: 'EXPLAIN_TEXT', payload: { selectedText, surroundingText, selectionType } }
```

Content scripts never make `fetch()` calls directly — all network access is centralised in the service worker.

#### 3. Prompt Construction (`prompt-builder.js`)

A pure function builds a structured prompt based on the `selectionType`:

- **word_or_phrase** — requests definition, domain/field, synonyms, and a real-world usage example
- **phrase_or_sentence** — requests a plain-English explanation, type identification (person/place/concept/etc.), and key facts
- **paragraph** — requests a 2-line summary, 3–4 key facts, caveats, and the big-picture significance

Surrounding context is always included to help the model disambiguate. The prompt instructs the model to respond in 3–6 plain-text bullet points with no markdown or URLs.

#### 4. Gemini API Call (`service-worker.js`)

The service worker:

1. Enforces a 4.5-second global cooldown across all tabs
2. Retrieves `geminiApiKey` and `geminiModel` from `chrome.storage.local` (never cached in memory)
3. Builds the endpoint dynamically: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
4. POSTs the prompt with conservative generation config (`temperature: 0.3`, `maxOutputTokens: 800`)
5. Maps HTTP error codes (400, 401, 403, 404, 429, 500, 503) to user-friendly messages
6. Parses the markdown bullet-point response into a plain string array

#### 5. Result Display (`content.js`)

The service worker's response is received by the content script, which replaces the loading skeleton in the Shadow DOM popup with the bullet points. Pressing **Escape** or clicking outside dismisses the panel and cleans up all event listeners.

### Security

- **Content Security Policy**: `script-src 'self'; object-src 'self'` — no eval, no inline scripts
- **API key**: stored only in `chrome.storage.local`, never in DOM storage, never logged to console
- **Minimal permissions**: `activeTab`, `storage`, and a host permission scoped to `generativelanguage.googleapis.com` only
- **Shadow DOM**: extension UI is fully isolated from the host page's CSS and JavaScript
- **No data collection**: only the selected text and local context window are sent to Gemini; no page URLs, user identity, or metadata

---

## After Any Code Change

1. Go to `chrome://extensions`
2. Click the **refresh icon** on the Reading Assistant card
3. Reload the tab you are testing on