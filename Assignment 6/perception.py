"""
perception.py — Perception role (orchestrator).

observe() runs every iteration. It:
  1. Decomposes the query into bounded goals (first call, prior_goals=[])
  2. Marks goals done when history shows satisfying actions/answers
  3. Attaches an artifact to the first unfinished goal when the goal needs bytes

Key safety properties:
  - Positional goal identity: the LLM never writes goal IDs; the loop assigns them
  - Integer artifact_index: the LLM emits an integer (0+) instead of an art: handle;
    the Python code maps it to the actual handle — prevents hallucinated handles
  - Sticky-done: once a goal is marked done, it stays done regardless of LLM output
  - temperature=1.0: prevents Gemini 3.1 flash-lite from looping at temperature=0
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

from schemas import ActionEvent, AnswerEvent, Goal, HistoryEvent, MemoryItem, Observation

_GW = Path(__file__).parent / "llm_gatewayV3"
if str(_GW) not in sys.path:
    sys.path.insert(0, str(_GW))

from client import LLM  # noqa: E402

_llm = LLM()


def _chat_with_retry(prompt: str, *, system: str, max_retries: int = 3, **kwargs) -> dict:
    for attempt in range(max_retries):
        try:
            return _llm.chat(prompt, system=system, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 502, 503) and attempt < max_retries - 1:
                wait = 10 * (2 ** attempt)
                print(f"  [perception] rate-limited ({e.response.status_code}), retrying in {wait}s ...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("unreachable")

_GEMINI = {"provider": "g", "model": "gemini-3.1-flash-lite"}

# Schema for LLM output — NO id field (positional identity), integer artifact_index
_PERCEPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "goals": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "done": {"type": "boolean"},
                    "artifact_index": {
                        "type": "number",
                        "description": "-1 means no attachment; 0+ is index into the ARTIFACT HITS list",
                    },
                },
                "required": ["text", "done", "artifact_index"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["goals"],
    "additionalProperties": False,
}

_PERCEPTION_SYSTEM = """\
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
"""


def observe(
    query: str,
    hits: list[MemoryItem],
    history: list[HistoryEvent],
    prior_goals: list[Goal],
    run_id: str,
) -> Observation:
    """Run the Perception role for one iteration."""

    # Build memory hits section with integer artifact_index labels
    artifact_hits: list[tuple[int, MemoryItem]] = []  # (art_idx, item)
    hits_lines: list[str] = []
    art_idx_counter = 0

    for item in hits:
        if item.artifact_id:
            label = f"artifact_index={art_idx_counter}"
            hits_lines.append(
                f"  [{item.kind}] {label} | {item.descriptor} | handle={item.artifact_id}"
            )
            artifact_hits.append((art_idx_counter, item))
            art_idx_counter += 1
        else:
            hits_lines.append(f"  [{item.kind}] no_artifact | {item.descriptor}")

    hits_block = "\n".join(hits_lines) if hits_lines else "  (none)"

    # Prior goals block
    if prior_goals:
        prior_lines = [
            f"  {'[done]' if g.done else '[open]'} {g.id}: {g.text}"
            for g in prior_goals
        ]
        prior_block = "PRIOR GOALS:\n" + "\n".join(prior_lines)
    else:
        prior_block = "PRIOR GOALS: (none — first call, please decompose the query)"

    # History block (last 10 events) — typed access via ActionEvent / AnswerEvent
    if history:
        hist_lines = []
        for h in history[-10:]:
            if isinstance(h, ActionEvent):
                args_str = str(h.arguments)[:80]
                desc = h.result_descriptor[:200]
                hist_lines.append(f"  iter{h.iter} ACTION {h.tool}({args_str}) → {desc}")
            elif isinstance(h, AnswerEvent):
                hist_lines.append(f"  iter{h.iter} ANSWER for {h.goal_id}: {h.text[:200]}")
        history_block = "RUN HISTORY:\n" + "\n".join(hist_lines)
    else:
        history_block = "RUN HISTORY: (empty)"

    user_prompt = f"""USER QUERY: {query}

MEMORY HITS (indexed):
{hits_block}

{prior_block}

{history_block}

Emit the goal list as JSON.
artifact_index: integer. Use -1 for no attachment. Use 0, 1, 2... to reference
the artifact_index shown in MEMORY HITS above.
"""

    resp = _chat_with_retry(
        user_prompt,
        system=_PERCEPTION_SYSTEM,
        **_GEMINI,
        temperature=1.0,
        max_tokens=1024,
        response_format={"type": "json_schema", "schema": _PERCEPTION_SCHEMA},
    )

    try:
        data = resp.get("parsed") or json.loads(resp.get("text", "{}"))
        raw_goals = data.get("goals", [])
    except Exception:
        raw_goals = []

    # Safety: if no goals returned, preserve prior goals or create a fallback
    if not raw_goals and prior_goals:
        raw_goals = [{"text": g.text, "done": g.done, "artifact_index": -1} for g in prior_goals]
    elif not raw_goals:
        raw_goals = [{"text": query, "done": False, "artifact_index": -1}]

    # Build typed Goal list with stable IDs, sticky-done, and resolved artifact handles
    art_lookup: dict[int, str] = {
        idx: item.artifact_id
        for idx, item in artifact_hits
        if item.artifact_id
    }

    goals: list[Goal] = []
    for i, rg in enumerate(raw_goals):
        # Positional ID — assigned by the loop, never by the LLM
        if i < len(prior_goals):
            goal_id = prior_goals[i].id
            # Sticky-done guard: once done, stays done
            is_done = prior_goals[i].done or bool(rg.get("done", False))
        else:
            goal_id = f"g{i + 1}"
            is_done = bool(rg.get("done", False))

        # Resolve integer artifact_index → actual art: handle
        art_idx_val = rg.get("artifact_index", -1)
        attach_id: str | None = None
        if isinstance(art_idx_val, int) and art_idx_val >= 0:
            attach_id = art_lookup.get(art_idx_val)

        goals.append(
            Goal(
                id=goal_id,
                text=rg.get("text", f"goal {i + 1}"),
                done=is_done,
                attach_artifact_id=attach_id,
            )
        )

    return Observation(goals=goals)
