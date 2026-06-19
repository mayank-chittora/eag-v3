"""Generate the 8-section run report from a persisted session.

Usage:
    uv run python report.py                  # picks the latest session
    uv run python report.py <session_id>     # specific session
    uv run python report.py --list           # list available sessions
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from persistence import SessionStore, list_sessions

SESSIONS_ROOT = Path(__file__).parent / "state" / "sessions"


# ── helpers ──────────────────────────────────────────────────────────────────

def _skill_label(node: dict) -> str:
    meta = node.get("metadata", {})
    label = meta.get("label") or node.get("id", "?")
    return f"{node['skill']}({label})"


def _dag_text(nodes: list[dict], edges: list[dict]) -> str:
    id_to_label = {n["id"]: _skill_label(n) for n in nodes}
    lines = []
    for e in edges:
        src = id_to_label.get(e["source"], e["source"])
        tgt = id_to_label.get(e["target"], e["target"])
        lines.append(f"  {src} → {tgt}")
    return "\n".join(lines) if lines else "  (no edges)"


def _browser_path(node: dict) -> str:
    result = node.get("result") or {}
    output = result.get("output") or {}
    path = output.get("layer_used") or output.get("method") or output.get("path")
    if path:
        return str(path)
    error = result.get("error") or ""
    if "Executable doesn't exist" in error or "playwright install" in error.lower():
        return "blocked — Playwright browser not installed"
    if not result.get("success", True):
        return f"blocked — {(error[:120] + '…') if len(error) > 120 else error}"
    return "static-extract (Layer 1)"


def _browser_actions(node: dict) -> list[str]:
    result = node.get("result") or {}
    output = result.get("output") or {}
    actions = output.get("actions") or output.get("steps") or []
    if isinstance(actions, list):
        return [str(a) for a in actions]
    return []


def _screenshots(session_dir: Path) -> list[Path]:
    browser_dir = session_dir / "browser"
    if not browser_dir.exists():
        return []
    return sorted(browser_dir.glob("*.png")) + sorted(browser_dir.glob("*.jpg"))


def _extracted_data(nodes: list[dict]) -> str:
    for skill in ("distiller", "researcher"):
        for n in nodes:
            if n.get("skill") == skill:
                result = n.get("result") or {}
                out = result.get("output") or {}
                findings = out.get("findings") or out.get("result") or out.get("text")
                if findings:
                    return str(findings)
    return "(none)"


def _final_answer(nodes: list[dict]) -> str:
    for n in reversed(nodes):
        if n.get("skill") == "formatter":
            result = n.get("result") or {}
            out = result.get("output") or {}
            ans = out.get("final_answer") or out.get("answer") or out.get("text")
            if ans:
                return str(ans)
    # fallback: last complete node output
    for n in reversed(nodes):
        result = n.get("result") or {}
        if result.get("success"):
            out = result.get("output") or {}
            if isinstance(out, dict):
                for v in out.values():
                    if isinstance(v, str) and len(v) > 30:
                        return v
            elif isinstance(out, str):
                return out
    return "(not found)"


def _cost_summary(nodes: list[dict]) -> tuple[int, float]:
    total_cost = 0.0
    turn_count = 0
    for n in nodes:
        result = n.get("result") or {}
        if result.get("success"):
            turn_count += 1
            total_cost += result.get("cost") or 0.0
    return turn_count, total_cost


# ── report ────────────────────────────────────────────────────────────────────

def generate_report(session_id: str) -> str:
    store = SessionStore(session_id)
    session_dir = SESSIONS_ROOT / session_id

    graph_path = session_dir / "graph.json"
    if not graph_path.exists():
        return f"ERROR: no graph.json under state/sessions/{session_id}/"

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    nodes: list[dict] = graph.get("nodes", [])
    edges: list[dict] = graph.get("edges", [])

    query = store.read_query() or "(not recorded)"

    browser_nodes = [n for n in nodes if n.get("skill") == "browser"]
    browser_node = browser_nodes[0] if browser_nodes else {}

    screenshots = _screenshots(session_dir)
    turn_count, total_cost = _cost_summary(nodes)

    sep = "─" * 72

    sections: list[str] = []

    # ── Section 1: Goal ──────────────────────────────────────────────────────
    sections.append(f"""## Section 1 — User Goal

{query}""")

    # ── Section 2: Planner DAG ───────────────────────────────────────────────
    dag_str = _dag_text(nodes, edges)
    node_summary = "\n".join(
        f"  [{n['status']:8s}] {_skill_label(n)}"
        for n in nodes
    )
    sections.append(f"""## Section 2 — Planner DAG

Edges:
{dag_str}

Node status:
{node_summary}""")

    # ── Section 3: Browser path ──────────────────────────────────────────────
    path = _browser_path(browser_node)
    meta = browser_node.get("metadata") or {}
    url = meta.get("url", "(no target URL)")
    goal = meta.get("goal", "")
    sections.append(f"""## Section 3 — Browser Path

Path used : {path}
Target URL : {url}
Browser goal: {goal}""")

    # ── Section 4: Browser actions ───────────────────────────────────────────
    actions = _browser_actions(browser_node)
    if actions:
        action_str = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions))
    else:
        status = (browser_node.get("result") or {}).get("success")
        if status is False:
            action_str = "  (browser skill did not execute — see Section 3 for reason)"
        else:
            action_str = "  (no discrete actions recorded; static extract used)"
    sections.append(f"""## Section 4 — Browser Actions

{action_str}""")

    # ── Section 5: Screenshots / page-state ──────────────────────────────────
    if screenshots:
        shot_list = "\n".join(f"  {p.name}  ({p.stat().st_size // 1024} KB)" for p in screenshots)
        shot_note = f"Saved under state/sessions/{session_id}/browser/\n{shot_list}"
    else:
        shot_note = "(no screenshots captured — browser skill did not reach a page)"
    sections.append(f"""## Section 5 — Screenshots / Page-State Logs

{shot_note}""")

    # ── Section 6: Extracted data ─────────────────────────────────────────────
    extracted = _extracted_data(nodes)
    sections.append(f"""## Section 6 — Extracted Data

{extracted}""")

    # ── Section 7: Final comparison ───────────────────────────────────────────
    final = _final_answer(nodes)
    sections.append(f"""## Section 7 — Final Comparison Table

{final}""")

    # ── Section 8: Cost summary ───────────────────────────────────────────────
    provider_rows = []
    for n in nodes:
        result = n.get("result") or {}
        if result.get("success"):
            provider = result.get("provider") or "—"
            elapsed = result.get("elapsed_s") or 0.0
            cost = result.get("cost") or 0.0
            provider_rows.append(
                f"  {_skill_label(n):35s}  {provider:12s}  {elapsed:6.1f}s  ${cost:.6f}"
            )
    provider_table = "\n".join(provider_rows) if provider_rows else "  (no data)"

    cost_str = f"${total_cost:.4f}" if total_cost else "$0.0000 (providers did not report cost)"
    sections.append(f"""## Section 8 — Turn Count & Cost Summary

Successful turns : {turn_count}
Total cost       : {cost_str}

Per-node breakdown:
  {'Agent':35s}  {'Provider':12s}  {'Elapsed':>7s}  Cost
  {sep}
{provider_table}""")

    # ── Assemble ──────────────────────────────────────────────────────────────
    header = f"""# Agent Run Report
Session : {session_id}
Query   : {query}
{sep}
"""
    return header + f"\n\n{sep}\n\n".join(sections)


# ── entry point ───────────────────────────────────────────────────────────────

def main() -> int:
    args = sys.argv[1:]

    if "--list" in args:
        sessions = list_sessions()
        if not sessions:
            print("No sessions found under state/sessions/")
            return 0
        print("Available sessions:")
        for s in sessions:
            print(f"  {s}")
        return 0

    if args:
        session_id = args[0]
    else:
        sessions = list_sessions()
        if not sessions:
            print("No sessions found. Run flow.py first.", file=sys.stderr)
            return 2
        session_id = sessions[-1]
        print(f"(using latest session: {session_id})\n")

    report = generate_report(session_id)
    print(report)

    out_path = SESSIONS_ROOT / session_id / "report.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"\n─ report saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
