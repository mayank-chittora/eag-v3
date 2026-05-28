"""
decision.py — Decision role.

next_step() selects the next action for one bounded goal.
Returns DecisionOutput with exactly one of: answer (str) or tool_call (ToolCall).

Design: uses response_format JSON schema instead of native tool calling.
The available MCP tools are described as a text block in the system prompt.
tool_arguments_json is a string (not object) so Gemini can freely write any JSON
without being constrained by a free-form object schema.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

from schemas import ActionEvent, AnswerEvent, DecisionOutput, Goal, HistoryEvent, MemoryItem, ToolCall

_GW = Path(__file__).parent / "llm_gatewayV3"
if str(_GW) not in sys.path:
    sys.path.insert(0, str(_GW))

from client import LLM  # noqa: E402

_llm = LLM()

_GEMINI = {"provider": "g", "model": "gemini-3.1-flash-lite"}

# tool_arguments_json is a STRING, not an object.
# Gemini can't reliably populate free-form {"type": "object"} fields in structured
# output mode. Encoding arguments as a JSON string lets the model write any valid
# JSON; we parse it in Python after.
_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {
            "type": "string",
            "enum": ["answer", "tool_call"],
        },
        "answer_text": {
            "type": "string",
            "description": "Substantive answer. Fill when action_type='answer', else empty string.",
        },
        "tool_name": {
            "type": "string",
            "description": "Name of the tool to call. Fill when action_type='tool_call', else empty string.",
        },
        "tool_arguments_json": {
            "type": "string",
            "description": (
                "JSON-encoded arguments for the tool, e.g. '{\"url\": \"https://...\"}'. "
                "Fill when action_type='tool_call'. Use '{}' when action_type='answer'."
            ),
        },
    },
    "required": ["action_type", "answer_text", "tool_name", "tool_arguments_json"],
    "additionalProperties": False,
}

_DECISION_SYSTEM_TEMPLATE = """\
You are the Decision role in a cognitive agent. You receive ONE goal and must
choose EXACTLY ONE action.

OUTPUT FORMAT (JSON):
  To answer directly:
    {{"action_type": "answer", "answer_text": "<your full answer>", "tool_name": "", "tool_arguments_json": "{{}}"}}

  To call a tool:
    {{"action_type": "tool_call", "answer_text": "", "tool_name": "<tool>", "tool_arguments_json": "<json string of args>"}}

TOOL SELECTION GUIDE:
  fetch_url  — use when the goal says "fetch", "read", or gives a specific URL
  web_search — use when the goal says "find", "search for", or needs to discover URLs
  get_time   — use when time or date information is needed
  create_file / update_file / edit_file — use when goal asks to create/write files
  read_file / list_dir — use when goal asks to read existing files

EXAMPLES of tool_arguments_json:
  fetch_url  : '{{"url": "https://en.wikipedia.org/wiki/Claude_Shannon"}}'
  web_search : '{{"query": "family-friendly things to do in Tokyo"}}'
  create_file: '{{"path": "reminders/note.txt", "content": "Reminder text here"}}'

RULES:
1. Use action_type="answer" when memory hits or ATTACHED ARTIFACTS already contain
   enough information to fully answer the goal.
2. ARTIFACT HANDLES (strings starting with "art:") are NOT valid tool arguments.
   Never put them in tool_arguments_json. Read artifact content from ATTACHED ARTIFACTS.
3. Substantive answers must be at least 3 sentences or a numbered list.
4. tool_arguments_json must be valid JSON encoded as a string.
5. Call exactly ONE tool per response.

AVAILABLE TOOLS:
{tools_block}
"""

_MAX_ARTIFACT_CHARS = 80_000  # ~20K tokens


def _tools_as_text(mcp_tools: list[dict]) -> str:
    lines = []
    for t in mcp_tools:
        name = t.get("name", "?")
        desc = t.get("description", "")
        schema = t.get("inputSchema", {})
        props = schema.get("properties", {})
        params = ", ".join(
            f"{k}: {v.get('type', 'any')}" for k, v in props.items()
        )
        lines.append(f"  {name}({params})\n    {desc}")
    return "\n".join(lines)


def _chat_with_retry(prompt: str, *, system: str, max_retries: int = 3, **kwargs) -> dict:
    """Call the gateway with exponential backoff on 503/429 rate-limit errors."""
    for attempt in range(max_retries):
        try:
            return _llm.chat(prompt, system=system, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 502, 503) and attempt < max_retries - 1:
                wait = 10 * (2 ** attempt)  # 10s, 20s, 40s
                print(f"  [decision] rate-limited ({e.response.status_code}), retrying in {wait}s ...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("unreachable")


def next_step(
    goal: Goal,
    hits: list[MemoryItem],
    attached: list[tuple[str, bytes]],
    history: list[HistoryEvent],
    mcp_tools: list[dict],
) -> DecisionOutput:
    """Select the next action for a single bounded goal."""

    # Memory hits block
    hits_lines = []
    for h in hits:
        art_note = f" [artifact: {h.artifact_id}]" if h.artifact_id else ""
        hits_lines.append(f"  [{h.kind}] {h.descriptor}{art_note}")
    hits_block = "\n".join(hits_lines) if hits_lines else "  (none)"

    # History block (last 8 events) — typed access via ActionEvent / AnswerEvent
    hist_lines = []
    for h in history[-8:]:
        if isinstance(h, ActionEvent):
            args_str = str(h.arguments)[:80]
            hist_lines.append(f"  iter{h.iter} {h.tool}({args_str}) → {h.result_descriptor[:200]}")
        elif isinstance(h, AnswerEvent):
            hist_lines.append(f"  iter{h.iter} ANSWER: {h.text[:200]}")
    history_block = "\n".join(hist_lines) if hist_lines else "  (none)"

    # Attached artifacts block
    attached_block = ""
    if attached:
        parts = []
        for art_id, blob in attached:
            try:
                text = blob.decode("utf-8", errors="replace")
            except Exception:
                text = f"[binary content, {len(blob)} bytes]"
            if len(text) > _MAX_ARTIFACT_CHARS:
                text = text[:_MAX_ARTIFACT_CHARS] + "\n...[truncated]"
            parts.append(f"=== ARTIFACT {art_id} ===\n{text}")
        attached_block = "\n\nATTACHED ARTIFACTS:\n" + "\n".join(parts)

    tools_block = _tools_as_text(mcp_tools)
    system = _DECISION_SYSTEM_TEMPLATE.format(tools_block=tools_block)

    user_prompt = f"""CURRENT GOAL: {goal.text}

MEMORY HITS:
{hits_block}

RECENT HISTORY:
{history_block}
{attached_block}

Respond with JSON only.
"""

    resp = _chat_with_retry(
        user_prompt,
        system=system,
        **_GEMINI,
        temperature=0.2,
        max_tokens=4096,
        response_format={"type": "json_schema", "schema": _DECISION_SCHEMA},
    )

    try:
        data = resp.get("parsed") or json.loads(resp.get("text", "{}"))
    except Exception:
        return DecisionOutput(
            answer="I was unable to parse the decision response. Please retry."
        )

    action_type = data.get("action_type", "answer")

    if action_type == "tool_call":
        tool_name = data.get("tool_name", "").strip()
        args_json = data.get("tool_arguments_json", "{}").strip()
        try:
            tool_args = json.loads(args_json)
        except Exception:
            # LLM returned malformed JSON in the string — try to salvage
            tool_args = {}
        if tool_name:
            return DecisionOutput(tool_call=ToolCall(name=tool_name, arguments=tool_args))

    answer_text = data.get("answer_text", "").strip()
    if answer_text:
        return DecisionOutput(answer=answer_text)

    return DecisionOutput(
        answer="Unable to determine the next action. Please rephrase the query."
    )
