# Prompts & PoP Validation JSON — Assignment 6

Each role that calls an LLM uses a `response_format` JSON schema to constrain the model's output. These schemas are the **PoP (Proof of Prompt) Validation JSONs** — they enforce the contract between the LLM output and the typed Pydantic objects consumed by the agent loop.

---

## 1. Perception

**File:** `perception.py`  
**Function:** `observe()`  
**Model:** `gemini-3.1-flash-lite` via LLM Gateway V3  
**Temperature:** `1.0` (prevents Gemini flash-lite from looping at temp=0 on structured output)

### System Prompt

```
You are the Perception role in a cognitive agent. Each iteration you receive:
- The user query
- Memory hits (some may carry artifact handles, shown with an artifact_index integer)
- Prior goals (if any) with their current done/open status
- Run history (recent actions and answers)

Your responsibilities:

1. FIRST CALL (prior_goals is empty):
   Decompose the query into 1-5 short imperative goals (verb + object).
   Each goal is one bounded task. Set done=false, artifact_index=-1 for all.

2. SUBSEQUENT CALLS (prior_goals is non-empty):
   Preserve the EXACT same number of goals in the EXACT same order.
   Do NOT reorder, insert, or drop goals.
   For each goal: examine run history. Mark done=true if history contains an
   action or answer that clearly satisfies the goal.
   STICKY DONE: once a goal is done, never set it back to false.

3. ARTIFACT ATTACHMENT (first unfinished goal only):
   If the first unfinished goal requires reading content from a previously
   fetched page/document (e.g., "extract", "summarise", "analyse", "compare",
   "choose", "list", "tell me based on"), AND an artifact exists in memory hits,
   set artifact_index to the integer shown next to that artifact in MEMORY HITS.
   Otherwise set artifact_index=-1.

SYNTHESIS RULE: If the first unfinished goal text contains any of these words —
   "synthesise", "synthesis", "extract", "compare", "list", "choose", "select",
   "decide", "tell me", "summarise", "agree on", "in common", "analyse", "analyze"
— AND there are artifacts in the MEMORY HITS section, automatically set
artifact_index to the index of the most recently created artifact hit.

Output valid JSON only. No explanations.
```

### User Prompt Template

```
USER QUERY: {query}

MEMORY HITS (indexed):
  [fact] no_artifact | <descriptor>
  [tool_outcome] artifact_index=0 | <descriptor> | handle=art:<id>
  [tool_outcome] artifact_index=1 | <descriptor> | handle=art:<id>

PRIOR GOALS: (none — first call, please decompose the query)
  — OR —
PRIOR GOALS:
  [done] g1: <goal text>
  [open] g2: <goal text>

RUN HISTORY: (empty)
  — OR —
RUN HISTORY:
  iter1 ACTION web_search({'query': '...'}) → <result descriptor>
  iter2 ANSWER for g1: <answer text>

Emit the goal list as JSON.
artifact_index: integer. Use -1 for no attachment. Use 0, 1, 2... to reference
the artifact_index shown in MEMORY HITS above.
```

### PoP Validation JSON (`_PERCEPTION_SCHEMA`)

```json
{
  "type": "object",
  "properties": {
    "goals": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "items": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string"
          },
          "done": {
            "type": "boolean"
          },
          "artifact_index": {
            "type": "integer",
            "description": "-1 means no attachment; 0+ is index into the ARTIFACT HITS list"
          }
        },
        "required": ["text", "done", "artifact_index"],
        "additionalProperties": false
      }
    }
  },
  "required": ["goals"],
  "additionalProperties": false
}
```

### Safety Guards Applied in Code (post-LLM)

| Guard | Implementation | Why |
|-------|----------------|-----|
| Positional goal IDs | Loop assigns `g1`, `g2`, ...; LLM never writes IDs | Prevents hallucinated/stale goal IDs |
| Integer artifact index | LLM emits `0`, `1`, ...; Python maps to `art:` handle | Prevents hallucinated `art:` handle strings |
| Sticky-done | `is_done = prior_goals[i].done or bool(rg["done"])` | Once satisfied, goal stays satisfied |
| Fallback on empty | If LLM returns no goals, preserve prior goals or echo query | Prevents silent agent stall |

---

## 2. Decision

**File:** `decision.py`  
**Function:** `next_step()`  
**Model:** `gemini-3.1-flash-lite` via LLM Gateway V3  
**Temperature:** `0.2` (stable, deterministic action selection)

### System Prompt Template

```
You are the Decision role in a cognitive agent. You receive ONE goal and must
choose EXACTLY ONE action.

OUTPUT FORMAT (JSON):
  To answer directly:
    {"action_type": "answer", "answer_text": "<your full answer>", "tool_name": "", "tool_arguments_json": "{}"}

  To call a tool:
    {"action_type": "tool_call", "answer_text": "", "tool_name": "<tool>", "tool_arguments_json": "<json string of args>"}

TOOL SELECTION GUIDE:
  fetch_url  — use when the goal says "fetch", "read", or gives a specific URL
  web_search — use when the goal says "find", "search for", or needs to discover URLs
  get_time   — use when time or date information is needed
  create_file / update_file / edit_file — use when goal asks to create/write files
  read_file / list_dir — use when goal asks to read existing files

EXAMPLES of tool_arguments_json:
  fetch_url  : '{"url": "https://en.wikipedia.org/wiki/Claude_Shannon"}'
  web_search : '{"query": "family-friendly things to do in Tokyo"}'
  create_file: '{"path": "reminders/note.txt", "content": "Reminder text here"}'

RULES:
1. Use action_type="answer" when memory hits or ATTACHED ARTIFACTS already contain
   enough information to fully answer the goal.
2. ARTIFACT HANDLES (strings starting with "art:") are NOT valid tool arguments.
   Never put them in tool_arguments_json. Read artifact content from ATTACHED ARTIFACTS.
3. Substantive answers must be at least 3 sentences or a numbered list.
4. tool_arguments_json must be valid JSON encoded as a string.
5. Call exactly ONE tool per response.

AVAILABLE TOOLS:
  web_search(query: string, max_results: integer)
    Search the web for current information.
  fetch_url(url: string)
    Fetch and extract the full text content of a URL.
  get_time(timezone: string)
    Get the current date and time in an IANA timezone.
  currency_convert(amount: number, from_currency: string, to_currency: string)
    Convert a currency amount using live exchange rates.
  read_file(path: string)
    Read the contents of a file (sandboxed to ./sandbox/).
  list_dir(path: string)
    List directory contents (sandboxed to ./sandbox/).
  create_file(path: string, content: string)
    Create a new file with the given content (sandboxed to ./sandbox/).
  update_file(path: string, content: string)
    Overwrite an existing file (sandboxed to ./sandbox/).
  edit_file(path: string, old_text: string, new_text: string)
    Replace a substring in an existing file (sandboxed to ./sandbox/).
```

### User Prompt Template

```
CURRENT GOAL: {goal.text}

MEMORY HITS:
  [fact] <descriptor>
  [tool_outcome] <descriptor> [artifact: art:<id>]

RECENT HISTORY:
  iter1 web_search({'query': '...'}) → <result descriptor>
  iter2 ANSWER: <answer text>

ATTACHED ARTIFACTS:
=== ARTIFACT art:<id> ===
<up to 80,000 chars of artifact text content>

Respond with JSON only.
```

### PoP Validation JSON (`_DECISION_SCHEMA`)

```json
{
  "type": "object",
  "properties": {
    "action_type": {
      "type": "string",
      "enum": ["answer", "tool_call"]
    },
    "answer_text": {
      "type": "string",
      "description": "Substantive answer. Fill when action_type='answer', else empty string."
    },
    "tool_name": {
      "type": "string",
      "description": "Name of the tool to call. Fill when action_type='tool_call', else empty string."
    },
    "tool_arguments_json": {
      "type": "string",
      "description": "JSON-encoded arguments for the tool, e.g. '{\"url\": \"https://...\"}'. Fill when action_type='tool_call'. Use '{}' when action_type='answer'."
    }
  },
  "required": ["action_type", "answer_text", "tool_name", "tool_arguments_json"],
  "additionalProperties": false
}
```

### Design Notes

| Choice | Reason |
|--------|--------|
| `tool_arguments_json` is a `string`, not an `object` | Gemini flash-lite cannot reliably populate free-form `{"type": "object"}` fields in structured output mode. Encoding args as a JSON string lets the model write any valid JSON; Python parses it after. |
| `temperature=0.2` | Low temperature gives stable, deterministic action selection without the repetition risk of `temperature=0`. |
| No native tool calling | `response_format` JSON schema is more reliable than native tool declarations for flash-lite. |
| Artifact content in prompt text | Artifact bytes are passed as plain text in `ATTACHED ARTIFACTS`, never as tool arguments — prevents the model from confusing content with handles. |
