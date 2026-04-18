// utils/prompt-builder.js — Reading Assistant
// Pure function: builds context-aware Gemini prompts based on selection type.
// No Chrome APIs, no DOM access — safe to unit-test in isolation.

/**
 * Build a Gemini prompt for the selected text.
 *
 * @param {string} selectedText     - The text the user highlighted
 * @param {string} surroundingText  - Up to 500 chars of surrounding paragraph text (may be empty)
 * @param {string} selectionType    - 'word_or_phrase' | 'phrase_or_sentence' | 'paragraph'
 * @returns {string} The complete prompt string to send to Gemini
 */
export function buildGeminiPrompt(selectedText, surroundingText, selectionType) {
  const contextSection = surroundingText && surroundingText.trim()
    ? `\n\nSurrounding context from the page:\n"""${surroundingText.trim()}"""`
    : '';

  const typeInstruction = getTypeInstruction(selectionType);

  return `You are a smart reading assistant embedded in a web browser. A reader has selected text while reading a webpage.

Selected text:
"""${selectedText}"""${contextSection}

${typeInstruction}

RESPONSE FORMAT RULES (CRITICAL — follow exactly):
- Respond ONLY with bullet points. No preamble, no intro sentence, no "Here are the details:", no conclusion.
- Use plain "-" as the bullet marker (hyphen + space), not numbers, not "•", not "*".
- Minimum 3 bullet points. Maximum 6 bullet points.
- Each bullet point: 1–2 sentences maximum. Be concise and precise.
- Plain text only. No bold (**), no italic (_), no markdown within bullets.
- Do NOT repeat the selected text back verbatim as a bullet.
- If you cannot determine accurate information with confidence, say so clearly in one bullet point.`;
}

/**
 * Returns the task-specific instruction block based on selection type.
 * @param {string} selectionType
 * @returns {string}
 */
function getTypeInstruction(selectionType) {
  switch (selectionType) {
    case 'word_or_phrase':
      return `The selected text is a word or short phrase. Your task:
- Provide a clear, concise definition in plain English
- Identify the context or domain it relates to (e.g., Finance, Biology, Law, Technology, History)
- List 2–3 synonyms or closely related terms (if applicable)
- Give one concrete example showing its real-world usage or significance`;

    case 'phrase_or_sentence':
      return `The selected text is a phrase or sentence. Your task:
- Explain what this means in simple, plain English
- Identify what type of thing this is: a concept, an event, a person, an organisation, a place, a policy, etc.
- Provide key facts or background context a reader would need to understand this fully
- If this refers to an organisation, person, or place: explain who/what they are and why they matter`;

    case 'paragraph':
    default:
      return `The selected text is a paragraph or longer passage. Your task:
- Summarise the single most important point in one sentence
- Extract 3–4 key facts, claims, or concepts from the text
- Note any important context, caveats, or nuances the reader should be aware of
- Explain why this topic matters in the broader context (one sentence on big-picture significance)`;
  }
}
