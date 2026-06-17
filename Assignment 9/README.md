# Browser-Capable Growing DAG Multi-Agent Orchestrator

## Overview

This project extends the growing-graph orchestrator with an interactive **Browser skill** that can perform real actions on JavaScript-rendered web pages — clicks, form fills, filter interactions, multi-page navigation — that static scraping tools like `web_search` and `fetch_url` cannot handle.

### What It Does

Given a natural-language query, the system:
1. **Plans** — a Planner LLM decomposes the query into a directed acyclic graph (DAG) of skills
2. **Executes** — skills run asynchronously; the graph grows dynamically as results arrive
3. **Browses** — the Browser skill interacts with live websites using a 4-layer cascade
4. **Extracts** — a Distiller skill pulls structured fields from raw page content
5. **Validates** — a Critic skill checks output quality; failures trigger automatic re-planning
6. **Formats** — a Formatter skill renders the final answer as a structured comparison table

### The 4-Layer Browser Cascade

The Browser skill tries the cheapest path first and escalates only when needed:

| Layer | Method | When Used |
|-------|--------|-----------|
| 1. Extract | `trafilatura` static HTML fetch | Static pages with no interactive goal |
| 2. Deterministic | CSS selectors from metadata | When explicit selectors are provided |
| 3. A11y | Playwright + accessibility tree (text-only) | Interactive goals (click, filter, sort) |
| 4. Vision | Playwright + Set-of-Marks screenshot | When A11y fails or page is visual-only |

When a layer's result is insufficient (e.g., the goal contains interactive verbs like "click" or "filter"), the skill automatically escalates to the next layer. Gateway blocks (CAPTCHA, login walls) are detected early and reported with `error_code="gateway_blocked"` for recovery.

### Growing DAG Design

- The **Planner** seeds the initial graph with skill nodes and typed edges
- Nodes execute when all their upstream dependencies are satisfied
- The **Critic** is auto-inserted after key nodes and validates outputs
- On failure, the **Planner** is re-invoked with the prior-complete context to grow new recovery paths — without re-running completed nodes
- **FAISS-backed memory** stores intermediate results and retrieves relevant facts for each skill's prompt

### Available Skills

| Skill | Role |
|-------|------|
| `planner` | Decomposes query into DAG; handles recovery re-planning |
| `researcher` | Multi-step web research using search and fetch tools |
| `browser` | Interactive web browsing via 4-layer cascade |
| `distiller` | Structured field extraction from raw text |
| `coder` | Generates and executes Python code in a sandbox |
| `critic` | Pass/fail quality gate (deterministic, temperature=0) |
| `formatter` | Renders final answer to user |
| `summariser` | Condenses long content for downstream skills |

### Output

Each run produces:
- A **structured comparison table** as the final answer
- An **8-section replay report** (via `report.py`) containing: user goal, planner DAG, browser path chosen, browser actions taken, page-state logs, extracted data, comparison table, turn count and cost summary

---

## Setup

### Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) package manager
- API keys for at least one LLM provider (Gemini free tier works)

### 1. Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```
GEMINI_API_KEY=...
TAVILY_API_KEY=...        # optional, for web search
# Add other provider keys as needed (GROQ, CEREBRAS, OPENROUTER, etc.)
```

### 2. Set Up the Gateway

```bash
cd gateway
uv sync
```

The gateway (FastAPI LLM router on port 8109) starts automatically when `flow.py` runs. To start it manually:

```bash
uv run python main.py
```

### 3. Set Up the Agent

```bash
cd agent/code
uv sync
uv run playwright install chromium
```

### 4. Run a Query

```bash
cd agent/code
uv run python flow.py "your query here"
```

The gateway auto-starts if not already running. Session data is saved to `state/sessions/<session_id>/`.

### 5. View Reports

```bash
# List all sessions
uv run python report.py --list

# View the 8-section replay report for a session
uv run python report.py <session_id>
```

---

## Sample Queries

### Compare 3 Sci-Fi Movies on IMDb (Rating > 7.0)

**Query:**

```bash
uv run python flow.py "Compare 3 movies on IMDb in the Sci-Fi genre with IMDb rating above 7.0."
```

**Results:**

session s8-e31555c5  ─  query: Compare 3 movies on IMDb in the Sci-Fi genre with IMDb rating above 7.0.

[n:1] planner            complete (6.9s)
[n:2] browser            complete (37.1s)
[n:3] distiller          complete (4.7s)
[n:5] critic             complete (4.3s)
  ↪ critic-fail recovery: planner node n:6 for n:3 (1/2)
[n:6] planner            complete (5.6s)
[n:7] browser            complete (33.8s)
[n:8] distiller          complete (5.4s)
[n:10] critic             complete (4.3s)
[n:9] formatter          complete (5.2s)


FINAL: Here is a comparison of three highly-rated Sci-Fi movies on IMDb:

1. Inception (Rating: 8.8): A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.
2. Interstellar (Rating: 8.7): When Earth becomes uninhabitable in the future, a farmer and ex-NASA pilot, Joseph Cooper, is tasked to pilot a spacecraft, along with a team of researchers, to find a new planet for humans.
3. The Matrix (Rating: 8.7): When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the sh


**Output Analysis:**
Refer [Output Report](agent/code/state/sessions/s8-e31555c5/report.md)
