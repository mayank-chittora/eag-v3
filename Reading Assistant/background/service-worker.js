// background/service-worker.js — Reading Assistant
// Handles all Gemini API communication and chrome.storage access.
// Content scripts NEVER make API calls directly — everything goes through here.

import { buildGeminiPrompt } from '../utils/prompt-builder.js';

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

// Global cooldown shared across all tabs (service worker is single process per extension)
let lastRequestAt = 0;
const COOLDOWN_MS = 4500;

// ─── Message Listener ─────────────────────────────────────────────────────────
// Must return true to keep the message channel open for the async response.

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== 'EXPLAIN_TEXT') return false;

  handleExplainText(message.payload)
    .then(result => sendResponse(result))
    .catch(err => sendResponse({ error: 'Unexpected error: ' + err.message }));

  return true; // Critical: keeps sendResponse valid across the async boundary
});

// ─── Core Handler ─────────────────────────────────────────────────────────────

async function handleExplainText({ selectedText, surroundingText, selectionType }) {
  // Step 1: Global cooldown check (shared across all tabs)
  const now = Date.now();
  const wait = COOLDOWN_MS - (now - lastRequestAt);
  if (wait > 0) {
    return { error: `Please wait ${Math.ceil(wait / 1000)}s before the next lookup.` };
  }
  lastRequestAt = now;

  // Step 2: Retrieve API key and model from storage (never cached in memory)
  const { geminiApiKey, geminiModel } = await chrome.storage.local.get(['geminiApiKey', 'geminiModel']);

  if (!geminiApiKey) {
    return {
      error: 'No API key set. Click the extension icon in your toolbar to add your Gemini API key.'
    };
  }

  const model = geminiModel || 'gemini-2.5-flash';
  const endpoint = `${GEMINI_BASE}/${model}:generateContent`;

  // Step 3: Build the prompt
  const prompt = buildGeminiPrompt(selectedText, surroundingText, selectionType);

  // Step 4: Call Gemini REST API
  let response;
  try {
    response = await fetch(`${endpoint}?key=${geminiApiKey}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [
          {
            parts: [{ text: prompt }]
          }
        ],
        generationConfig: {
          temperature: 0.3,   // Low temp for factual, consistent output
          maxOutputTokens: 800,   // Enough for 5-6 full bullet points without truncation
          topP: 0.8,
          topK: 40
        },
        safetySettings: [
          { category: 'HARM_CATEGORY_HARASSMENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_HATE_SPEECH', threshold: 'BLOCK_MEDIUM_AND_ABOVE' },
          { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_MEDIUM_AND_ABOVE' }
        ]
      })
    });
  } catch (_networkError) {
    return { error: 'Network error. Please check your internet connection and try again.' };
  }

  // Step 4: Map HTTP error codes to user-friendly messages
  if (!response.ok) {
    return { error: mapHttpError(response.status) };
  }

  // Step 5: Parse the response
  let data;
  try {
    data = await response.json();
  } catch (_parseError) {
    return { error: 'Could not read Gemini response. Please try again.' };
  }

  // Check for safety blocks or empty candidates
  const candidate = data?.candidates?.[0];
  if (!candidate) {
    const blockReason = data?.promptFeedback?.blockReason;
    if (blockReason) {
      return { error: 'This content was blocked by Gemini safety filters.' };
    }
    return { error: 'No response received from Gemini. Please try again.' };
  }

  const rawText = candidate?.content?.parts?.[0]?.text;
  if (!rawText || !rawText.trim()) {
    return { error: 'Gemini returned an empty response. Please try again.' };
  }

  // Step 6: Parse bullet points from markdown-style response
  const bullets = parseBulletPoints(rawText);

  if (bullets.length === 0) {
    return { error: 'Could not parse Gemini response. Please try again.' };
  }

  return { bullets };
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Parse bullet points from Gemini's markdown response.
 * Handles "- item", "* item", "• item", and plain lines.
 */
function parseBulletPoints(rawText) {
  return rawText
    .split('\n')
    .map(line => line.replace(/^[\s\-\*\•\–]+/, '').trim())
    .filter(line => line.length > 3); // Filter out very short/empty lines
}

/**
 * Map HTTP status codes to user-friendly error messages.
 */
function mapHttpError(status) {
  switch (status) {
    case 400:
      return 'The selected text could not be processed. Try selecting a shorter passage.';
    case 401:
    case 403:
      return 'Invalid API key. Click the extension icon to update your Gemini API key.';
    case 404:
      return 'Gemini model not found. The selected model may not be available with your API key.';
    case 429:
      return 'Rate limit reached. Please wait a moment and try again.';
    case 500:
    case 503:
      return 'Gemini service is temporarily unavailable. Please try again in a moment.';
    default:
      return `Gemini API error (${status}). Please try again.`;
  }
}
