# Multi-agent Orchestrator with Computer-Use Skill

A **Computer-Use skill** that slots into the multi-agent orchestrator and drives real desktop applications via [`cua-driver`](https://github.com/trycua/cua). The skill follows the same five-layer cascade pattern as the Browser skill and uses the gateway for all LLM and vision calls.

---

## Architecture

### The Five-Layer Cascade

The cascade tries the cheapest layer first and escalates only when the current layer cannot complete the goal.

```
┌────────────────────────────────────────────────────────────────┐
│  ComputerSkill.run(NodeSpec)                                   │
│                                                                │
│  Pre-condition: ensure_daemon()  +  activate_window()          │
│  Recording:    start_recording() ... stop_recording()          │
│                                                                │
│  Layer 1  ─ Extract ──────────────── AX tree read-only         │  $0 / 0 LLM
│  Layer 2a ─ Deterministic ─────────── press_key / hotkey seq   │  $0 / 0 LLM
│  Layer 2b ─ A11y + LLM ────────────── AX tree + text LLM       │  cents / turn
│  Layer 2b-E─ Electron / CDP ────────── page tool via DevTools  │  cents / turn
│  Layer 3  ─ Vision ─────────────────── screenshot + vision LLM │  ~10× layer 2b
│                                                                │
│  Each layer returns success=True or passes to the next layer   │
└────────────────────────────────────────────────────────────────┘
                              │
                      cua-driver daemon
                    (cua-driver serve)
                  AX / UIA / AT-SPI + CDP
```

### Layer Details

| Layer | Mechanism | When used | Cost |
|-------|-----------|-----------|------|
| **1. Extract** | Read `tree_markdown` directly from `get_window_state(ax)` | Read-only goals (what/show/get) | $0 |
| **2a. Deterministic** | Fixed `press_key` / `hotkey` / `type_text` sequence | Known-app hotkeys (Calculator, etc.) | $0 |
| **2b. A11y** | `get_window_state(ax)` → text LLM → `{verdict, action, element_index}` loop | Standard native desktop apps | cents |
| **2b-E. Electron** | `page` tool via CDP (launched with `electron_debugging_port`) | VS Code, Slack, Notion, Discord | cents |
| **3. Vision** | `get_window_state(vision)` PNG → vision LLM → `click {x, y}` | Canvas apps, games, opaque AX | ~10× Layer 2b |

### Scan-Act-Verify Loop (Layer 2b)

Below two invariants are enforced in `computer/skill.py`:

1. **One scan per turn before any element_index action** — `scan()` in `driver.py` builds the element-index cache and guards `element_count == 0`.
2. **Re-scan after every state change** — every `_dispatch_action` call is followed by a new `scan()` at the top of the next loop iteration.

### Integration into the Orchestrator

Only two files changed:

**`agent_config.yaml`** — added the `computer:` skill entry (same shape as `browser:`).

**`skills.py`** — added one `if skill.name == "computer":` dispatch branch (identical pattern to the `browser` branch).

The `computer/` package is self-contained alongside `browser/`. The gateway, schemas, flow, replay viewer, and cost ledger are all unchanged.

---

## Three Tasks

### Task 1 — Windows Calculator (Layer 2a, zero LLM, zero vision)

**Goal:** Compute `(15 + 25) × 3 = 120`

**Cascade decision:** The arithmetic sequence is fully known in advance (`1 5 + 2 5 = * 3 =`), so `task_type="deterministic"` with a `hotkeys` list is used. No LLM is consulted. Verification reads the `AXStaticText` value from the final AX scan.

**Constraint satisfied:** ✓ At least one task with zero vision calls.

### Task 2 — VS Code (Layer 2b-E, Electron CDP)

**Goal:** Create a new untitled file and type a message into it.

**Cascade decision:** VS Code renders its UI as an `AXWebArea` — the AX tree has no addressable buttons. Launching with `electron_debugging_port: 9222` and using the `page` tool gives full CSS-selector / JS-evaluation access to the DOM. The `page_actions` sequence opens the command palette, runs "New Untitled File", and types content into the editor.

**Constraint satisfied:** ✓ At least one task using the Electron page path.

### Task 3 — Canvas Tic-Tac-Toe (Layer 3, vision)

**Goal:** Open a local HTML canvas game and make two moves.

**Cascade decision:** The `<canvas>` element has zero AX nodes. `get_window_state(ax)` returns `element_count=0` for everything inside the canvas. `task_type="vision"` forces Layer 3: screenshot → base64 PNG → `/v1/vision` → `{x, y}` → `click`. The game is a local HTML file (`tasks/canvas_game.html`) included in the repo — no external URL dependency.

**Constraint satisfied:** ✓ At least one task using vision.

---

## Failure Modes Encountered (and mitigations)

| Symptom | Cause | Guard in code |
|---------|-------|---------------|
| `element_count: 0` on first scan | Window not activated after `launch_app` | `activate_window()` + 0.4 s sleep before first scan |
| Cache miss on element_index | UI reflowed; indices shifted | Re-scan at top of every loop iteration (Layer 2b invariant) |
| `element_count: 0` on VS Code | Electron / AXWebArea opaque to AX | `electron_debugging_port: 9222` → `page` tool |
| `element_count: 0` on canvas | Canvas paints own pixels | Layer 3 vision; no AX recovery available |
| `bring_to_front` error on macOS | Tool is Windows-only | `activate_window()` swallows `CuaError`; macOS users add `osascript` |

---

## Setup

### 1. Install cua-driver

**Windows:**
```powershell
powershell -c "irm https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.ps1 | iex"
```

**macOS / Linux:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

Verify: `cua-driver --version`

### 2. Grant OS permissions (macOS only)

```bash
cua-driver permissions grant
# Accept both Accessibility and Screen Recording dialogs
```

### 3. Start the cua-driver daemon

```bash
cua-driver serve
# Verify with: cua-driver status
```

### 4. Start the gateway

```bash
cd "gateway"
uv run main.py
# Starts on http://localhost:8109
```

### 5. Install Python dependencies

```bash
cd "agent/code"
uv add httpx pillow pydantic
```

---

## Running the Demo

```bash
cd "agent/code"

# Individual tasks
uv run python run_demo.py task1   # Calculator — deterministic
uv run python run_demo.py task2   # VS Code — Electron CDP
uv run python run_demo.py task3   # Canvas game — vision

# All three tasks
uv run python run_demo.py all
```

Expected output summary:

```
task1    PASS ✓   deterministic   2.1s   —
task2    PASS ✓   electron        5.8s   —
task3    PASS ✓   vision          12.4s  2
```

Trajectory directories are created under:
```
agent/code/state/sessions/<session_id>/computer/trajectories/run-<timestamp>/
```

Each trajectory contains every `(tool, args)` pair recorded by `start_recording`. Use `cua-driver call replay_trajectory '{"trajectory_dir": "<path>"}'` to replay.

---

## Full Orchestrator Integration

The computer skill also works via the flow.py orchestrator:

```bash
cd "agent/code"
uv run python flow.py "Use Calculator to compute the square root of 144 plus 7 times 8"
uv run python flow.py "Open VS Code and create a new file with a note about the weather"
```

The planner will emit `computer` skill nodes using the `prompts/computer.md` guidance. The replay viewer (`python replay.py <session_id>`) shows the chosen layer under `output.path`, identical to how Browser's layer is surfaced.

---

## File Structure

```
Assignment 10/
├── agent/code/
│   ├── computer/
│   │   ├── __init__.py
│   │   ├── skill.py       # ComputerSkill — five-layer cascade
│   │   ├── driver.py      # cua-driver subprocess wrapper + scan/screenshot helpers
│   │   ├── client.py      # Async V9Client (vision + chat)
│   │   └── highlight.py   # Set-of-Marks annotator + image_to_data_url
│   ├── prompts/
│   │   └── computer.md    # Planner description for computer nodes
│   ├── tasks/
│   │   └── canvas_game.html  # Local HTML canvas tic-tac-toe (Task 3 target)
│   ├── agent_config.yaml  # config + computer skill entry
│   ├── skills.py          # skills + computer dispatch branch
│   └── run_demo.py        # Standalone demo runner
├── gateway/               # gateway
└── README.md              # This file
```
