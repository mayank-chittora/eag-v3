"""Thin Python wrapper around the cua-driver CLI daemon.

All calls proxy through `cua-driver serve` so every invocation shares
the same in-memory element-index cache.  The daemon must be running
before any element_index-addressed action; `ensure_daemon()` starts it
if needed.

Usage pattern (matches the scan-act-verify loop from the course notes):

    ensure_daemon()
    pid, wid = launch_and_find("Calculator")
    activate_window(pid, wid)           # bring_to_front on Windows
    state = scan(pid, wid, query="button")
    call("click", {"pid": pid, "window_id": wid, "element_index": 5})
    state = scan(pid, wid)              # re-scan; indices shift after actions
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from typing import Any


# ── locate the binary ────────────────────────────────────────────────────────

def _find_cua() -> str:
    """Return the path to cua-driver, searching PATH and common install dirs."""
    found = shutil.which("cua-driver")
    if found:
        return found
    from pathlib import Path
    candidates = [
        # macOS / Linux
        Path.home() / ".local" / "bin" / "cua-driver",
        # Windows: cua installer drops versioned releases here
        *sorted(
            (Path.home() / ".cua-driver" / "packages" / "releases").glob(
                "**/cua-driver.exe"
            ),
            reverse=True,  # newest version first
        ),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return "cua-driver"  # let subprocess raise a clear error


CUA = _find_cua()


# ── exceptions ───────────────────────────────────────────────────────────────

class CuaError(RuntimeError):
    """cua-driver returned a non-zero exit code or an unexpected response."""


class PermissionsError(CuaError):
    """get_window_state returned element_count=0 — likely a missing OS grant."""


# ── core call ────────────────────────────────────────────────────────────────

def call(
    tool: str,
    args: dict[str, Any],
    extra_env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Invoke one cua-driver tool through the running daemon.

    Raises CuaError on non-zero exit.  Returns the parsed JSON dict.
    extra_env is merged into the subprocess environment (e.g. CUA_DRIVER_CDP_PORT).
    """
    import os
    env = {**os.environ, **(extra_env or {})}
    proc = subprocess.run(
        [CUA, "call", tool, json.dumps(args)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        env=env,
    )
    if proc.returncode != 0:
        raise CuaError(f"{tool} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    text = proc.stdout.strip()
    if text.startswith("{"):
        return json.loads(text)
    return {"raw": text}


# ── daemon management ────────────────────────────────────────────────────────

def _start_daemon(extra_env: dict[str, str] | None = None) -> None:
    import os
    env = {**os.environ, **(extra_env or {})}
    subprocess.Popen(
        [CUA, "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    for _ in range(6):
        time.sleep(0.5)
        chk = subprocess.run(
            [CUA, "status"],
            capture_output=True, encoding="utf-8", errors="replace", timeout=3,
        )
        if "is running" in chk.stdout:
            return
    raise CuaError("cua-driver daemon did not start within 3 s")


def ensure_daemon(extra_env: dict[str, str] | None = None) -> None:
    """Start `cua-driver serve` if no daemon is already running.

    If extra_env is supplied and the daemon is already up, it is killed and
    restarted so the new environment variables take effect.  Pass
    extra_env={"CUA_DRIVER_CDP_PORT": "9222"} before running Electron tasks.
    """
    status = subprocess.run(
        [CUA, "status"], capture_output=True, encoding="utf-8", errors="replace", timeout=5
    )
    if "is running" in status.stdout:
        if extra_env:
            # Restart with the new env (e.g. CUA_DRIVER_CDP_PORT).
            subprocess.run(
                [CUA, "stop"], capture_output=True, encoding="utf-8", errors="replace", timeout=10
            )
            time.sleep(0.5)
            _start_daemon(extra_env)
        return
    _start_daemon(extra_env)


# ── perception helpers ───────────────────────────────────────────────────────

def scan(
    pid: int,
    window_id: int,
    *,
    query: str | None = None,
    mode: str = "ax",
) -> dict[str, Any]:
    """Call get_window_state and guard against an empty AX tree.

    An empty tree (element_count == 0) in ax mode almost always means
    either missing OS permissions or the window hasn't been activated yet.
    We raise PermissionsError immediately so the cascade can surface it
    rather than silently failing on a later element_index lookup.
    """
    args: dict[str, Any] = {
        "pid": pid,
        "window_id": window_id,
        "capture_mode": mode,
    }
    if query:
        args["query"] = query
    state = call("get_window_state", args)
    if mode == "ax" and state.get("element_count", 0) == 0:
        raise PermissionsError(
            "cua-driver returned an empty AX tree. "
            "Check: (1) permissions granted, (2) window activated, "
            "(3) electron_debugging_port if this is an Electron app."
        )
    return state


def screenshot(pid: int, window_id: int, out_file: str) -> dict[str, Any]:
    """Capture a vision-mode screenshot to a PNG file on disk.

    On Windows, cua-driver returns the PNG as base64 in the JSON response
    rather than writing it to screenshot_out_file.  We handle both paths.
    """
    import base64
    from pathlib import Path as _Path
    result = call("get_window_state", {
        "pid": pid,
        "window_id": window_id,
        "capture_mode": "vision",
        "screenshot_out_file": out_file,
    })
    # If the file was not written (Windows behavior), decode base64 ourselves.
    if not _Path(out_file).exists() and result.get("screenshot_png_b64"):
        png_data = base64.b64decode(result["screenshot_png_b64"])
        _Path(out_file).write_bytes(png_data)
    return result


# ── window management ────────────────────────────────────────────────────────

def activate_window(pid: int, window_id: int) -> None:
    """Bring the window to the foreground.

    bring_to_front works on Windows.  On macOS/Linux it is a documented
    no-op; we swallow the error and let callers add a sleep + re-scan.
    """
    try:
        call("bring_to_front", {"pid": pid, "window_id": window_id})
    except CuaError:
        pass  # expected on macOS/Linux


def list_windows_for_pid(pid: int) -> list[dict[str, Any]]:
    """Return all top-level windows belonging to `pid`."""
    result = call("list_windows", {})
    return [w for w in result.get("windows", []) if w.get("pid") == pid]
