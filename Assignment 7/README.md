# EAG V3 — Session 7: Agentic System with Vector Memory

A multi-tier agentic system built for EAG V3 Session 7. It extends the Session 6 agent with FAISS-backed vector memory, document indexing tools, and a full-stack IPO research web application.

---

## Overview

The project has three major components:

### 1. Agent Core (`agent_core/`)
A four-layer cognitive loop that runs up to 20 iterations per query:

```
memory.read → perception.observe → decision.next_step → action.execute → memory.record_outcome
```

- **Perception** decomposes the query into goals, tracks completion, and decides when to attach artifact bytes to the current goal.
- **Memory** stores typed items (`fact`, `preference`, `tool_outcome`, `scratchpad`). In Session 7, reads go through FAISS vector similarity first and fall back to keyword search. Writes embed the descriptor and append to the FAISS index.
- **Decision** makes a single LLM call per iteration: either picks a tool or emits the final answer.
- **Action** dispatches MCP tool calls and pushes large results (>4 KB) to the artifact store, returning a handle.

**11 MCP tools:** `web_search`, `fetch_url`, `get_time`, `currency_convert`, `read_file`, `list_dir`, `create_file`, `update_file`, `edit_file`, `index_document` *(new in S7)*, `search_knowledge` *(new in S7)*

**Research papers** available in `agent_core/sandbox/papers/`: `attention.md`, `cot.md`, `dpo.md`, `lora.md`, `react.md`

### 2. LLM Gateway (`gateway/`)
A FastAPI service on port **8107** that sits between the agent and LLM providers.

- **Worker pool** — 4 Gemini model variants as independent virtual providers (`gemini`, `gemini-lite`, `gemini-35`, `gemini-31-lite`), each with its own rate-limit state for automatic failover. Supports Ollama, NVIDIA, Groq, Cerebras, OpenRouter, GitHub as additional workers.
- **Router pool** — Small models classify incoming requests into `TINY` / `LARGE` / `HUGE` tiers, routing to the most cost-efficient worker. The router only ever sees token count and an 800-char sample — never the full prompt or schema.
- **Embedding endpoint** — `POST /v1/embed` using Ollama (local, free) with Gemini as fallback. Fixed 768-dim model. Changing the model invalidates all existing FAISS indices.
- **Dashboard** — `http://localhost:8107` — live provider status, rate-limit state, call logs.

### 3. IPO Explorer (`ipo_explorer/`)
A full-stack web application on port **8200** demonstrating the agent in a real research context.

- **Corpus** — 63 Indian IPOs (2020–2024) with company metadata, Wikipedia links, and rich descriptions.
- **Indexing** — Select a year range, hit "Index", and the app crawls each IPO's website, chunks text, embeds it, and stores facts in memory — streamed live over SSE.
- **Querying** — Ask any question about the indexed companies. The agent's iteration trace (goals, tool calls, memory hits) is streamed to the UI in real time.
- **12 MCP tools** — All 11 from agent_core plus `index_ipo_company(symbol)`.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User / Browser                          │
└───────────────┬─────────────────────────────┬───────────────────┘
                │ CLI query                   │ HTTP / SSE
         ┌──────▼──────┐               ┌──────▼──────┐
         │  agent7.py  │               │ ipo_explorer│
         │  (CLI mode) │               │  /server.py │
         └──────┬──────┘               └──────┬──────┘
                │                             │
         ┌──────▼─────────────────────────────▼──────┐
         │              agent_core                    │
         │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
         │  │Perception│→ │ Decision │→ │  Action  │ │
         │  └──────────┘  └──────────┘  └────┬─────┘ │
         │  ┌──────────┐                      │MCP    │
         │  │  Memory  │ ←────────────────────┘       │
         │  │(FAISS +  │    ┌──────────────────────┐  │
         │  │ keyword) │    │     MCP Server       │  │
         │  └──────────┘    │  11 tools (web, file,│  │
         │  ┌──────────┐    │  index, search, ...)  │  │
         │  │Artifacts │    └──────────────────────┘  │
         │  └──────────┘                               │
         └────────────────────┬────────────────────────┘
                              │ HTTP
         ┌────────────────────▼────────────────────────┐
         │              LLM Gateway :8107              │
         │  ┌──────────────────┐  ┌──────────────────┐ │
         │  │  Router Pool     │  │   Worker Pool    │ │
         │  │ (tier classify)  │  │ gemini / lite /  │ │
         │  │                  │  │ 35 / 31-lite /   │ │
         │  └──────────────────┘  │ ollama / groq ...│ │
         │  ┌──────────────────┐  └──────────────────┘ │
         │  │  /v1/embed       │  (independent rate    │
         │  │  Ollama→Gemini   │   states per model)   │
         │  └──────────────────┘                       │
         └─────────────────────────────────────────────┘
```

**Data flow per iteration:**
1. `memory.read(query)` → FAISS vector search → keyword fallback → top-k `MemoryItem`s
2. `perception.observe(query, hits, history, goals)` → updated `Observation` (goal list + artifact attachment hint)
3. `decision.next_step(goal, memory_hits, artifact_bytes?)` → `ToolCall` or `Answer`
4. `action.execute(tool_call)` → result string + optional `artifact_id`
5. `memory.record_outcome(tool_call, result)` → embeds descriptor → appends to FAISS

---

## Setup

### Prerequisites
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`
- A `GEMINI_API_KEY` — only required key for a basic run

### Environment variables

Create a `.env` file in the `Assignment 7/` root:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here   # optional; falls back to DuckDuckGo
```

Optional gateway provider keys (add any you have):
```bash
GROQ_API_KEY=...
NVIDIA_API_KEY=...
CEREBRAS_API_KEY=...
OPEN_ROUTER_API_KEY=...
GITHUB_ACCESS_TOKEN=...
OLLAMA_URL=http://localhost:11434         # if Ollama is running locally
```

---

## Usage

### LLM Gateway

The gateway must be running before starting the agent or the app.

```bash
cd gateway
./run.sh          # auto-creates .venv on first run, starts on port 8107
# or
uv run main.py
```

**Verify:**
```bash
curl http://localhost:8107/v1/providers    # lists all registered providers
curl http://localhost:8107/v1/status       # rate-limit state per provider
```

Open `http://localhost:8107` for the live dashboard.

---

### Agent (CLI)

```bash
cd agent_core
uv run agent7.py "What is the current time in Tokyo and Bangalore?"
```

The agent will auto-start the gateway if it isn't already running.

**Example queries:**
```bash
uv run agent7.py "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and summarise his contributions."
uv run agent7.py "Index the file papers/attention.md and tell me the three key contributions of the Transformer."
uv run agent7.py "My mom's birthday is 15 May 2026. Remember that and create reminders."
```

**Clear memory between runs** (optional):
```bash
python3 -c "import sys; sys.path.insert(0,'agent_core'); from memory import clear; clear()"
```

---

### IPO Explorer App

```bash
cd ipo_explorer
uv run uvicorn server:app --port 8200 --reload
```

Open `http://localhost:8200` in a browser.

1. **Welcome** — enter a year range (e.g. 2022–2024) and click "Start Setup"
2. **Setup** — the app indexes each IPO company from the corpus; progress streams live
3. **Query** — ask questions like:
   - *"Which fintech IPOs had the best first-day gains?"*
   - *"Compare Zomato and Swiggy's IPO performance."*
   - *"What sectors dominated Indian IPOs in 2023?"*

The agent's iteration trace (goals, tool calls, memory hits, answer) is shown in real time.

---

## Running Test Queries

`run_tests.sh` runs all 10 queries from `Test Queries.json` sequentially, clears memory at the right points, and prints a pass/fail summary.

```bash
cd "/Users/mayankchittora/Documents/EAG V3/Assignment 7"

# Run all queries A–H
./run_tests.sh

# Run only specific queries (comma-separated IDs)
./run_tests.sh --only A
./run_tests.sh --only A,B,C

# Skip memory clears (useful when debugging a single query mid-run)
./run_tests.sh --no-clear
```

**Memory clear policy:**
- Memory is wiped before every `run: 1` entry.
- **C-run-2** ("When is mom's birthday?") and **F-run-2** ("Across the papers I have indexed…") intentionally depend on memory from their `run: 1` — the script skips the clear for those.

---

## Test Query Results

> The complete execution logs and results for all test queries are documented in [Test Queries Results.txt](Test%20Queries%20Results.txt).

| Query | ID | Expected Iterations | Actual Iterations | Notes |
|-------|----|--------------------:|------------------:|-------|
| Fetch Wikipedia + extract facts | A-run-1 | 3 | 3 | |
| Tokyo weekend activities + weather | B-run-1 | 8 | 5 | |
| Save birthday reminder | C-run-1 | 4 | 4 | |
| Recall birthday from memory | C-run-2 | 3 | 2 | Memory persistence test |
| Search asyncio best practices | D-run-1 | 6 | 5 | |
| Index attention.md + extract | E-run-1 | 5 | 5 | |
| Index all papers + count chunks | F-run-1 | 11 | 9 | |
| Query indexed papers (CoT) | F-run-2 | 3 | 4 | Knowledge base test |
| Cross-paper: credit assignment | G-run-1 | 4 | 4 | Requires F-run-1 |
| Compare ReAct vs CoT papers | H-run-1 | 3 | 5 | Requires F-run-1 |

---

## IPO Explorer App — Query Results

> Results are shown in the YouTube video attached below.

- [IPO Explorer Demo](https://youtu.be/VMJY3HWHOJY)

| # | Query |
|---|-------|
| 1 | Based on the indexed IPO corpus, which company manufactures environmentally conscious materials for internal design or construction without harmful aldehydes? |
| 2 | Based on the indexed IPO corpus, which business provides sustainable two-wheeled transportation options for environment-minded city travelers in Bharat? |
| 3 | Based on the indexed IPO corpus, identify the diagnostic service provider operating radiology and pathology centers in government hospitals under public-private partnerships in rural Bharat. |
| 4 | Based on the indexed IPO corpus, which specialty chemical company listed in 2021 had the highest percentage increase from its issue price to its listing price? |
| 5 | Based on the indexed IPO corpus, which corporate entity supplies mapping APIs and IoT fleet management tools to automotive manufacturers and government agencies in India? |

---
