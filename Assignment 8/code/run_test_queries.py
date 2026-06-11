"""Validation script for the five base test queries.

Runs each query (except the manually-executed resume query) against the agent,
reads the persisted session state from disk, and validates against the
expectations defined in test_queries.json.

Usage:
    uv run python run_test_queries.py             # skip 'resume' query
    uv run python run_test_queries.py --all       # include 'resume' query
    uv run python run_test_queries.py --id hello  # run a single query by id
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
STATE_DIR = ROOT / "state" / "sessions"
QUERIES_FILE = ROOT / "test_queries.json"


# ── helpers ───────────────────────────────────────────────────────────────────

def run_query(query: str) -> tuple[str | None, float, str]:
    """Run the agent with *query*, return (session_id, wall_clock_s, stdout)."""
    start = time.time()
    result = subprocess.run(
        ["uv", "run", "python", "flow.py", query],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    elapsed = time.time() - start
    output = result.stdout + result.stderr

    sid = None
    for line in output.splitlines():
        m = re.search(r"session\s+(s\w+-[0-9a-f]+)", line)
        if m:
            sid = m.group(1)
            break

    return sid, elapsed, output


def load_session(sid: str) -> dict | None:
    """Load graph.json for a session; return None if not found."""
    path = STATE_DIR / sid / "graph.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def get_node_skills(graph: dict) -> list[str]:
    return [n.get("skill", "") for n in graph.get("nodes", [])]


def get_final_answer(sid: str) -> str:
    """Find the final_answer from the formatter node's persisted state."""
    nodes_dir = STATE_DIR / sid / "nodes"
    if not nodes_dir.exists():
        return ""
    for node_file in sorted(nodes_dir.iterdir()):
        try:
            data = json.loads(node_file.read_text())
            if data.get("skill") == "formatter" and data.get("status") == "complete":
                result = data.get("result") or {}
                output = result.get("output") or {}
                fa = output.get("final_answer", "")
                if fa:
                    return fa
        except Exception:
            continue
    return ""


def get_elapsed_by_skill(sid: str) -> dict[str, list[float]]:
    """Return {skill: [elapsed_s, ...]} for all complete nodes."""
    nodes_dir = STATE_DIR / sid / "nodes"
    out: dict[str, list[float]] = {}
    if not nodes_dir.exists():
        return out
    for node_file in sorted(nodes_dir.iterdir()):
        try:
            data = json.loads(node_file.read_text())
            skill = data.get("skill", "")
            result = data.get("result") or {}
            elapsed = result.get("elapsed_s", 0.0)
            out.setdefault(skill, []).append(elapsed)
        except Exception:
            continue
    return out


# ── validation ────────────────────────────────────────────────────────────────

def validate(spec: dict, sid: str, wall_clock: float) -> list[str]:
    """Return a list of failure messages; empty list means PASS."""
    failures = []
    graph = load_session(sid)
    if graph is None:
        return [f"session directory not found: {sid}"]

    skills_in_graph = get_node_skills(graph)
    node_count = len(skills_in_graph)
    expected_count = spec.get("expected_node_count")
    max_clock = spec.get("max_wall_clock_s")

    # Node count check (allow ±1 for critic auto-insertion)
    if expected_count is not None:
        if abs(node_count - expected_count) > 1:
            failures.append(
                f"node count {node_count} differs from expected "
                f"{expected_count} by more than 1"
            )

    # Expected skills present
    for skill in spec.get("expected_skills", []):
        if skill not in skills_in_graph:
            failures.append(f"expected skill '{skill}' not found in graph")

    # Wall-clock
    if max_clock is not None and wall_clock > max_clock:
        failures.append(
            f"wall-clock {wall_clock:.1f}s exceeded limit {max_clock}s"
        )

    # Final answer content
    final_answer = get_final_answer(sid).lower()
    for keyword in spec.get("answer_contains", []):
        if keyword.lower() not in final_answer:
            failures.append(f"final answer missing keyword '{keyword}'")

    # answer_contains_any — at least one must match
    any_keywords = spec.get("answer_contains_any", [])
    if any_keywords:
        if not any(kw.lower() in final_answer for kw in any_keywords):
            failures.append(
                f"final answer missing all of: {any_keywords}"
            )

    # Parallel layer check
    parallel_skills = spec.get("parallel_layer_skills", [])
    parallel_count = spec.get("parallel_layer_count", 0)
    if parallel_skills and parallel_count > 1:
        elapsed_by_skill = get_elapsed_by_skill(sid)
        for ps in parallel_skills:
            times = elapsed_by_skill.get(ps, [])
            if len(times) < parallel_count:
                failures.append(
                    f"expected {parallel_count} parallel '{ps}' nodes, "
                    f"found {len(times)}"
                )
            elif len(times) >= parallel_count:
                # Parallel wall-clock should be ≤ max branch, not sum
                max_branch = max(times[:parallel_count])
                sum_branches = sum(times[:parallel_count])
                if sum_branches > 0:
                    ratio = sum_branches / max_branch
                    if ratio > parallel_count * 0.85:
                        failures.append(
                            f"parallel '{ps}' nodes may have run serially "
                            f"(sum={sum_branches:.1f}s, max={max_branch:.1f}s, "
                            f"ratio={ratio:.2f})"
                        )

    return failures


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate base test queries")
    parser.add_argument("--all", action="store_true",
                        help="Include queries marked skip_auto_run")
    parser.add_argument("--id", dest="query_id",
                        help="Run a single query by its id")
    args = parser.parse_args()

    specs = json.loads(QUERIES_FILE.read_text())

    if args.query_id:
        specs = [s for s in specs if s["id"] == args.query_id]
        if not specs:
            print(f"No query with id '{args.query_id}' found in {QUERIES_FILE.name}")
            sys.exit(1)

    results = []
    for spec in specs:
        if spec.get("skip_auto_run") and not args.all:
            print(f"\n[SKIP] {spec['id']:20s} — {spec['description']}")
            print("        Run manually: see description for instructions.")
            continue

        print(f"\n{'─' * 70}")
        print(f"[RUN]  {spec['id']:20s} | {spec['description']}")
        print(f"       query: {spec['query'][:80]}")

        try:
            sid, wall_clock, output = run_query(spec["query"])
        except subprocess.TimeoutExpired:
            print(f"       TIMEOUT after 300s")
            results.append({"id": spec["id"], "status": "FAIL",
                             "failures": ["process timed out"]})
            continue
        except Exception as e:
            print(f"       ERROR: {e}")
            results.append({"id": spec["id"], "status": "FAIL",
                             "failures": [str(e)]})
            continue

        if sid is None:
            print(f"       WARNING: could not extract session id from output")
            print(f"       stdout/stderr tail:\n{output[-400:]}")
            results.append({"id": spec["id"], "status": "FAIL",
                             "failures": ["session id not found in output"]})
            continue

        print(f"       session: {sid}  |  wall-clock: {wall_clock:.1f}s")

        failures = validate(spec, sid, wall_clock)
        status = "PASS" if not failures else "FAIL"
        print(f"       status: {status}")
        for f in failures:
            print(f"         ✗ {f}")

        final_answer = get_final_answer(sid)
        if final_answer:
            print(f"       answer: {final_answer[:200]}")

        results.append({
            "id": spec["id"],
            "session_id": sid,
            "wall_clock_s": round(wall_clock, 2),
            "status": status,
            "failures": failures,
        })

    # Summary table
    print(f"\n{'═' * 70}")
    print(f"{'QUERY':<22} {'STATUS':<8} {'WALL-CLOCK':>12}  DETAILS")
    print(f"{'─' * 70}")
    all_pass = True
    for r in results:
        status = r["status"]
        wc = f"{r.get('wall_clock_s', 0):.1f}s" if "wall_clock_s" in r else "—"
        detail = "; ".join(r.get("failures", [])) or "all checks passed"
        print(f"{r['id']:<22} {status:<8} {wc:>12}  {detail[:40]}")
        if status != "PASS":
            all_pass = False
    print(f"{'═' * 70}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
