"""
action.py — Action role (pure MCP dispatch, no LLM).

execute() dispatches a ToolCall via MCP and returns (descriptor, artifact_id|None).

Two guards:
  1. art: handle guard  — rejects tool arguments that are artifact handles
  2. Artifact threshold — payloads >4KB go to the artifact store; the loop
     receives a short descriptor + handle instead of raw bytes
"""
from __future__ import annotations

from mcp import ClientSession

from artifacts import ArtifactStore
from schemas import ActionResult, ToolCall

ARTIFACT_THRESHOLD_BYTES = 4096  # 4 KB


async def execute(
    session: ClientSession,
    tool_call: ToolCall,
    art_store: ArtifactStore,
) -> ActionResult:
    """Dispatch a tool call and return (descriptor, artifact_id|None)."""

    # Guard 1: reject art: handles passed as tool arguments
    for k, v in tool_call.arguments.items():
        if isinstance(v, str) and v.startswith("art:"):
            return ActionResult(
                descriptor=(
                    f"[ERROR] argument '{k}' is an artifact handle '{v}'. "
                    "Artifact handles are not valid tool arguments (not a URL or path). "
                    "The artifact bytes are provided in the ATTACHED ARTIFACTS section "
                    "of the Decision context. Read them from there."
                ),
                artifact_id=None,
            )

    # MCP dispatch
    try:
        result = await session.call_tool(
            tool_call.name,
            arguments=tool_call.arguments,
        )
    except Exception as e:
        return ActionResult(descriptor=f"[ERROR] MCP tool '{tool_call.name}' failed: {e}")

    # Collapse MCP content blocks into a single string
    text_parts: list[str] = []
    for block in result.content:
        if hasattr(block, "text"):
            text_parts.append(block.text)
        elif isinstance(block, dict):
            text_parts.append(block.get("text", str(block)))
        else:
            text_parts.append(str(block))
    raw_text = "\n".join(text_parts)

    result_bytes = raw_text.encode("utf-8")

    # Guard 2: large payload → artifact store
    if len(result_bytes) >= ARTIFACT_THRESHOLD_BYTES:
        art_id = art_store.put(
            result_bytes,
            content_type="text/plain",
            source=f"{tool_call.name}({list(tool_call.arguments.values())[:1]})",
            descriptor=f"{tool_call.name} result — {len(result_bytes):,} bytes",
        )
        preview = raw_text[:300].replace("\n", " ")
        descriptor = f"[artifact {art_id}, {len(result_bytes):,} bytes] preview: {preview}"
        return ActionResult(descriptor=descriptor, artifact_id=art_id)

    # Small payload → return directly (cap at 2000 chars for history readability)
    return ActionResult(descriptor=raw_text[:2000])
