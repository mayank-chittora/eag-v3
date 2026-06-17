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

| Description | Query | Expected Skills | Actual Skills | Output |
|-------------|-------|-----------------|---------------|--------|
| Minimum DAG — planner emits formatter directly, no tools | `Say hello.` | planner → formatter | planner → formatter | `Hello! How can I help you today?` |
| Sequential DAG with Distiller + auto-inserted Critic | `Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his birth date, death date, and three key contributions to information theory.` | planner → researcher → distiller → critic → formatter | planner → researcher → distiller → critic → formatter | `Claude Shannon was born on April 30, 1916, and passed away on February 24, 2001. His three key contributions to information theory include: 1) The development of information theory through his seminal paper 'A Mathematical Theory of Communication'; 2) The establishment of the 'bit' as the fundamental unit of information; and 3) The application of Boolean logic to the design of digital circuits.` |
| Parallel fan-out (3 researchers) + Coder + SandboxExecutor | `Find the populations of London, Paris, Berlin and tell me which two are closest in size.` | planner → researcher×3 → coder → sandbox_executor + formatter | planner → researcher×3 → coder → sandbox_executor + formatter | `Based on current metropolitan area population estimates, the populations of the three cities are approximately 9.1 million for London, 11.418 million for Paris, and 4.0 million for Berlin. Comparing these figures, the two cities closest in size are London and Paris, with a population difference of approximately 2.318 million.` |
| Planner fails fast with a degenerate 2-node DAG | `Read /nonexistent/path.txt and tell me what's in it.` | planner → formatter | planner → formatter | `I cannot fulfill this request because I do not have access to local file systems or private resources, and the requested file path does not exist within my available data.` |
| Resumable execution — kill mid-run, resume with `--resume` | `For Lagos, Cairo, and Kinshasa, find current populations and growth rates and tell me which is growing fastest.` | planner → researcher×3 → coder → sandbox_executor + formatter | planner → researcher×3 → coder → sandbox_executor + formatter | `Here is the current population and annual growth rate data for the three cities: City, Estimated Population, Annual Growth Rate; Lagos, ~16.5M – 17.1M, 3.7% – 3.75%; Cairo, ~23.5M (2026), 1.99% – 2.00%; Kinshasa, ~18.5M – 18.6M (2026), 4.36% – 5.13%. Kinshasa is the fastest-growing city among the three, with an average annual growth rate estimated between 4.36% and 5.13%.` |

---

### Additional Queries

These eight queries exercise specific capabilities. Run them with `run_additional_queries.py` or individually with `flow.py`.

#### Parallel Fan-out

| Query | Skills | Output |
|-------|-----------------|--------|
| `Find the current exchange rates of USD to EUR, USD to JPY, and USD to GBP. Then tell me which currency gives the most value per dollar.` | planner → researcher×3 → coder → formatter + sandbox_executor | `The current exchange rates for 1 USD are as follows: 1 USD = 0.86 EUR, 1 USD = 159.38 JPY, and 1 USD = 0.7457 GBP. Based on these rates, the Japanese Yen (JPY) provides the most value per dollar with a numerical rate of 159.38.` |
| `Find the current market capitalisation of Apple, Microsoft, and Google (Alphabet). Rank them from largest to smallest.` | planner → researcher×3 → coder → formatter + sandbox_executor | ` Based on current market data, here is the ranking of Apple, Microsoft, and Alphabet (Google) by market capitalization, from largest to smallest: 1. Apple: $4.60 trillion, 2. Alphabet: $4.36 trillion, 3. Microsoft: $2.90 trillion` |

#### Critic Verdict

| Query | Skills | Output |
|-------|---------------|--------|
| `Fetch https://en.wikipedia.org/wiki/Ada_Lovelace and extract her birth year, death year, and main contribution to computing.` | planner → researcher → distiller → critic (pass) → formatter | `Ada Lovelace was born in 1815 and passed away in 1852. Her main contribution to computing was writing the first computer program intended for Charles Babbage's Analytical Engine.` |
| `Fetch https://en.wikipedia.org/wiki/Ada_Lovelace and extract her birth year, death year, her father's full name, and her exact birthplace address.` | planner → researcher → distiller → critic (fail) → planner → researcher → distiller → critic (fail) → planner → researcher → distiller → critic (fail) → formatter | `The requested information for Ada Lovelace is as follows: she was born in 1815 and died in 1852. Her father was George Gordon Byron (Lord Byron), and she was born at 12 Piccadilly Terrace, London.` |

#### Coder Computation

| Query | Skills | Output |
|-------|---------------|--------|
| `Calculate how much $10,000 invested at 7% annual interest compounded monthly would grow to after 20 years. Show the final amount and total interest earned.` | planner → coder → formatter + sandbox_executor | `If you invest $1,000 at a 7% annual interest rate compounded monthly for 20 years, your investment will grow to a final amount of $4,038.74. The total interest earned over this period will be $3,038.74.` |
| `Compute the first 15 Fibonacci numbers and find which one is closest to 500.` | planner → coder → formatter + sandbox_executor | `The first 15 Fibonacci numbers are: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, and 377. Among these, the number closest to 500 is 377.` |

#### Sentiment Analyser

| Query | Skills | Output |
|-------|---------------|--------|
| `Search the web for recent user reviews of the iPhone 16 and analyse the overall sentiment. Are customers mostly positive, negative, or mixed about it?` | planner → researcher → sentiment_analyser → formatter | `The overall sentiment toward the iPhone 16 is positive. Users generally view the device as a solid, reliable, and well-rounded upgrade, specifically highlighting improved battery life, enhanced camera capabilities, and significant performance benefits. While there is some ongoing debate regarding the value proposition of the Pro models, the general consensus is that the iPhone 16 successfully narrows the gap in features between standard and premium models.` |

---

## Troubleshooting

| Symptom | Where to look |
|---------|---------------|
| `[gateway] launching … failed to start within 45s` | Start the gateway manually: `cd gateway && uv run main.py`. Check stderr for missing API keys or port 8108 already in use. |
| `503 Service Unavailable` from gateway | All configured providers are in cooldown or unconfigured. Add another API key to `.env`, or wait a minute and retry. |
| `sandbox_executor` reports `no code in upstream coder output` | The Coder's prompt did not emit the expected `{"code": "...", "rationale": "..."}` JSON. Run `replay.py <sid>` and inspect the coder node's `prompt_sent`. |
| Final answer is short or wrong | Run `replay.py <sid>` and read each node's `prompt_sent` and `output` fields to trace where the reasoning went off. |
| Resume fails with `no graph.pkl on disk` | The session directory under `state/sessions/<sid>/` may be missing or corrupted. Start a fresh run instead. |
