"""Computer-Use skill: five-layer cascade over cua-driver.

Mirrors browser/skill.py but targets desktop applications instead of web
pages.  The skill receives a NodeSpec from the orchestrator (same contract
as the browser skill) and returns an AgentResult.

Layer hierarchy (cheapest → most expensive):

    Layer 1   Extract       Read AX tree text directly — no action, no LLM
    Layer 2a  Deterministic Fixed hotkey / press_key sequences for known apps
    Layer 2b  A11y          get_window_state(ax) + cheap text LLM → actions
    Layer 2b-E Electron     `page` tool via CDP for Electron / browser targets
    Layer 3   Vision        get_window_state(vision) PNG + vision LLM → (x,y)

Escalation: each layer returns success=True or propagates to the next.
If all layers fail the skill returns success=False with the last error.

Scan-act-verify invariants (from the course notes):
  - Call get_window_state once per turn BEFORE any element_index action.
  - Every new get_window_state snapshot replaces the previous index map.
  - Re-scan after every state-changing action.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Any

# Schemas live in the parent code directory.
import sys
_CODE_ROOT = Path(__file__).parent.parent
if str(_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(_CODE_ROOT))

from schemas import AgentResult, NodeSpec

from .client import V9Client
from .driver import (
    CuaError,
    PermissionsError,
    activate_window,
    call,
    ensure_daemon,
    list_windows_for_pid,
    scan,
    screenshot,
)
from .highlight import image_to_data_url


# ── prompts ──────────────────────────────────────────────────────────────────

_A11Y_SYSTEM = """\
You are a desktop UI automation agent.  You receive an accessibility tree
(AX tree) and a goal.  Your job is to choose exactly ONE next action that
advances the goal, or declare it done.

Respond with a single JSON object — no markdown fences, no prose:
{
  "verdict":       "act" | "done" | "escalate",
  "action":        "click" | "type_text" | "press_key" | "hotkey" | "scroll" | "set_value",
  "element_index": <integer N from the [N] tag in the tree — required for click/set_value>,
  "text":          "<string — required for type_text>",
  "key":           "<key name — required for press_key, e.g. Return, Escape, Tab>",
  "keys":          ["<modifier>", "<key>"] — required for hotkey, e.g. ["ctrl","s"],
  "direction":     "up" | "down" | "left" | "right" — required for scroll,
  "amount":        <integer scroll ticks — default 3>,
  "value":         "<string — required for set_value>",
  "result":        "<describe current state when verdict=done>",
  "reason":        "<why escalating when verdict=escalate>"
}

Rules:
- verdict=done   when the goal is fully achieved; describe the outcome in result.
- verdict=escalate if the AX tree is empty, the target element is missing, or
  the task cannot be completed with available elements.
- verdict=act    otherwise.  Provide exactly ONE action.
- element_index must come from the [N] tags in the tree, first occurrence only.
- After a click that opens a menu/dialog the caller will re-scan automatically.
"""

_VISION_SYSTEM = """\
You are a desktop UI automation agent using vision.  You receive a screenshot
of a desktop window and a goal.  Your job is to choose exactly ONE click that
advances the goal, or declare it done.

Respond with a single JSON object — no markdown fences, no prose:
{
  "verdict": "act" | "done" | "escalate",
  "action":  "click",
  "row":     <0-indexed grid row to click — 0=top, 1=middle, 2=bottom — ONLY for 3x3 grid targets>,
  "col":     <0-indexed grid column to click — 0=left, 1=middle, 2=right — ONLY for 3x3 grid targets>,
  "x":       <pixel x coordinate in the screenshot — use when no grid>,
  "y":       <pixel y coordinate in the screenshot — use when no grid>,
  "result":  "<describe what you see and what was achieved, if done>",
  "reason":  "<why escalating, if escalate>"
}

Rules:
- verdict=done     when the goal is achieved.
- verdict=escalate if you cannot determine where to click.
- verdict=act      otherwise.
- For a 3x3 grid (like Tic-Tac-Toe): provide row + col instead of x/y.
  top-left=row0/col0, top-center=row0/col1, center=row1/col1, etc.
- For non-grid targets: provide x + y pixel coordinates.
- Coordinates must be within the screenshot bounds.
"""


# ── main class ───────────────────────────────────────────────────────────────

class ComputerSkill:
    """Five-layer cascade that drives desktop apps via cua-driver.

    Instantiated once per skill invocation by the skills.py dispatcher.
    """

    def __init__(
        self,
        artifacts_root: str,
        session: str,
        max_steps_a11y: int = 20,
        max_steps_vision: int = 10,
    ):
        self.artifacts_root = Path(artifacts_root)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.session = session
        self.max_steps_a11y = max_steps_a11y
        self.max_steps_vision = max_steps_vision
        self.client = V9Client(session=session)

    # ── public entry point ───────────────────────────────────────────────────

    async def run(self, node: NodeSpec) -> AgentResult:
        """Execute the cascade and return an AgentResult."""
        started = time.time()
        meta = node.metadata or {}
        app       = meta.get("app", "")
        goal      = meta.get("goal", "")
        task_type = meta.get("task_type", "auto")
        hotkeys   = meta.get("hotkeys") or []

        # Pre-condition: daemon must be running.
        # Restart with CUA_DRIVER_CDP_PORT when any task needs CDP — either an
        # Electron task driving VS Code, or a vision task that uses JS CDP clicks
        # as a fallback when the OS foreground-lock blocks SendInput.
        cdp_port = meta.get("electron_debugging_port")
        daemon_env = {"CUA_DRIVER_CDP_PORT": str(cdp_port)} if cdp_port else None
        cdp_env: dict[str, str] = {"CUA_DRIVER_CDP_PORT": str(cdp_port)} if cdp_port else {}
        ensure_daemon(extra_env=daemon_env)

        # Start trajectory recording.
        traj_root = self.artifacts_root / "trajectories"
        traj_root.mkdir(parents=True, exist_ok=True)
        traj_dir  = str(traj_root / f"run-{int(time.time())}")
        recording = False
        try:
            call("start_recording", {"output_dir": traj_dir})
            recording = True
        except CuaError:
            pass  # recording failure is non-fatal

        path_chosen = "none"
        output: dict[str, Any] = {}
        error: str | None = None

        try:
            # Launch / find the app window.
            pid, window_id = await asyncio.to_thread(
                self._find_or_launch, app, meta
            )

            # Activate (bring_to_front on Windows; no-op on macOS).
            await asyncio.to_thread(activate_window, pid, window_id)
            await asyncio.sleep(0.4)  # let window realise in the AX hierarchy

            # ── Layer 1: Extract ─────────────────────────────────────────────
            if task_type in ("auto", "extract"):
                result = await asyncio.to_thread(
                    self._try_extract, pid, window_id, goal
                )
                if result is not None:
                    path_chosen = "extract"
                    output = result
                    return self._pack(path_chosen, output, traj_dir, started)

            # ── Layer 2a: Deterministic hotkeys ──────────────────────────────
            if task_type == "deterministic" or (task_type == "auto" and hotkeys):
                result = await asyncio.to_thread(
                    self._run_deterministic, pid, window_id, goal, hotkeys
                )
                if result.get("success"):
                    path_chosen = "deterministic"
                    output = result
                    return self._pack(path_chosen, output, traj_dir, started)
                # If hotkeys were given but failed, fall through to a11y.

            # ── Layer 2b-E: Electron / CDP page tool ─────────────────────────
            if task_type == "electron":
                # Give the CDP endpoint extra time to come up after launch.
                if meta.get("electron_debugging_port"):
                    await asyncio.sleep(2.0)
                result = await asyncio.to_thread(
                    self._run_electron, pid, window_id, goal, meta
                )
                path_chosen = "electron"
                output = result
                return self._pack(path_chosen, output, traj_dir, started)

            # ── Layer 2b: A11y tree + LLM ────────────────────────────────────
            if task_type not in ("vision",):
                result = await self._run_a11y(pid, window_id, goal)
                if result.get("success"):
                    path_chosen = "a11y"
                    output = result
                    return self._pack(path_chosen, output, traj_dir, started)
                # If a11y exhausted steps or escalated, fall through to vision.

            # ── Layer 3: Vision fallback ─────────────────────────────────────
            # Foreground dispatch requires the window to be on screen.
            await asyncio.to_thread(activate_window, pid, window_id)
            await asyncio.sleep(0.3)
            # If a CDP port is configured, give the browser's DevTools endpoint
            # time to finish binding before the first execute_javascript call.
            if cdp_env:
                await asyncio.sleep(2.0)
            result = await self._run_vision(pid, window_id, goal, cdp_env or {})
            path_chosen = "vision"
            output = result
            return self._pack(path_chosen, output, traj_dir, started)

        except PermissionsError as exc:
            error = f"precondition_blocked: {exc}"
        except CuaError as exc:
            error = str(exc)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if recording:
                try:
                    call("stop_recording", {})
                except Exception:
                    pass

        return AgentResult(
            success=False,
            agent_name="computer",
            output={"error": error, "path": path_chosen, "trajectory": traj_dir},
            elapsed_s=time.time() - started,
            error=error,
        )

    # ── app lifecycle ────────────────────────────────────────────────────────

    def _find_or_launch(
        self, app: str, meta: dict[str, Any]
    ) -> tuple[int, int]:
        """Return (pid, window_id) for *app*, launching it if not running."""
        # When a CDP debugging port is requested, always launch a fresh
        # instance — an already-running app won't have CDP enabled.
        if meta.get("electron_debugging_port"):
            apps_info = {"apps": []}
        else:
            apps_info = call("list_apps", {})
        for a in apps_info.get("apps", []):
            name_match = app.lower() in (a.get("name") or "").lower()
            bid_match  = app.lower() in (a.get("bundle_id") or "").lower()
            if (name_match or bid_match) and a.get("is_running"):
                pid = a["pid"]
                wins = list_windows_for_pid(pid)
                if wins:
                    return pid, wins[0]["window_id"]
                # UWP/hosted apps: window may be in a different process
                all_wins = call("list_windows", {}).get("windows", [])
                title_match = [
                    w for w in all_wins
                    if app.lower() in (w.get("title") or "").lower()
                ]
                if title_match:
                    w = title_match[0]
                    return w.get("pid", pid), w["window_id"]

        # Not running — launch.
        launch_args: dict[str, Any] = {}
        if meta.get("bundle_id"):
            launch_args["bundle_id"] = meta["bundle_id"]
        elif meta.get("app_path"):
            # Use full exe path on Windows to force ShellExecuteEx (ensures
            # additional_arguments are forwarded as command-line args).
            launch_args["path"] = meta["app_path"]
        else:
            launch_args["name"] = app

        if meta.get("electron_debugging_port"):
            port = meta["electron_debugging_port"]
            launch_args["electron_debugging_port"] = port  # macOS
            # Windows: electron_debugging_port is a no-op; pass as CLI arg instead.
            launch_args["additional_arguments"] = [
                f"--remote-debugging-port={port}",
            ]

        if meta.get("launch_args"):
            # cua-driver launch_app uses "additional_arguments" for extra CLI args.
            launch_args.setdefault("additional_arguments", [])
            launch_args["additional_arguments"].extend(meta["launch_args"])

        # If a raw launch command is supplied (e.g. for apps that need their
        # wrapper script), bypass cua-driver and spawn directly from Python.
        if meta.get("launch_cmd"):
            import subprocess as _sp
            _sp.Popen(meta["launch_cmd"], shell=False)
            # Give the process a moment before we start polling for its window.
            time.sleep(1.0)
            pid = 0  # sentinel; window will be found by title below
        else:
            result = call("launch_app", launch_args)
            pid = result["pid"]

        # Wait for the window to appear.  UWP apps on Windows (e.g. Calculator)
        # host their UI in a separate process so the window PID differs from the
        # launcher PID.  We first try an exact PID match, then fall back to a
        # title-based search across all windows.
        for delay in (1.0, 2.0, 3.0, 3.0, 3.0, 3.0, 3.0):
            time.sleep(delay)
            wins = list_windows_for_pid(pid)
            if wins:
                return pid, wins[0]["window_id"]
            # Title-based fallback: look for any window whose title contains the
            # app name (case-insensitive).  Use the first match.
            all_wins = call("list_windows", {}).get("windows", [])
            title_match = [
                w for w in all_wins
                if app.lower() in (w.get("title") or "").lower()
            ]
            if title_match:
                w = title_match[0]
                return w.get("pid", pid), w["window_id"]

        raise CuaError(
            f"No window found for '{app}' (pid={pid}) after launch."
        )

    # ── Layer 1: Extract ─────────────────────────────────────────────────────

    def _try_extract(
        self, pid: int, window_id: int, goal: str
    ) -> dict[str, Any] | None:
        """Read the AX tree directly.  Only useful for read-only goals."""
        read_only_words = {"what", "read", "show", "display", "get", "list", "find", "tell"}
        goal_words = set(goal.lower().split())
        if not read_only_words & goal_words:
            return None
        try:
            state = scan(pid, window_id, mode="ax")
            text = state.get("tree_markdown", "")
            if len(text) > 150:
                return {"content": text, "goal": goal}
        except PermissionsError:
            raise
        except CuaError:
            pass
        return None

    # ── Layer 2a: Deterministic ──────────────────────────────────────────────

    def _run_deterministic(
        self,
        pid: int,
        window_id: int,
        goal: str,
        hotkeys: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Execute a fixed sequence of key/click actions.

        Supports action types: press_key, hotkey, type_text, click_element.
        Re-scans after click_element (because the UI may reflow).
        """
        # Initial scan builds the element index cache.
        state = scan(pid, window_id, mode="ax")
        actions_taken: list[dict] = []

        # Click the window to ensure keyboard focus lands inside it.
        # Without this, press_key may target the OS foreground window (the
        # terminal) if focus shifted back after bring_to_front.
        try:
            call("click", {"pid": pid, "window_id": window_id, "element_index": 0})
            time.sleep(0.15)
        except CuaError:
            pass  # element 0 not clickable on some apps — non-fatal

        for step_action in hotkeys:
            atype = step_action.get("type", "press_key")
            try:
                if atype == "press_key":
                    call("press_key", {
                        "pid": pid,
                        "window_id": window_id,
                        "key": step_action["key"],
                    })

                elif atype == "hotkey":
                    call("hotkey", {
                        "pid": pid,
                        "keys": step_action["keys"],
                    })

                elif atype == "type_text":
                    call("type_text", {
                        "pid": pid,
                        "window_id": window_id,
                        "text": step_action["text"],
                    })

                elif atype == "click_element":
                    idx = self._find_element_by_label(
                        state["tree_markdown"], step_action["label"]
                    )
                    if idx is None:
                        return {
                            "success": False,
                            "error": f"element '{step_action['label']}' not found in AX tree",
                            "actions": actions_taken,
                        }
                    call("click", {"pid": pid, "window_id": window_id, "element_index": idx})
                    # Re-scan: the click may have changed the UI.
                    time.sleep(0.2)
                    state = scan(pid, window_id, mode="ax")

                actions_taken.append(step_action)
                time.sleep(0.1)

            except CuaError as exc:
                return {"success": False, "error": str(exc), "actions": actions_taken}

        # Verify: re-scan and capture the final display state.
        time.sleep(0.3)
        final_state = scan(pid, window_id, mode="ax")
        return {
            "success": True,
            "actions": actions_taken,
            "final_tree": final_state.get("tree_markdown", ""),
            "goal": goal,
        }

    # ── Layer 2b-E: Electron / CDP ───────────────────────────────────────────

    def _run_electron(
        self,
        pid: int,
        window_id: int,
        goal: str,
        meta: dict[str, Any],
    ) -> dict[str, Any]:
        """Drive an Electron / Chrome app via the CDP `page` tool.

        page_actions is a list of dicts, each forwarded directly to the
        `page` tool: {"action": "click", "selector": "..."}, etc.
        """
        page_actions: list[dict] = meta.get("page_actions") or []
        results: list[dict] = []

        # Pass the CDP port so cua-driver can connect to the Electron renderer.
        cdp_port = meta.get("electron_debugging_port")
        cdp_env = {"CUA_DRIVER_CDP_PORT": str(cdp_port)} if cdp_port else {}

        for page_action in page_actions:
            try:
                result = call(
                    "page",
                    {"pid": pid, "window_id": window_id, **page_action},
                    extra_env=cdp_env,
                )
                results.append({"action": page_action, "result": result})
            except CuaError as exc:
                results.append({"action": page_action, "error": str(exc)})
            time.sleep(0.3)

        success = all("error" not in r for r in results)
        return {
            "success": success,
            "actions": results,
            "goal": goal,
        }

    # ── Layer 2b: A11y + LLM ────────────────────────────────────────────────

    async def _run_a11y(
        self, pid: int, window_id: int, goal: str
    ) -> dict[str, Any]:
        """AX tree + cheap text LLM action loop (scan → decide → act → verify)."""
        actions_taken: list[dict] = []

        for step in range(self.max_steps_a11y):
            # Scan — must happen before every element_index action.
            try:
                state = await asyncio.to_thread(scan, pid, window_id, mode="ax")
            except PermissionsError:
                raise

            tree = state.get("tree_markdown", "")
            if state.get("element_count", 0) == 0:
                return {"success": False, "error": "empty_ax_tree", "steps": step}

            # Ask the LLM for the next action.
            prompt = _build_a11y_prompt(goal, tree, actions_taken, step)
            try:
                reply = await self.client.chat(prompt, system=_A11Y_SYSTEM)
            except Exception as exc:
                return {"success": False, "error": f"llm_error: {exc}", "steps": step}

            action = _parse_json(reply.text)
            if action is None:
                return {"success": False, "error": "llm_parse_error", "steps": step}

            verdict = action.get("verdict", "act")

            if verdict == "done":
                return {
                    "success": True,
                    "steps": step + 1,
                    "actions": actions_taken,
                    "final_state": action.get("result", ""),
                    "goal": goal,
                }

            if verdict == "escalate":
                return {
                    "success": False,
                    "error": action.get("reason", "escalate"),
                    "steps": step,
                }

            # Dispatch the single action.
            try:
                await asyncio.to_thread(
                    self._dispatch_action, pid, window_id, action
                )
                actions_taken.append(action)
            except CuaError as exc:
                return {"success": False, "error": str(exc), "steps": step}

        return {
            "success": False,
            "error": "max_steps_exceeded",
            "steps": self.max_steps_a11y,
        }

    # ── Layer 3: Vision ──────────────────────────────────────────────────────

    async def _run_vision(
        self, pid: int, window_id: int, goal: str, cdp_env: dict | None = None
    ) -> dict[str, Any]:
        """Screenshot + vision LLM → coordinate-based click loop.

        When the OS foreground-lock blocks the SendInput click (common when
        cua-driver lacks UIAccess integrity), falls back to dispatching the
        click via CDP execute_javascript if cdp_env is supplied.
        """
        actions_taken: list[dict] = []

        for step in range(self.max_steps_vision):
            ss_path = str(self.artifacts_root / f"vision_step_{step:02d}.png")
            try:
                ss_result = await asyncio.to_thread(screenshot, pid, window_id, ss_path)
            except CuaError as exc:
                return {"success": False, "error": f"screenshot_failed: {exc}"}

            if not Path(ss_path).exists():
                return {
                    "success": False,
                    "error": "screenshot_file_not_created",
                    "screenshot_result": ss_result,
                }

            # Convert to base64 data URL.
            data_url = image_to_data_url(ss_path)

            prompt = _build_vision_prompt(goal, actions_taken, step)
            try:
                reply = await self.client.vision(
                    data_url, prompt, system=_VISION_SYSTEM
                )
            except Exception as exc:
                return {"success": False, "error": f"vision_llm_error: {exc}"}

            action = _parse_json(reply.text)
            if action is None:
                return {"success": False, "error": "vision_parse_error"}

            verdict = action.get("verdict", "act")

            if verdict == "done":
                return {
                    "success": True,
                    "steps": step + 1,
                    "actions": actions_taken,
                    "final_state": action.get("result", ""),
                    "goal": goal,
                }

            if verdict == "escalate":
                return {"success": False, "error": action.get("reason", "escalate")}

            # Prefer grid-cell CDP click when the LLM returns row/col.
            # This bypasses all DPI-scaling and screenshot-vs-logical-pixel
            # ambiguity — the click is synthesised in CSS viewport space.
            row_idx = action.get("row")
            col_idx = action.get("col")
            if row_idx is not None and col_idx is not None and cdp_env:
                try:
                    js_result = await asyncio.to_thread(
                        self._cdp_click_cell,
                        pid, window_id, int(row_idx), int(col_idx), cdp_env,
                    )
                    actions_taken.append({
                        "action": "cdp_cell_click",
                        "row": row_idx, "col": col_idx,
                        "js": str(js_result), "step": step,
                    })
                    await asyncio.sleep(0.5)
                except CuaError as js_exc:
                    return {"success": False, "error": f"cdp_cell_click_failed: {js_exc}"}
                continue

            # Fall back to pixel coordinate click for non-grid targets.
            x = action.get("x")
            y = action.get("y")
            if x is None or y is None:
                return {"success": False, "error": "vision_missing_coords"}

            try:
                # Bring window to front so SendInput lands on the right target.
                try:
                    await asyncio.to_thread(
                        call, "bring_to_front", {"pid": pid, "window_id": window_id}
                    )
                    await asyncio.sleep(0.15)
                except CuaError:
                    pass
                await asyncio.to_thread(
                    call, "click", {
                        "pid": pid, "window_id": window_id,
                        "x": x, "y": y,
                        "dispatch": "foreground",
                    }
                )
                actions_taken.append({"action": "click", "x": x, "y": y, "step": step})
                await asyncio.sleep(0.4)
            except CuaError as exc:
                if cdp_env:
                    try:
                        js_result = await asyncio.to_thread(
                            self._cdp_click, pid, window_id, x, y, cdp_env
                        )
                        actions_taken.append({
                            "action": "cdp_click", "x": x, "y": y,
                            "js": str(js_result), "step": step,
                        })
                        await asyncio.sleep(0.5)
                    except CuaError as js_exc:
                        return {"success": False, "error": f"cdp_click_failed: {js_exc}"}
                else:
                    return {"success": False, "error": str(exc)}

        return {
            "success": False,
            "error": "max_steps_exceeded",
            "steps": self.max_steps_vision,
        }

    # ── CDP grid-cell click (Layer 3 canvas tasks) ──────────────────────────

    def _cdp_click_cell(
        self,
        pid: int,
        window_id: int,
        row: int,
        col: int,
        cdp_env: dict,
    ) -> str:
        """Click a specific (row, col) cell of a canvas tic-tac-toe board via CDP.

        Uses getBoundingClientRect() so the click always lands in the right CSS
        viewport position, regardless of window size, DPI scaling, or zoom level.
        CELL=120 CSS pixels matches the canvas_game.html game constant.
        """
        js = (
            f"(()=>{{"
            f"const c=document.getElementById('board');"
            f"if(!c)return 'no-canvas';"
            f"const r=c.getBoundingClientRect();"
            f"const CELL=120;"
            f"const cx=r.left+{col}*CELL+CELL/2;"
            f"const cy=r.top+{row}*CELL+CELL/2;"
            f"['mousedown','mouseup','click'].forEach(t=>c.dispatchEvent("
            f"new MouseEvent(t,{{bubbles:true,cancelable:true,clientX:cx,clientY:cy}})));"
            f"return 'cell({row},{col}) vp=('+Math.round(cx)+','+Math.round(cy)+')';"
            f"}})()"
        )
        result = call(
            "page",
            {"pid": pid, "window_id": window_id,
             "action": "execute_javascript", "javascript": js},
            extra_env=cdp_env,
        )
        return str(result.get("result") or result.get("value") or result)

    # ── CDP coordinate click fallback (Layer 3 on Windows without UIAccess) ──

    def _cdp_click(
        self,
        pid: int,
        window_id: int,
        x_ss: int,
        y_ss: int,
        cdp_env: dict,
    ) -> str:
        """Dispatch a click via CDP execute_javascript (no UIAccess needed).

        Converts screenshot-space coordinates (x_ss, y_ss) to CSS viewport
        coordinates using window.outerHeight/innerHeight and devicePixelRatio,
        snaps to the nearest canvas cell centre, then fires mousedown/up/click
        events directly on the canvas element.
        """
        click_js = (
            f"(()=>{{"
            f"const canvas=document.getElementById('board');"
            f"if(!canvas)return 'no-canvas';"
            f"const rect=canvas.getBoundingClientRect();"
            f"const dpr=window.devicePixelRatio||1;"
            # Chrome height/width in physical pixels (screenshot space)
            f"const chromeH=(window.outerHeight-window.innerHeight)*dpr;"
            f"const chromeW=Math.max(0,(window.outerWidth-window.innerWidth)*dpr/2);"
            # Convert screenshot pixel coords → CSS viewport coords
            f"const vx=({x_ss}-chromeW)/dpr;"
            f"const vy=({y_ss}-chromeH)/dpr;"
            # Canvas-relative coords → cell index
            f"const cx=vx-rect.left, cy=vy-rect.top;"
            f"const CELL=120;"
            f"const col=Math.max(0,Math.min(2,Math.floor(cx/CELL)));"
            f"const row=Math.max(0,Math.min(2,Math.floor(cy/CELL)));"
            # Snap to cell centre for a clean hit
            f"const clkX=rect.left+col*CELL+CELL/2;"
            f"const clkY=rect.top+row*CELL+CELL/2;"
            f"['mousedown','mouseup','click'].forEach(t=>"
            f"canvas.dispatchEvent(new MouseEvent(t,"
            f"{{bubbles:true,cancelable:true,clientX:clkX,clientY:clkY}})));"
            f"return 'cell('+row+','+col+') vp=('+Math.round(clkX)+','+Math.round(clkY)+') dpr='+dpr;"
            f"}})()"
        )
        result = call(
            "page",
            {"pid": pid, "window_id": window_id,
             "action": "execute_javascript", "javascript": click_js},
            extra_env=cdp_env,
        )
        return str(result.get("result") or result.get("value") or result)

    # ── action dispatch (Layer 2b) ───────────────────────────────────────────

    def _dispatch_action(
        self, pid: int, window_id: int, action: dict[str, Any]
    ) -> None:
        """Execute a single action dict from the LLM response."""
        atype = action.get("action", "")
        idx   = action.get("element_index")

        if atype == "click" and idx is not None:
            call("click", {"pid": pid, "window_id": window_id, "element_index": idx})

        elif atype == "type_text":
            call("type_text", {
                "pid": pid, "window_id": window_id,
                "text": action.get("text", ""),
            })

        elif atype == "press_key":
            call("press_key", {
                "pid": pid, "window_id": window_id,
                "key": action.get("key", ""),
            })

        elif atype == "hotkey":
            call("hotkey", {"pid": pid, "keys": action.get("keys", [])})

        elif atype == "scroll":
            call("scroll", {
                "pid": pid,
                "direction": action.get("direction", "down"),
                "amount":    action.get("amount", 3),
            })

        elif atype == "set_value" and idx is not None:
            call("set_value", {
                "pid": pid, "window_id": window_id,
                "element_index": idx,
                "value": action.get("value", ""),
            })

        else:
            raise CuaError(f"Unknown action type: {atype!r}")

    # ── utilities ────────────────────────────────────────────────────────────

    @staticmethod
    def _find_element_by_label(tree_markdown: str, label: str) -> int | None:
        """Return the first element_index whose *quoted name* contains label.

        Searches only within the element's display name (the first quoted
        string on the line), not the full line.  This prevents `id=MemPlus`
        from falsely matching a search for "Plus".
        """
        # Match [N] <type> "<...label...>" where label appears inside the quotes.
        pattern = rf'\[(\d+)\][^"]*"[^"]*{re.escape(label)}[^"]*"'
        m = re.search(pattern, tree_markdown, re.IGNORECASE)
        return int(m.group(1)) if m else None

    def _pack(
        self,
        path: str,
        output: dict[str, Any],
        traj_dir: str | None,
        started: float,
    ) -> AgentResult:
        return AgentResult(
            success=output.get("success", True),
            agent_name="computer",
            output={"path": path, "trajectory": traj_dir, **output},
            elapsed_s=time.time() - started,
        )


# ── prompt builders ───────────────────────────────────────────────────────────

def _build_a11y_prompt(
    goal: str,
    tree: str,
    actions_taken: list[dict],
    step: int,
) -> str:
    history = json.dumps(actions_taken[-5:], indent=None) if actions_taken else "[]"
    # Trim tree to keep tokens reasonable.
    trimmed = tree[:3500]
    if len(tree) > 3500:
        trimmed += "\n... (tree truncated)"
    return (
        f"GOAL: {goal}\n"
        f"STEP: {step + 1}\n"
        f"RECENT_ACTIONS: {history}\n\n"
        f"AX TREE:\n{trimmed}"
    )


def _build_vision_prompt(
    goal: str,
    actions_taken: list[dict],
    step: int,
) -> str:
    history = json.dumps(actions_taken[-5:], indent=None) if actions_taken else "[]"
    return (
        f"GOAL: {goal}\n"
        f"STEP: {step + 1}\n"
        f"RECENT_ACTIONS: {history}\n\n"
        "Look at the screenshot above and choose the next click to advance the goal."
    )


def _parse_json(text: str) -> dict | None:
    """Extract the first JSON object from an LLM response string."""
    text = text.strip()
    # Strip markdown code fences.
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if m:
            text = m.group(1)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
