"""
agent6.py — Main loop for the multi-role cognitive agent.

Wires together Memory → Perception → Decision → Action in a fixed iteration order.
Each iteration:
  1. Memory.read()       — keyword search over persisted items (no LLM)
  2. Perception.observe()— emits updated goal list with done flags + artifact attach
  3. Decision.next_step()— returns answer or tool_call for the current goal
  4. Action.execute()    — dispatches MCP tool, stores large results as artifacts
  5. Memory.record_outcome() — persists the tool result

Usage:
  uv run python agent6.py "Your query here"
  uv run python agent6.py --query-a
  uv run python agent6.py --query-b
  uv run python agent6.py --query-c1
  uv run python agent6.py --query-c2
  uv run python agent6.py --query-d
"""
from __future__ import annotations

import asyncio
import subprocess
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import action
import perception
import decision
from artifacts import ArtifactStore, artifacts
from memory import MemoryService, memory
from schemas import ActionEvent, AnswerEvent, Goal, HistoryEvent, Observation

_DIR = Path(__file__).parent
_MCP_SERVER = _DIR / "mcp_server.py"
_GATEWAY_URL = "http://localhost:8101"
_MAX_ITERATIONS = 15

# ── Target queries ────────────────────────────────────────────────────────────

QUERIES: dict[str, str] = {
    "--query-a": (
        "Fetch https://en.wikipedia.org/wiki/Claude_Shannon and tell me his "
        "birth date, death date, and three key contributions to information theory."
    ),
    "--query-b": (
        "Find 3 family-friendly things to do in Tokyo this weekend. "
        "Check Saturday's weather forecast there and tell me which one is most appropriate."
    ),
    "--query-c1": (
        "My mom's birthday is 15 May 2026. Remember that and give me a "
        "calendar reminder for two weeks before and on the day."
    ),
    "--query-c2": "When is mom's birthday?",
    "--query-d": (
        "Search for 'Python asyncio best practices', read the top 3 results, "
        "and give me a short numbered list of the advice they agree on."
    ),
}

# ── Gateway helpers ───────────────────────────────────────────────────────────


def _gateway_alive() -> bool:
    import httpx
    try:
        r = httpx.get(f"{_GATEWAY_URL}/v1/providers", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def ensure_gateway() -> None:
    if _gateway_alive():
        print("[gateway] running at", _GATEWAY_URL)
        return
    print("[gateway] not detected — attempting to start llm_gatewayV3 ...")
    gw_main = _DIR / "llm_gatewayV3" / "main.py"
    if not gw_main.exists():
        print(f"[gateway] ERROR: {gw_main} not found. Start the gateway manually.")
        sys.exit(1)
    subprocess.Popen(
        [sys.executable, str(gw_main)],
        cwd=str(_DIR / "llm_gatewayV3"),
    )
    for i in range(10):
        time.sleep(3)
        if _gateway_alive():
            print("[gateway] started")
            return
    print("[gateway] ERROR: gateway did not start within 30s. Aborting.")
    sys.exit(1)


# ── MCP helpers ───────────────────────────────────────────────────────────────


async def _load_tools(session: ClientSession) -> list[dict]:
    result = await session.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description or "",
            "inputSchema": t.inputSchema if hasattr(t, "inputSchema") else {},
        }
        for t in result.tools
    ]


# ── Final answer extraction ───────────────────────────────────────────────────


def _final_answer(history: list[HistoryEvent]) -> str:
    answers = [h for h in history if isinstance(h, AnswerEvent)]
    if answers:
        return answers[-1].text
    actions = [h for h in history if isinstance(h, ActionEvent)]
    if actions:
        last = actions[-1]
        return f"Completed: {last.tool} → {last.result_descriptor[:500]}"
    return "No answer produced."


# ── Main run loop ─────────────────────────────────────────────────────────────


async def run(query: str, *, mem: MemoryService = memory, art: ArtifactStore = artifacts) -> str:
    ensure_gateway()

    run_id = uuid.uuid4().hex[:8]
    history: list[HistoryEvent] = []
    prior_goals: list[Goal] = []

    print(f"\n[run:{run_id}] {query[:120]}")

    # Classify the user's query so durable facts/preferences survive future runs
    print("[memory.remember] classifying query ...")
    mem.remember(query, source="user_query", run_id=run_id)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(_MCP_SERVER)],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            mcp_tools = await _load_tools(session)
            tool_names = [t["name"] for t in mcp_tools]
            print(f"[mcp] {len(mcp_tools)} tools: {tool_names}")

            obs: Observation | None = None

            for it in range(1, _MAX_ITERATIONS + 1):
                print(f"\n─── iter {it} ───")

                # Step 1: Memory read (no LLM)
                hits = mem.read(query, history)
                hit_descs = [h.descriptor[:60] for h in hits]
                print(f"[memory.read]  {len(hits)} hits: {hit_descs}")

                # Step 2: Perception
                obs = perception.observe(
                    query=query,
                    hits=hits,
                    history=history,
                    prior_goals=prior_goals,
                    run_id=run_id,
                )
                prior_goals = obs.goals

                for g in obs.goals:
                    status = "[done]" if g.done else "[open]"
                    attach = f"  attach={g.attach_artifact_id}" if g.attach_artifact_id else ""
                    print(f"  [perception]  {status} {g.id}: {g.text}{attach}")

                if obs.all_done:
                    print("[done] all goals satisfied")
                    break

                goal = obs.next_unfinished()
                if goal is None:
                    break

                # Step 3: Load attached artifact bytes if Perception requested one
                attached: list[tuple[str, bytes]] = []
                if goal.attach_artifact_id:
                    if art.exists(goal.attach_artifact_id):
                        blob = art.get_bytes(goal.attach_artifact_id)
                        attached.append((goal.attach_artifact_id, blob))
                        print(
                            f"  [attach]      {goal.attach_artifact_id} "
                            f"({len(blob):,} bytes)"
                        )
                    else:
                        print(
                            f"  [attach]      WARNING: {goal.attach_artifact_id} "
                            "not in store — skipping"
                        )

                # Step 4: Decision
                out = decision.next_step(
                    goal=goal,
                    hits=hits,
                    attached=attached,
                    history=history,
                    mcp_tools=mcp_tools,
                )

                if out.is_answer:
                    print(f"  [decision]    ANSWER: {out.answer[:300]}")
                    history.append(AnswerEvent(iter=it, goal_id=goal.id, text=out.answer))
                    continue

                tc = out.tool_call
                print(f"  [decision]    TOOL_CALL: {tc.name}({tc.arguments})")

                # Step 5: Action (pure MCP dispatch)
                result = await action.execute(
                    session=session,
                    tool_call=tc,
                    art_store=art,
                )
                print(f"  [action]      → {result.descriptor[:300]}")

                # Step 6: Record outcome in memory (no LLM)
                mem.record_outcome(
                    tool_call=tc,
                    result_text=result.descriptor,
                    artifact_id=result.artifact_id,
                    run_id=run_id,
                    goal_id=goal.id,
                )

                history.append(ActionEvent(
                    iter=it,
                    goal_id=goal.id,
                    tool=tc.name,
                    arguments=tc.arguments,
                    result_descriptor=result.descriptor[:300],
                    artifact_id=result.artifact_id,
                ))

            else:
                print(f"[done] max iterations ({_MAX_ITERATIONS}) reached")

    final = _final_answer(history)
    sep = "=" * 60
    print(f"\n{sep}\nFINAL ANSWER:\n{final}\n{sep}")
    return final


# ── CLI ───────────────────────────────────────────────────────────────────────


def _parse_args() -> str:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # Check for named query flags
    for flag, text in QUERIES.items():
        if flag in args:
            return text

    # Otherwise treat all args as the query string
    return " ".join(args)


if __name__ == "__main__":
    asyncio.run(run(_parse_args()))
