# DAG-Based Multi-Agent Orchestrator

## Overview

This is a **growing-graph multi-agent orchestrator** where the agent's loop is a NetworkX directed acyclic graph (DAG) of typed skills. Instead of a single iterative loop, the agent decomposes every query into a graph of specialised nodes that execute in parallel wherever dependencies allow.

**How it works:**
- A **Planner** node reads the user query and emits the initial DAG — one node per task, with dependencies expressed as edges.
- An **Executor** continuously finds nodes whose predecessors have all completed and runs them concurrently via `asyncio.gather`.
- As nodes complete they can extend the graph further, so the structure visible at the start is rarely the final structure at termination.
- The graph and every node's state are persisted to disk after each completion; a killed run can be resumed cleanly.

**Skills available:**

| Skill | Role |
|-------|------|
| `planner` | Decomposes the user query into a DAG; emits recovery sub-graphs on failure |
| `researcher` | Multi-step web search and page fetching |
| `retriever` | Vector search over the agent's indexed knowledge base (FAISS) |
| `distiller` | Extracts structured fields from raw text |
| `summariser` | Condenses long content |
| `critic` | Pass/fail evaluation of an upstream node's output |
| `coder` | Generates Python code; automatically routes to `sandbox_executor` |
| `sandbox_executor` | Runs code in a subprocess and returns stdout, stderr, and exit code |
| `sentiment_analyser` | Classifies text sentiment as positive, negative, neutral, or mixed |
| `formatter` | Renders the final user-facing answer (terminal node) |

**Key architectural properties:**
- **Parallel fan-out**: independent sub-tasks (e.g. researching three cities) run concurrently; wall-clock equals the slowest branch, not the sum.
- **Critic auto-insertion**: skills tagged `critic: true` in `agent_config.yaml` automatically get a Critic node on every outgoing edge.
- **Code execution**: the Coder → SandboxExecutor chain lets the agent ground numerical answers in real Python computation.
- **Memory**: FAISS vector search is performed once at session start; the same hits are threaded into every skill's prompt.
- **Failure recovery**: transient errors skip silently; upstream failures trigger a recovery Planner (capped at one re-plan per branch).

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com/) with the `nomic-embed-text` model pulled
- At least one LLM provider API key (Gemini, Groq, NVIDIA NIM, Cerebras, OpenRouter, or GitHub Models)

```bash
ollama pull nomic-embed-text
```

### 1. Configure API keys

```bash
cp .env.example .env
# Edit .env and add the keys you have
```

### 2. Install dependencies

```bash
cd gateway && uv sync && cd ..
cd code    && uv sync && cd ..
```

### 3. Start the LLM gateway

The gateway is a FastAPI service that routes requests to provider backends, handles retries, and logs per-skill token spend.

```bash
cd gateway
uv run main.py
# Boots on http://localhost:8108
# Verify: curl http://localhost:8108/v1/routers
```

### 4. Run the agent

```bash
cd code
uv run python flow.py "your query here"
```

A successful first run prints one line per node as it completes and ends with the final answer. Sessions are saved to `code/state/sessions/<session-id>/`.

### Replay a completed session

```bash
cd code
uv run python replay.py <session-id>
```

Walks through each node one at a time, showing the exact prompt sent and the output received.

### Resume a killed session

```bash
cd code
uv run python flow.py --resume <session-id>
```

Resets any `running` nodes to `pending` and continues from where the run was killed. Completed nodes are not re-executed.

### Run the base query validation suite

```bash
cd code
uv run python run_test_queries.py          # runs 4 of the 5 base queries
uv run python run_test_queries.py --all    # includes the resume query (run manually)
uv run python run_test_queries.py --id hello  # single query by id
```

Prints a PASS/FAIL table with node count, wall-clock, and answer keyword checks. Exits 0 on all pass, 1 on any failure.

### Run the additional query suite

```bash
cd code
uv run python run_additional_queries.py            # all additional queries
uv run python run_additional_queries.py --id <id>  # single query
uv run python run_additional_queries.py --dry-run  # list queries without running
```

Prints a per-query report (node execution table, wall-clock, final answer) and writes full results to `additional_queries_results.json`.

---

## Project Layout

```
Assignment 8/
├── README.md
├── .env.example
│
├── code/                        ← the agent; run all commands from here
│   ├── flow.py                  ← orchestrator (Graph + Executor + CLI)
│   ├── skills.py                ← skill registry, prompt rendering, run_skill
│   ├── recovery.py              ← failure classification + critic-fail splice
│   ├── persistence.py           ← session writes (graph.json + per-node JSON)
│   ├── mcp_runner.py            ← multi-turn tool-use loop wrapper
│   ├── sandbox.py               ← subprocess Python runner
│   ├── replay.py                ← stdin-driven trace viewer
│   ├── schemas.py               ← AgentResult, NodeSpec, NodeState, MemoryItem
│   ├── agent_config.yaml        ← skills catalogue (yaml entries + prompt paths)
│   ├── prompts/                 ← one .md per skill
│   │   ├── planner.md
│   │   ├── researcher.md
│   │   ├── retriever.md
│   │   ├── distiller.md
│   │   ├── summariser.md
│   │   ├── critic.md
│   │   ├── coder.md
│   │   ├── sandbox_executor.md
│   │   ├── formatter.md
│   │   └── sentiment_analyser.md
│   ├── test_queries.json        ← 5 base validation queries with expected outcomes
│   ├── run_test_queries.py      ← runs + validates base queries
│   ├── additional_queries.json  ← 8 extended queries (parallel, critic, coder, sentiment)
│   ├── run_additional_queries.py← runs + reports extended queries
│   ├── mcp_server.py            ← MCP tools: web_search, fetch_url, search_knowledge
│   ├── memory.py                ← FAISS-backed memory service
│   ├── vector_index.py          ← FAISS index wrapper
│   ├── artifacts.py             ← artifact storage
│   ├── sandbox/papers/          ← five indexed knowledge-base documents
│   └── tests/
│       └── test_recovery.py     ← 22 unit tests for failure classification + critic splice
│
└── gateway/                     ← LLM gateway (FastAPI, port 8108)
    ├── main.py
    ├── client.py
    ├── providers.py / router.py / embedders.py / db.py / cache.py
    ├── agent_routing.yaml       ← pins skill names to preferred providers
    └── pyproject.toml
```

---

## Example Queries

### Base Queries

These five queries cover the core architecture properties. Run them with `run_test_queries.py` or individually with `flow.py`.

| ID | Description | Query | Expected Skills | Actual Skills | Output |
|----|-------------|-------|-----------------|---------------|--------|
| `hello` | Minimum DAG — planner emits formatter directly, no tools | `Say hello.` | planner → formatter | | |
| `shannon` | Sequential DAG with Distiller + auto-inserted Critic | `Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.` | planner → researcher → distiller → critic → formatter | | |
| `three_cities` | Parallel fan-out (3 researchers) + Coder + SandboxExecutor | `Find the populations of London, Paris, Berlin and tell me which two are closest in size.` | planner → researcher×3 → coder → sandbox_executor + formatter | | |
| `graceful_failure` | Planner fails fast with a degenerate 2-node DAG | `Read /nonexistent/path.txt and tell me what's in it.` | planner → formatter | | |
| `resume` | Resumable execution — kill mid-run, resume with `--resume` | `For Lagos, Cairo, and Kinshasa, find current populations and growth rates and tell me which is growing fastest.` | planner → researcher×3 → coder → sandbox_executor + formatter | | |

---

### Additional Queries

These eight queries exercise specific capabilities. Run them with `run_additional_queries.py` or individually with `flow.py`.

#### Parallel Fan-out

| ID | Query | Expected Skills | Actual Skills | Output |
|----|-------|-----------------|---------------|--------|
| `parallel_currencies` | `Find the current exchange rates of USD to EUR, USD to JPY, and USD to GBP. Then tell me which currency gives the most value per dollar.` | planner → researcher×3 → formatter | | |
| `parallel_tech_companies` | `Find the current market capitalisation of Apple, Microsoft, and Google (Alphabet). Rank them from largest to smallest.` | planner → researcher×3 → formatter | | |

#### Critic Verdict

| ID | Query | Expected Outcome | Actual Skills | Output |
|----|-------|-----------------|---------------|--------|
| `critic_pass` | `Fetch https://en.wikipedia.org/wiki/Ada_Lovelace and extract her birth year, death year, and main contribution to computing.` | Critic returns **pass** — all fields present on the page | | |
| `critic_fail_trigger` | `Fetch https://en.wikipedia.org/wiki/Ada_Lovelace and extract her birth year, death year, her father's full name, and her exact birthplace address. The distiller output must contain all four fields — the critic should fail if the birthplace address is missing.` | Critic returns **fail** (street-level address not on Wikipedia) → recovery Planner fires | | |

#### Coder Computation

| ID | Query | Expected Skills | Actual Skills | Output |
|----|-------|-----------------|---------------|--------|
| `coder_compound_interest` | `Calculate how much $10,000 invested at 7% annual interest compounded monthly would grow to after 20 years. Show the final amount and total interest earned.` | planner → coder → sandbox_executor → formatter | | |
| `coder_fibonacci` | `Compute the first 15 Fibonacci numbers and find which one is closest to 500.` | planner → coder → sandbox_executor → formatter | | |

#### Sentiment Analyser

| ID | Query | Expected Skills | Actual Skills | Output |
|----|-------|-----------------|---------------|--------|
| `sentiment_product_reviews` | `Search the web for recent user reviews of the iPhone 16 and analyse the overall sentiment. Are customers mostly positive, negative, or mixed about it?` | planner → researcher → sentiment_analyser → formatter | | |
| `sentiment_climate_article` | `Fetch https://en.wikipedia.org/wiki/Climate_change and analyse the sentiment of the opening content. Is the language alarming, neutral, or optimistic?` | planner → researcher → sentiment_analyser → formatter | | |

---

## Troubleshooting

| Symptom | Where to look |
|---------|---------------|
| `[gateway] launching … failed to start within 45s` | Start the gateway manually: `cd gateway && uv run main.py`. Check stderr for missing API keys or port 8108 already in use. |
| `503 Service Unavailable` from gateway | All configured providers are in cooldown or unconfigured. Add another API key to `.env`, or wait a minute and retry. |
| `sandbox_executor` reports `no code in upstream coder output` | The Coder's prompt did not emit the expected `{"code": "...", "rationale": "..."}` JSON. Run `replay.py <sid>` and inspect the coder node's `prompt_sent`. |
| Final answer is short or wrong | Run `replay.py <sid>` and read each node's `prompt_sent` and `output` fields to trace where the reasoning went off. |
| Resume fails with `no graph.pkl on disk` | The session directory under `state/sessions/<sid>/` may be missing or corrupted. Start a fresh run instead. |
