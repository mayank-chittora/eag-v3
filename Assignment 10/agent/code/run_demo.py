"""Standalone demo runner for Assignment 10: Computer-Use skill.

Exercises all three tasks required by the assignment without going through
the full S9 orchestrator.  Each task is a direct ComputerSkill.run() call.

Tasks
-----
task1  Windows Calculator  Layer 2a — deterministic hotkeys, zero LLM, zero vision
task2  VS Code             Layer 2b-E — Electron CDP page tool
task3  Canvas Tic-Tac-Toe  Layer 3   — vision (canvas has no AX nodes)

Usage
-----
    # single task
    uv run python run_demo.py task1
    uv run python run_demo.py task2
    uv run python run_demo.py task3

    # all tasks sequentially
    uv run python run_demo.py all

Prerequisites
-------------
    - cua-driver daemon running   (cua-driver serve)
    - V9 gateway running          (cd ../../gateway && uv run main.py)
    - For task2: VS Code installed
    - For task3: Microsoft Edge or Chrome installed
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

# Ensure stdout/stderr can handle Unicode on Windows (default cp1252 cannot).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Allow importing from the code directory.
_HERE = Path(__file__).parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from schemas import NodeSpec
from computer.skill import ComputerSkill

# ── session setup ─────────────────────────────────────────────────────────────

_STATE_ROOT = _HERE / "state" / "sessions"


def _new_session() -> tuple[str, ComputerSkill]:
    sid = f"s10-{uuid.uuid4().hex[:8]}"
    artifacts = _STATE_ROOT / sid / "computer"
    artifacts.mkdir(parents=True, exist_ok=True)
    skill = ComputerSkill(
        artifacts_root=str(artifacts),
        session=sid,
        max_steps_a11y=25,
        max_steps_vision=12,
    )
    return sid, skill


# ── Task 1: Windows Calculator (Layer 2a — deterministic) ────────────────────

async def run_task1() -> dict:
    """Compute (15 + 25) × 3 = 120 via deterministic hotkeys.

    Zero LLM calls, zero screenshots.  The sequence:
        1, 5, +, 2, 5, =, ×, 3, =
    Result verified by reading AXStaticText from the AX tree.
    """
    sid, skill = _new_session()
    print(f"\n{'='*60}")
    print("Task 1 — Windows Calculator  [Layer 2a: deterministic]")
    print(f"Session: {sid}")
    print("Goal   : Compute (15 + 25) * 3  ->  expected 120")
    print('='*60)

    node = NodeSpec(
        skill="computer",
        inputs=[],
        metadata={
            "app": "Calculator",
            "goal": "Compute (15 + 25) * 3 and verify the result is 120",
            "task_type": "deterministic",
            "hotkeys": [
                # Use click_element — UIA InvokePattern; no focus needed.
                # Button labels from the Windows Calculator AX tree.
                {"type": "click_element", "label": "Clear"},
                {"type": "click_element", "label": "One"},
                {"type": "click_element", "label": "Five"},
                {"type": "click_element", "label": "Plus"},
                {"type": "click_element", "label": "Two"},
                {"type": "click_element", "label": "Five"},
                {"type": "click_element", "label": "Equals"},   # → 40
                {"type": "click_element", "label": "Multiply by"},
                {"type": "click_element", "label": "Three"},
                {"type": "click_element", "label": "Equals"},   # → 120
            ],
        },
    )

    result = await skill.run(node)
    _print_result(result)

    final_tree = result.output.get("final_tree", "")
    # Windows UIA: display node label is "Display is <value>" with id=CalculatorResults
    import re
    display_match = re.search(r'Display is ([^\s"]+)', final_tree)
    if display_match:
        display_val = display_match.group(1).strip().rstrip('"')
        print(f"Calculator display : {display_val}")
        if "120" in display_val:
            print("Verification       : PASS -- display shows 120")
        else:
            print(f"Verification       : FAIL — expected 120, got {display_val!r}")
    elif "120" in final_tree:
        print("Verification       : PASS -- 120 found in AX tree")
    else:
        hits = [l.strip() for l in final_tree.splitlines()
                if any(k in l for k in ("CalculatorResults", "Display", "value="))]
        print("Verification       : could not confirm 120 in AX tree")
        for h in hits[:8]:
            print(f"  {h}")

    return {"task": "task1", "success": result.success, "path": result.output.get("path"),
            "elapsed": result.elapsed_s, "trajectory": result.output.get("trajectory")}


# ── Task 2: VS Code (Layer 2b-E — Electron CDP) ──────────────────────────────

async def run_task2() -> dict:
    """Open VS Code with debugging port and create a new untitled file.

    Uses the `page` tool via Chrome DevTools Protocol — no AX tree involved.
    Action sequence:
        1. Launch VS Code with electron_debugging_port=9222
        2. Open command palette (Ctrl+Shift+P)
        3. Type 'New Untitled File' → Enter
        4. Type a short message into the editor
    """
    sid, skill = _new_session()
    print(f"\n{'='*60}")
    print("Task 2 — VS Code  [Layer 2b-E: Electron / CDP page tool]")
    print(f"Session: {sid}")
    print("Goal   : Create a new untitled file and type a message")
    print('='*60)

    node = NodeSpec(
        skill="computer",
        inputs=[],
        metadata={
            "app": "Code",
            "goal": "Create a new untitled file and type a short agent-authored message",
            "task_type": "electron",
            "electron_debugging_port": 9222,
            # On Windows, launch via the code.cmd wrapper so that
            # --remote-debugging-port=9222 reaches the Electron process.
            # The Code.exe launcher alone does not forward the flag.
            "launch_cmd": ["cmd", "/c", "start", "/b", "code", "--remote-debugging-port=9222"],
            "page_actions": [
                # 1. Prove CDP is connected: read VS Code's visible text.
                {"action": "get_text"},
                # 2. Open a new untitled file via VS Code's command palette shortcut.
                #    dispatch Ctrl+N to the workbench element; VS Code's keybinding
                #    system handles both trusted and untrusted events.
                {
                    "action": "execute_javascript",
                    "javascript": (
                        "(async()=>{"
                        "const wb=document.querySelector('.monaco-workbench')||document.body;"
                        "['keydown','keyup'].forEach(t=>wb.dispatchEvent("
                        "new KeyboardEvent(t,{key:'n',keyCode:78,ctrlKey:true,bubbles:true,cancelable:true})));"
                        "await new Promise(r=>setTimeout(r,1200));"
                        "return 'dispatched Ctrl+N, title='+document.title;"
                        "})()"
                    ),
                },
                # 3. Type content into the active editor textarea via execCommand.
                {
                    "action": "execute_javascript",
                    "javascript": (
                        "(async()=>{"
                        "const ta=document.querySelector('.monaco-editor textarea');"
                        "if(!ta){return 'no-textarea';}"
                        "ta.focus();"
                        "const msg='Assignment 10: Computer-Use Agent CDP demo via cua-driver';"
                        "document.execCommand('insertText',false,msg);"
                        "return 'typed:'+msg.slice(0,40);"
                        "})()"
                    ),
                },
                # 4. Final state snapshot.
                {"action": "get_text"},
            ],
        },
    )

    result = await skill.run(node)
    _print_result(result)

    # Report action outcomes
    actions = result.output.get("actions", [])
    success_count = sum(1 for a in actions if "error" not in a)
    print(f"CDP actions completed: {success_count} / {len(actions)}")
    for a in actions:
        act_name = a.get("action", {}).get("action", "?")
        if "error" in a:
            print(f"  FAIL [{act_name}]: {a['error']}")
        else:
            raw = a.get("result", {})
            detail = raw.get("raw", "") if isinstance(raw, dict) else str(raw)
            safe = detail[:80].encode("ascii", "replace").decode("ascii")
            print(f"  OK   [{act_name}]" + (f": {safe}" if safe else ""))

    return {"task": "task2", "success": result.success, "path": result.output.get("path"),
            "elapsed": result.elapsed_s, "trajectory": result.output.get("trajectory")}


# ── Task 3: Canvas Tic-Tac-Toe (Layer 3 — vision) ───────────────────────────

async def run_task3() -> dict:
    """Navigate to a local canvas game and make two moves via vision.

    The canvas element exposes zero AX nodes — cua-driver's AX scan returns
    element_count=0 for anything inside it.  This forces Layer 3: screenshot
    → base64 data URL → vision LLM → click by (x, y).
    """
    sid, skill = _new_session()
    print(f"\n{'='*60}")
    print("Task 3 — Canvas Tic-Tac-Toe  [Layer 3: vision]")
    print(f"Session: {sid}")
    print("Goal   : Play tic-tac-toe: place X in the top-left cell, then O in the centre")
    print('='*60)

    # Absolute path to the local HTML file.
    game_path = (_HERE / "tasks" / "canvas_game.html").resolve()

    # Launch Edge with a CDP debugging port so that when the OS foreground-lock
    # blocks cua-driver's SendInput click (UIAccess limitation), we can fall back
    # to dispatching a MouseEvent directly on the canvas via execute_javascript.
    # The vision layer still drives everything: screenshot -> LLM -> (x,y) -> click.
    node = NodeSpec(
        skill="computer",
        inputs=[],
        metadata={
            "app": "edge",
            "goal": (
                "The page shows a Tic-Tac-Toe game on a dark background. "
                "The board is a 3x3 grid drawn on a canvas. "
                "Click the top-left cell to place X there. "
                "Then click the centre cell to place O there. "
                "The task is complete after both moves are made."
            ),
            "task_type": "vision",
            "electron_debugging_port": 9223,
            # --user-data-dir forces a new Edge process (separate from any
            # already-running instance) so --remote-debugging-port=9223 is
            # honoured.  Without it, Edge reuses the existing process and the
            # flag is silently ignored.
            "launch_cmd": [
                "cmd", "/c", "start", "/b", "msedge",
                "--remote-debugging-port=9223",
                r"--user-data-dir=C:\Users\Tradelab\AppData\Local\Temp\edge-cdp-9223",
                "--no-first-run",
                "--no-default-browser-check",
                str(game_path),
            ],
        },
    )

    result = await skill.run(node)
    _print_result(result)

    steps = result.output.get("steps", 0)
    print(f"Vision steps taken : {steps}")
    if not result.success:
        ss_result = result.output.get("screenshot_result")
        if ss_result:
            print(f"Screenshot result  : {str(ss_result)[:200]}")
    actions = result.output.get("actions", [])
    for a in actions:
        act = a.get("action", "click")
        if act == "cdp_cell_click":
            js_info = f"  [{a.get('js', '')[:60]}]"
            print(f"  {act} row={a.get('row')} col={a.get('col')}  step={a.get('step')}{js_info}")
        elif act == "cdp_click":
            js_info = f"  [{a.get('js', '')[:40]}]"
            print(f"  {act} ({a.get('x')}, {a.get('y')})  step={a.get('step')}{js_info}")
        else:
            print(f"  {act} ({a.get('x')}, {a.get('y')})  step={a.get('step')}")

    return {"task": "task3", "success": result.success, "path": result.output.get("path"),
            "elapsed": result.elapsed_s, "trajectory": result.output.get("trajectory"),
            "steps": steps}


# ── helpers ───────────────────────────────────────────────────────────────────

def _print_result(result) -> None:
    status = "PASS" if result.success else "FAIL"
    path   = result.output.get("path", "none")
    traj   = result.output.get("trajectory", "—")
    elapsed = f"{result.elapsed_s:.1f}s" if result.elapsed_s else "—"
    print(f"Result    : {status}")
    print(f"Layer     : {path}")
    print(f"Elapsed   : {elapsed}")
    print(f"Trajectory: {traj}")
    if not result.success:
        print(f"Error     : {result.output.get('error') or result.error}")


def _summary(results: list[dict]) -> None:
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    cols = ("task", "success", "path", "elapsed", "steps")
    fmt = "{:<8} {:<8} {:<15} {:<10} {}"
    print(fmt.format(*cols))
    print("-" * 55)
    for r in results:
        print(fmt.format(
            r.get("task", "?"),
            "PASS" if r.get("success") else "FAIL",
            r.get("path") or "—",
            f"{r.get('elapsed') or 0:.1f}s",
            r.get("steps", "—"),
        ))
    print()


# ── entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    results: list[dict] = []

    if arg in ("all", "task1"):
        results.append(await run_task1())
    if arg in ("all", "task2"):
        results.append(await run_task2())
    if arg in ("all", "task3"):
        results.append(await run_task3())

    if len(results) > 1:
        _summary(results)


if __name__ == "__main__":
    asyncio.run(main())
