# EAG V3 Assignment 6 — Multi-Role Cognitive Agent

A multi-role cognitive agent with four typed roles (Memory, Perception, Decision, Action)
communicating via Pydantic v2 contracts. All LLM calls use Gemini via the LLM Gateway V3.

## Architecture

```
agent6.py
  ├── schemas.py      — Pydantic v2 contracts: MemoryItem, Goal, Observation, ToolCall,
  │                     DecisionOutput, ActionResult, ActionEvent, AnswerEvent, HistoryEvent
  ├── memory.py       — Keyword-search read (no LLM) + LLM-classify write; state/memory.json
  ├── artifacts.py    — Content-addressable blob store; state/artifacts/
  ├── perception.py   — observe(): goal decomposition + artifact attach (Gemini, temp=1.0)
  ├── decision.py     — next_step(): answer or tool call (Gemini, temp=0.2, JSON schema)
  ├── action.py       — execute(): pure MCP dispatch, 4KB artifact threshold → ActionResult
  └── mcp_server.py   — 9 MCP tools via stdio (web_search, fetch_url, file tools, ...)
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Gemini API key

## Setup

```bash
cd "Assignment 6"

# 1. Copy .env.example and add your Gemini API key
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY

# 2. Install dependencies
uv sync
```

## Start the LLM Gateway

The gateway must be running before starting the agent. Open a separate terminal:

```bash
cd "Assignment 6/llm_gatewayV3"
./run.sh
# Creates .venv + installs deps on first run, then starts on port 8101
# Dashboard: http://localhost:8101
```

## Run the Four Target Queries

```bash
# Clean state before each attempt
rm -rf state/

# Query A — Claude Shannon Wikipedia
uv run python agent6.py --query-a

# Query B — Tokyo activities + Saturday weather (multi-goal)
rm -rf state/
uv run python agent6.py --query-b

# Query C — Durable memory across two separate runs
rm -rf state/
uv run python agent6.py --query-c1
uv run python agent6.py --query-c2   # do NOT clear state between c1 and c2

# Query D — Multi-source asyncio synthesis
rm -rf state/
uv run python agent6.py --query-d

# Or pass any custom query
uv run python agent6.py "Your custom query here"
```

## Reset State

```bash
rm -rf state/
```

---

## Terminal Output

### Query A — Claude Shannon Wikipedia

```
[gateway] running at http://localhost:8101

[run:89f96cd9] Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions t
[memory.remember] classifying query ...
[mcp] 9 tools: ['web_search', 'fetch_url', 'get_time', 'currency_convert', 'read_file', 'list_dir', 'create_file', 'update_file', 'edit_file']

─── iter 1 ───
[memory.read]  1 hits: ['Claude Shannon birth, death, and key information theory cont']
  [perception]  [open] g1: Fetch the Wikipedia page for Claude Shannon.
  [perception]  [open] g2: Extract his birth date, death date, and three key contributions to information theory.
  [decision]    TOOL_CALL: fetch_url({'url': 'https://en.wikipedia.org/wiki/Claude_Shannon'})
  [action]      → Error executing tool fetch_url: BrowserType.launch: Executable doesn't exist ...

─── iter 2 ───
[memory.read]  2 hits: ["fetch_url(url='https://en.wikipedia.org/wiki/') → Error exec", 'Claude Shannon birth, death, and key information theory cont']
  [perception]  [open] g1: Fetch the Wikipedia page for Claude Shannon.
  [perception]  [open] g2: Extract his birth date, death date, and three key contributions to information theory.
  [decision]    TOOL_CALL: web_search({'query': 'Claude Shannon Wikipedia', 'max_results': 1})
  [action]      → {"title": "Claude Shannon - Wikipedia", "url": "https://en.wikipedia.org/wiki/Claude_Shannon",
                   "snippet": "Claude Elwood Shannon (April 30, 1916 – February 24, 2001) was an American polymath ..."}

─── iter 3 ───
[memory.read]  3 hits: [...]
  [perception]  [done] g1: Fetch the Wikipedia page for Claude Shannon.
  [perception]  [open] g2: Extract his birth date, death date, and three key contributions to information theory.
  [decision]    TOOL_CALL: fetch_url({'url': 'https://en.wikipedia.org/wiki/Claude_Shannon'})
  [action]      → Error executing tool fetch_url: BrowserType.launch: Executable doesn't exist ...

─── iter 4 ───
[memory.read]  4 hits: [...]
  [perception]  [done] g1: Fetch the Wikipedia page for Claude Shannon.
  [perception]  [open] g2: Extract his birth date, death date, and three key contributions to information theory.
  [decision]    ANSWER: Claude Shannon was born on April 30, 1916, and passed away on February 24, 2001. ...

─── iter 5 ───
[memory.read]  4 hits: [...]
  [perception]  [done] g1: Fetch the Wikipedia page for Claude Shannon.
  [perception]  [done] g2: Extract his birth date, death date, and three key contributions to information theory.
[done] all goals satisfied

============================================================
FINAL ANSWER:
Claude Shannon was born on April 30, 1916, and passed away on February 24, 2001. His three key
contributions to information theory include:
1. The founding of information theory through his 1948 paper 'A Mathematical Theory of
   Communication', which introduced the concept of the bit.
2. The development of the Shannon-Hartley theorem, which establishes the maximum rate at which
   information can be transmitted over a communications channel with a specified bandwidth in the
   presence of noise.
3. His pioneering work on digital circuit design, where he demonstrated that Boolean algebra could
   be used to simplify the arrangement of relays and switches in electronic circuits.
============================================================
```

---

### Query B — Tokyo Activities + Saturday Weather

```
[gateway] running at http://localhost:8101

[run:7781b4e3] Find 3 family-friendly things to do in Tokyo this weekend. Check Saturday's weather forecast there and tell me which one
[memory.remember] classifying query ...
[mcp] 9 tools: ['web_search', 'fetch_url', 'get_time', 'currency_convert', 'read_file', 'list_dir', 'create_file', 'update_file', 'edit_file']

─── iter 1 ───
[memory.read]  1 hits: ['User is planning family activities in Tokyo for the upcoming']
  [perception]  [open] g1: Find 3 family-friendly activities in Tokyo for the weekend
  [perception]  [open] g2: Check Tokyo's weather forecast for Saturday
  [perception]  [open] g3: Determine the most appropriate activity based on the weather
  [decision]    TOOL_CALL: web_search({'query': 'family-friendly activities in Tokyo for the weekend', 'max_results': 3})
  [action]      → {"title": "Fun Things To Do in Tokyo With Kids: 25 Family-Friendly", ...}

─── iter 2 ───
[memory.read]  2 hits: [...]
  [perception]  [done] g1: Find 3 family-friendly activities in Tokyo for the weekend
  [perception]  [open] g2: Check Tokyo's weather forecast for Saturday
  [perception]  [open] g3: Determine the most appropriate activity based on the weather
  [decision]    TOOL_CALL: web_search({'query': 'weather forecast Tokyo Saturday', 'max_results': 1})
  [action]      → {"title": "Tokyo, Japan 14 day weather forecast", "snippet": "Currently: 69 °F. Passing clouds."}

─── iter 3 ───
[memory.read]  3 hits: [...]
  [perception]  [done] g1: Find 3 family-friendly activities in Tokyo for the weekend
  [perception]  [done] g2: Check Tokyo's weather forecast for Saturday
  [perception]  [open] g3: Determine the most appropriate activity based on the weather
  [decision]    ANSWER: Given the current weather in Tokyo, which features pleasant temperatures around 69°F with passing clouds, ...

─── iter 4 ───
[memory.read]  3 hits: [...]
  [perception]  [done] g1: Find 3 family-friendly activities in Tokyo for the weekend
  [perception]  [done] g2: Check Tokyo's weather forecast for Saturday
  [perception]  [done] g3: Determine the most appropriate activity based on the weather
[done] all goals satisfied

============================================================
FINAL ANSWER:
Given the current weather in Tokyo, which features pleasant temperatures around 69°F with passing
clouds, it is an excellent time for outdoor family activities. You might consider visiting Ueno Park,
which offers a zoo, museums, and plenty of space for children to run around. Alternatively, the
Ghibli Museum or a visit to the teamLab Borderless digital art exhibit are fantastic options that
provide a mix of indoor comfort and engaging experiences for all ages.
============================================================
```

---

### Query C — Durable Memory (Run 1 + Run 2)

**Run 1** (`rm -rf state/ && uv run python agent6.py --query-c1`):

```
[gateway] running at http://localhost:8101

[run:8d75637f] My mom's birthday is 15 May 2026. Remember that and give me a calendar reminder for two weeks before and on the day.
[memory.remember] classifying query ...
[mcp] 9 tools: ['web_search', 'fetch_url', 'get_time', 'currency_convert', 'read_file', 'list_dir', 'create_file', 'update_file', 'edit_file']

─── iter 1 ───
[memory.read]  1 hits: ["My mom's birthday is 15 May 2026. Remember that and give me "]
  [perception]  [open] g1: Memorize mom's birthday as 15 May 2026
  [perception]  [open] g2: Create calendar reminder for 1 May 2026
  [perception]  [open] g3: Create calendar reminder for 15 May 2026
  [decision]    ANSWER: I have successfully memorized that your mother's birthday is on 15 May 2026. ...

─── iter 2 ───
  [perception]  [done] g1: Memorize mom's birthday as 15 May 2026
  [perception]  [open] g2: Create calendar reminder for 1 May 2026
  [perception]  [open] g3: Create calendar reminder for 15 May 2026
  [decision]    TOOL_CALL: create_file({'path': 'reminders/1_may_2026.txt', 'content': 'Calendar reminder for 1 May 2026.'})
  [action]      → Error executing tool create_file: Parent directory of 'reminders/1_may_2026.txt' does not exist

─── iter 3 ───
  [perception]  [done] g1: Memorize mom's birthday as 15 May 2026
  [perception]  [open] g2: Create calendar reminder for 1 May 2026
  [perception]  [open] g3: Create calendar reminder for 15 May 2026
  [decision]    TOOL_CALL: create_file({'path': '1_may_2026.txt', 'content': 'Calendar reminder for 1 May 2026'})
  [action]      → {"ok": true, "path": "1_may_2026.txt", "size_bytes": 32}

─── iter 4 ───
  [perception]  [done] g1: Memorize mom's birthday as 15 May 2026
  [perception]  [done] g2: Create calendar reminder for 1 May 2026
  [perception]  [open] g3: Create calendar reminder for 15 May 2026
  [decision]    TOOL_CALL: create_file({'path': '15_may_2026.txt', 'content': "Calendar reminder: Mom's birthday is on 15 May 2026."})
  [action]      → {"ok": true, "path": "15_may_2026.txt", "size_bytes": 52}

─── iter 5 ───
  [perception]  [done] g1: Memorize mom's birthday as 15 May 2026
  [perception]  [done] g2: Create calendar reminder for 1 May 2026
  [perception]  [done] g3: Create calendar reminder for 15 May 2026
[done] all goals satisfied

============================================================
FINAL ANSWER:
I have successfully memorized that your mother's birthday is on 15 May 2026. I have noted this date
in my memory for future reference. Please let me know if you would like me to assist with any
further reminders or planning for this occasion.
============================================================
```

**Run 2** (`uv run python agent6.py --query-c2` — state NOT cleared):

```
[gateway] running at http://localhost:8101

[run:3d4db792] When is mom's birthday?
[memory.remember] classifying query ...
[mcp] 9 tools: ['web_search', 'fetch_url', 'get_time', 'currency_convert', 'read_file', 'list_dir', 'create_file', 'update_file', 'edit_file']

─── iter 1 ───
[memory.read]  3 hits: ["My mom's birthday is 15 May 2026. Remember that and give me ",
                        "create_file(path='15_may_2026.txt', content=\"Calendar remind",
                        "User is asking for the date of their mother's birthday."]
  [perception]  [open] g1: Identify mom's birthday from memory
  [decision]    ANSWER: Your mother's birthday is on May 15, 2026. I have previously created a
                        calendar reminder file for this date to ensure you do not miss it.

─── iter 2 ───
[memory.read]  5 hits: [...]
  [perception]  [done] g1: Identify mom's birthday from memory
[done] all goals satisfied

============================================================
FINAL ANSWER:
Your mother's birthday is on May 15, 2026. I have previously created a calendar reminder file for
this date to ensure you do not miss it. Please let me know if you would like me to add any
additional details to that reminder.
============================================================
```

> Memory persisted across process runs. Run 2 answered in **2 iterations** with zero tool calls — directly from `state/memory.json`.

---

### Query D — Python asyncio Best Practices Synthesis

```
[gateway] running at http://localhost:8101

[run:29f32917] Search for 'Python asyncio best practices', read the top 3 results, and give me a short numbered list of the advice they
[memory.remember] classifying query ...
[mcp] 9 tools: ['web_search', 'fetch_url', 'get_time', 'currency_convert', 'read_file', 'list_dir', 'create_file', 'update_file', 'edit_file']

─── iter 1 ───
[memory.read]  1 hits: ['Researching and summarizing Python asyncio best practices fr']
  [perception]  [open] g1: Search for Python asyncio best practices
  [perception]  [open] g2: Read the top 3 search results
  [perception]  [open] g3: List the best practices they agree on
  [decision]    TOOL_CALL: web_search({'query': 'Python asyncio best practices', 'max_results': 3})
  [action]      → {"title": "Python's asyncio: A Hands-On Walkthrough – Real Python", "url": "https://realpython.com/async-io-python/", ...}

─── iter 2 ───
  [perception]  [done] g1: Search for Python asyncio best practices
  [perception]  [open] g2: Read the top 3 search results
  [perception]  [open] g3: List the best practices they agree on
  [decision]    TOOL_CALL: fetch_url({'url': 'https://realpython.com/async-io-python/'})
  [action]      → Error executing tool fetch_url: BrowserType.launch: Executable doesn't exist ...

─── iter 3 ───
  [perception]  [done] g1: Search for Python asyncio best practices
  [perception]  [open] g2: Read the top 3 search results
  [perception]  [open] g3: List the best practices they agree on
  [decision]    TOOL_CALL: web_search({'query': 'Python asyncio best practices', 'max_results': 3})
  [action]      → {"title": "Asyncio best practices - Async-SIG - Discussions on Python.org", ...}

─── iter 4 ───
  [decision]    TOOL_CALL: web_search({'query': 'Python asyncio best practices', 'max_results': 3})
  [action]      → {"title": "Asyncio best practices - Async-SIG - Discussions on Python.org", ...}

─── iter 5 ───
  [decision]    ANSWER: The top search results for Python asyncio best practices include a
                        comprehensive guide from Real Python ...

─── iter 6 ───
  [perception]  [done] g1: Search for Python asyncio best practices
  [perception]  [done] g2: Read the top 3 search results
  [perception]  [open] g3: List the best practices they agree on
  [decision]    ANSWER: Based on community discussions and technical documentation, the following
                        are widely agreed-upon best practices for Python asyncio: ...

─── iter 7 ───
  [perception]  [done] g1: Search for Python asyncio best practices
  [perception]  [done] g2: Read the top 3 search results
  [perception]  [done] g3: List the best practices they agree on
[done] all goals satisfied

============================================================
FINAL ANSWER:
Based on community discussions and technical documentation, the following are widely agreed-upon
best practices for Python asyncio:
1. Avoid blocking the event loop by ensuring that CPU-bound tasks are offloaded to executors or
   processes, keeping the loop free for I/O operations.
2. Always use 'async with' or 'async for' context managers and iterators to ensure that resources
   like network connections or file handles are properly closed.
3. Prefer using high-level APIs like 'asyncio.run()' for managing the lifecycle of the event loop
   rather than manually creating and closing loops.
4. Be cautious with task cancellation and ensure that your code handles 'asyncio.CancelledError'
   gracefully to prevent resource leaks or inconsistent states.
============================================================
```

---

## Design Notes

| Role | File | LLM? | Notes |
|------|------|------|-------|
| Memory | memory.py | write only | `remember()` classifies via Gemini; `read()` is pure Python keyword overlap |
| Perception | perception.py | yes | `temperature=1.0` prevents Gemini looping; integer artifact indices prevent hallucinated handles |
| Decision | decision.py | yes | `response_format` JSON schema (not native tools); `temperature=0.2` |
| Action | action.py | no | Pure MCP dispatch; 4KB threshold → `ActionResult` typed return |

All LLM calls: `provider="g"`, `model="gemini-3.1-flash-lite"` via LLM Gateway V3 at `http://localhost:8101`.

### Pydantic v2 Contracts at Every Role Boundary

| Schema | Used by |
|--------|---------|
| `MemoryItem` | Memory → Perception, Memory → Decision |
| `Goal` | Perception → agent loop |
| `Observation` | Perception → agent loop |
| `ToolCall` | Decision → Action |
| `DecisionOutput` | Decision → agent loop |
| `ActionResult` | Action → agent loop |
| `ActionEvent` / `AnswerEvent` / `HistoryEvent` | agent loop → Memory, Perception, Decision |

### Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| LLM provider | `provider="g"`, `model="gemini-3.1-flash-lite"` everywhere | Assignment requirement |
| Decision tool dispatch | `response_format` JSON schema (not native tools) | More reliable with flash-lite |
| `tool_arguments_json` | `{"type": "string"}` in schema | Gemini can't fill free-form `{"type": "object"}` — encode as JSON string, parse in Python |
| Perception temperature | 1.0 | Gemini 3.1 flash-lite loops at temp=0 on structured output |
| Decision temperature | 0.2 | Stable JSON without temp=0 repetition risk |
| Artifact threshold | 4096 bytes | Large results (Wikipedia pages) go to content-addressable store |
| Goal identity | Positional (loop assigns IDs, LLM never writes them) | Prevents hallucinated stale IDs |
| Artifact reference | Integer index in prompt → mapped to handle in Python | Prevents hallucinated `art:` strings |
| Retry on 429/502/503 | Exponential backoff (10s, 20s, 40s) | Gemini free tier is 15 RPM |
