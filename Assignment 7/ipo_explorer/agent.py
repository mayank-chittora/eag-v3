"""agent.py — IPO Explorer agent.

Wraps the agent_core Session 7 agent loop with:
  1. State isolation: memory and artifacts use ipo_explorer/state/ not agent_core/state/
  2. Callback hook: callers (FastAPI SSE) receive per-iteration events
  3. Terminal runnable: python agent.py "query"

agent_core modules are imported via sys.path — no file copying, one source of truth.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Callable

# ── State isolation: point memory and artifacts at ipo_explorer/state/ ───────
_HERE = Path(__file__).parent
_S7 = _HERE.parent / "agent_core"
_STATE = _HERE / "state"
_STATE.mkdir(parents=True, exist_ok=True)
(_STATE / "artifacts").mkdir(exist_ok=True)

# Insert agent_core onto sys.path BEFORE importing its modules
sys.path.insert(0, str(_S7))

import memory as _memory         # noqa: E402
import artifacts as _artifacts    # noqa: E402
import action                     # noqa: E402
import decision                   # noqa: E402
import perception                 # noqa: E402

# Redirect module-level state paths so this agent uses ipo_explorer/state/
_memory.STATE_PATH = _STATE / "memory.json"
_memory.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
_artifacts.STORE = _STATE / "artifacts"
_artifacts.STORE.mkdir(exist_ok=True)

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client             # noqa: E402

from gateway import ensure_gateway                     # noqa: E402
from schemas import Goal                               # noqa: E402

MCP_SERVER = _HERE / "mcp_server.py"
MAX_ITERATIONS = 12

EventCallback = Callable[[dict], None] | None


def _mcp_tools_for_decision(tools) -> list[dict]:
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema or {"type": "object", "properties": {}},
        }
        for t in tools
    ]


async def run(query: str, callback: EventCallback = None) -> str:
    """Run the agent loop for `query`.

    `callback` is called with an event dict at five points per iteration:
      memory / perception / decision / action / memory_write
    and once at the end with event="done".
    """
    ensure_gateway()
    run_id = uuid.uuid4().hex[:8]
    print(f"\n{'═' * 78}")
    print(f"run {run_id}  ─  query: {query}")
    print(f"{'═' * 78}")

    try:
        _memory.remember(query, source="user_query", run_id=run_id)
    except Exception as e:
        print(f"[memory.remember] skipped: {e}")

    server_params = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)])
    history: list[dict] = []
    prior_goals: list[Goal] = []
    final_answer: str = ""

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools_for_decision = _mcp_tools_for_decision(mcp_tools)
            print(f"[mcp] loaded {len(mcp_tools)} tools: {[t.name for t in mcp_tools]}")

            for it in range(1, MAX_ITERATIONS + 1):
                print(f"\n─── iter {it} ─────────────────────────────────────────────")

                # 1. MEMORY READ
                hits = _memory.read(query, history)
                print(f"[memory.read]   {len(hits)} hits")
                if callback:
                    callback({
                        "event": "memory",
                        "iter": it,
                        "hits": len(hits),
                        "descriptors": [h.descriptor[:100] for h in hits],
                    })

                # 2. PERCEPTION
                obs = perception.observe(query, hits, history, prior_goals, run_id)
                prior_goals = obs.goals
                for g in obs.goals:
                    flag = "✓" if g.done else "○"
                    print(f"[perception]    {flag} {g.id} — {g.text}")

                if callback:
                    callback({
                        "event": "perception",
                        "iter": it,
                        "goals": [{"text": g.text, "done": g.done} for g in obs.goals],
                    })

                if obs.all_done:
                    print(f"\n[done] all {len(obs.goals)} goals satisfied")
                    break

                goal = obs.next_unfinished()
                if goal is None:
                    print(f"\n[done] no unfinished goal — stopping")
                    break

                attached: list[tuple[str, bytes]] = []
                if goal.attach_artifact_id and _artifacts.exists(goal.attach_artifact_id):
                    blob = _artifacts.get_bytes(goal.attach_artifact_id)
                    attached.append((goal.attach_artifact_id, blob))
                    print(f"[attach]        {goal.attach_artifact_id} ({len(blob)} bytes)")

                # 3. DECISION
                out = decision.next_step(goal, hits, attached, history, tools_for_decision)

                if out.is_answer:
                    answer_preview = out.answer[:200] + ("..." if len(out.answer) > 200 else "")
                    print(f"[decision]      ANSWER: {answer_preview}")
                    if callback:
                        callback({
                            "event": "decision",
                            "iter": it,
                            "kind": "answer",
                            "detail": out.answer[:300],
                        })
                    history.append({
                        "iter": it,
                        "kind": "answer",
                        "goal_id": goal.id,
                        "text": out.answer,
                    })
                    final_answer = out.answer
                    # Short-circuit: if this was the last unfinished goal, exit now
                    # rather than waiting for Perception to confirm in the next iteration.
                    if not any(g for g in obs.goals if not g.done and g.id != goal.id):
                        break
                    continue

                # 4. ACTION
                tc = out.tool_call
                print(f"[decision]      TOOL_CALL: {tc.name}({json.dumps(tc.arguments)[:120]})")
                if callback:
                    callback({
                        "event": "decision",
                        "iter": it,
                        "kind": "tool_call",
                        "detail": f"{tc.name}({json.dumps(tc.arguments)[:120]})",
                    })

                result_text, art_id = await action.execute(session, tc)
                preview = result_text[:200].replace("\n", " ")
                print(f"[action]        → {preview}{'...' if len(result_text) > 200 else ''}"
                      + (f"   +{art_id}" if art_id else ""))
                if callback:
                    callback({
                        "event": "action",
                        "iter": it,
                        "tool": tc.name,
                        "result_preview": result_text[:300].replace("\n", " "),
                        "artifact_id": art_id,
                    })

                # 5. MEMORY WRITE
                _memory.record_outcome(
                    tool_call=tc,
                    result_text=result_text,
                    artifact_id=art_id,
                    run_id=run_id,
                    goal_id=goal.id,
                )
                if callback:
                    callback({"event": "memory_write", "iter": it})

                history.append({
                    "iter": it,
                    "kind": "action",
                    "goal_id": goal.id,
                    "tool": tc.name,
                    "arguments": tc.arguments,
                    "result_descriptor": result_text[:300],
                    "artifact_id": art_id,
                })

    print(f"\n{'═' * 78}")
    print(f"FINAL: {final_answer}")
    print(f"{'═' * 78}\n")

    if callback:
        callback({"event": "done", "answer": final_answer, "iters": MAX_ITERATIONS})

    return final_answer


def main() -> None:
    query = " ".join(sys.argv[1:]) or "Which IPO companies are in digital payments or fintech?"
    asyncio.run(run(query))


if __name__ == "__main__":
    main()
