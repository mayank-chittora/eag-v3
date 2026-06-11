"""Runner and reporter for the additional queries defined in additional_queries.json.

Runs each query against the agent, reads persisted session state, and produces
a detailed per-query report covering: node execution table, wall-clock, final
answer, and category-specific validation results.

Full results are also written to additional_queries_results.json.

Usage:
    uv run python run_additional_queries.py              # run all queries
    uv run python run_additional_queries.py --id <id>   # run one query
    uv run python run_additional_queries.py --dry-run   # show queries without running
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
QUERIES_FILE = ROOT / "additional_queries.json"
RESULTS_FILE = ROOT / "additional_queries_results.json"


# ── helpers ───────────────────────────────────────────────────────────────────

def run_query(query: str) -> tuple[str | None, float, str]:
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


def load_graph(sid: str) -> dict | None:
    path = STATE_DIR / sid / "graph.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_node_states(sid: str) -> list[dict]:
    nodes_dir = STATE_DIR / sid / "nodes"
    if not nodes_dir.exists():
        return []
    states = []
    for node_file in sorted(nodes_dir.iterdir()):
        try:
            states.append(json.loads(node_file.read_text()))
        except Exception:
            continue
    return states


def get_skills_list(graph: dict) -> list[str]:
    return [n.get("skill", "") for n in graph.get("nodes", [])]


def get_final_answer(node_states: list[dict]) -> str:
    for state in reversed(node_states):
        if state.get("skill") == "formatter" and state.get("status") == "complete":
            result = state.get("result") or {}
            output = result.get("output") or {}
            fa = output.get("final_answer", "")
            if fa:
                return fa
    return ""


def get_node_table(node_states: list[dict]) -> list[dict]:
    rows = []
    for state in node_states:
        result = state.get("result") or {}
        rows.append({
            "node_id": state.get("node_id", "?"),
            "skill": state.get("skill", "?"),
            "status": state.get("status", "?"),
            "elapsed_s": round(result.get("elapsed_s", 0.0), 2),
            "provider": result.get("provider", ""),
        })
    return rows


def compute_parallel_metrics(node_table: list[dict], skill: str, count: int) -> dict:
    times = [r["elapsed_s"] for r in node_table if r["skill"] == skill]
    if len(times) < count:
        return {"found": len(times), "expected": count, "ok": False}
    branch_times = times[:count]
    max_branch = max(branch_times)
    sum_branches = sum(branch_times)
    speedup = sum_branches / max_branch if max_branch > 0 else 1.0
    parallel_ok = sum_branches > max_branch * 1.2  # at least 20% saving vs serial
    return {
        "found": len(times),
        "expected": count,
        "branch_elapsed_s": branch_times,
        "max_branch_s": round(max_branch, 2),
        "sum_branches_s": round(sum_branches, 2),
        "speedup_ratio": round(speedup, 2),
        "ok": parallel_ok,
    }


# ── category-specific validators ─────────────────────────────────────────────

def validate_parallel_fan_out(spec: dict, node_table: list[dict],
                               skills_list: list[str]) -> dict:
    skill = spec.get("expected_parallel_skill", "researcher")
    count = spec.get("min_parallel_nodes", 3)
    metrics = compute_parallel_metrics(node_table, skill, count)
    failures = []
    if not metrics["ok"] and metrics["found"] < metrics["expected"]:
        failures.append(
            f"expected ≥{count} parallel '{skill}' nodes, found {metrics['found']}"
        )
    if metrics.get("speedup_ratio", 1.0) < 1.2 and metrics["found"] >= count:
        failures.append(
            f"parallel layer shows little speedup (ratio={metrics.get('speedup_ratio', 0):.2f}); "
            "nodes may have run serially"
        )
    return {"metrics": metrics, "failures": failures}


def validate_critic_scenario(spec: dict, skills_list: list[str],
                              node_table: list[dict]) -> dict:
    failures = []
    has_critic = "critic" in skills_list
    if spec.get("expected_critic") and not has_critic:
        failures.append("expected a critic node in the graph but none found")

    critic_verdict = None
    if has_critic:
        for row in node_table:
            if row["skill"] == "critic" and row["status"] == "complete":
                # verdict lives in the node state's result.output.verdict
                node_path_match = [
                    s for s in sorted(
                        (STATE_DIR / row.get("node_id", "")).parent.glob("*.json")
                    )
                ] if False else []
                break

    return {"has_critic": has_critic, "failures": failures}


def validate_coder_computation(spec: dict, skills_list: list[str],
                                final_answer: str) -> dict:
    failures = []
    if "coder" not in skills_list:
        failures.append("expected 'coder' node but not found in graph")
    if "sandbox_executor" not in skills_list:
        failures.append("expected 'sandbox_executor' node but not found in graph")
    for kw in spec.get("answer_contains", []):
        if kw.lower() not in final_answer.lower():
            failures.append(f"final answer missing expected value '{kw}'")
    return {"failures": failures}


def validate_new_skill(spec: dict, skills_list: list[str],
                       final_answer: str) -> dict:
    failures = []
    for skill in spec.get("expected_skills", []):
        if skill not in skills_list:
            failures.append(f"expected skill '{skill}' not in graph")
    for kw in spec.get("answer_contains", []):
        if kw.lower() not in final_answer.lower():
            failures.append(f"final answer missing keyword '{kw}'")
    return {"failures": failures}


def validate_generic(spec: dict, skills_list: list[str],
                     final_answer: str) -> dict:
    failures = []
    for skill in spec.get("expected_skills", []):
        if skill not in skills_list:
            failures.append(f"expected skill '{skill}' not in graph")
    for kw in spec.get("answer_contains", []):
        if kw.lower() not in final_answer.lower():
            failures.append(f"final answer missing keyword '{kw}'")
    return {"failures": failures}


# ── per-query report ──────────────────────────────────────────────────────────

def report_query(spec: dict, sid: str, wall_clock: float) -> dict:
    graph = load_graph(sid)
    if graph is None:
        return {"id": spec["id"], "session_id": sid,
                "status": "FAIL", "failures": ["session graph not found on disk"]}

    node_states = load_node_states(sid)
    node_table = get_node_table(node_states)
    skills_list = get_skills_list(graph)
    final_answer = get_final_answer(node_states)

    category = spec.get("category", "generic")
    if category == "parallel_fan_out":
        check = validate_parallel_fan_out(spec, node_table, skills_list)
    elif category == "critic_scenario":
        check = validate_critic_scenario(spec, skills_list, node_table)
    elif category == "coder_computation":
        check = validate_coder_computation(spec, skills_list, final_answer)
    elif category == "new_skill":
        check = validate_new_skill(spec, skills_list, final_answer)
    else:
        check = validate_generic(spec, skills_list, final_answer)

    failures = check.get("failures", [])
    status = "PASS" if not failures else "FAIL"

    return {
        "id": spec["id"],
        "category": category,
        "session_id": sid,
        "wall_clock_s": round(wall_clock, 2),
        "node_count": len(node_table),
        "skills_executed": skills_list,
        "node_table": node_table,
        "final_answer": final_answer[:400],
        "check_details": check,
        "status": status,
        "failures": failures,
    }


def print_report(spec: dict, r: dict) -> None:
    print(f"\n{'─' * 72}")
    print(f"  ID       : {r['id']}")
    print(f"  Category : {r.get('category', '?')}")
    print(f"  Session  : {r.get('session_id', '?')}")
    print(f"  Query    : {spec['query'][:80]}")
    print(f"  Notes    : {spec.get('validation_notes', '')}")
    print()

    node_table = r.get("node_table", [])
    if node_table:
        print(f"  {'NODE_ID':<8} {'SKILL':<22} {'STATUS':<10} {'ELAPSED':>8}  PROVIDER")
        print(f"  {'─'*7} {'─'*22} {'─'*10} {'─'*8}  {'─'*12}")
        for row in node_table:
            print(f"  {row['node_id']:<8} {row['skill']:<22} {row['status']:<10} "
                  f"{row['elapsed_s']:>7.2f}s  {row.get('provider', '')}")
    print()

    wc = r.get("wall_clock_s", 0)
    print(f"  Wall-clock  : {wc:.1f}s")

    cd = r.get("check_details", {})
    if "metrics" in cd:
        m = cd["metrics"]
        print(f"  Parallel    : found={m.get('found')}, expected≥{m.get('expected')}, "
              f"max_branch={m.get('max_branch_s', 0):.1f}s, "
              f"sum={m.get('sum_branches_s', 0):.1f}s, "
              f"speedup={m.get('speedup_ratio', 0):.2f}x")
    if "has_critic" in cd:
        print(f"  Critic node : {'yes' if cd['has_critic'] else 'no'}")

    fa = r.get("final_answer", "")
    if fa:
        print(f"  Answer      : {fa[:200]}")

    print(f"\n  STATUS: {r['status']}")
    for f in r.get("failures", []):
        print(f"    ✗ {f}")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run and report additional queries"
    )
    parser.add_argument("--id", dest="query_id",
                        help="Run a single query by its id")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print queries without running the agent")
    args = parser.parse_args()

    specs = json.loads(QUERIES_FILE.read_text())

    if args.query_id:
        specs = [s for s in specs if s["id"] == args.query_id]
        if not specs:
            print(f"No query with id '{args.query_id}'")
            sys.exit(1)

    if args.dry_run:
        print(f"\nAdditional queries ({len(specs)} total):\n")
        for spec in specs:
            print(f"  [{spec['category']}] {spec['id']}")
            print(f"    {spec['query'][:80]}")
        sys.exit(0)

    all_results = []
    for spec in specs:
        print(f"\n[RUN] {spec['id']}  ({spec['category']})")
        print(f"      {spec['query'][:80]}")

        try:
            sid, wall_clock, _output = run_query(spec["query"])
        except subprocess.TimeoutExpired:
            print("      TIMEOUT after 300s")
            all_results.append({"id": spec["id"], "status": "FAIL",
                                 "failures": ["process timed out"]})
            continue
        except Exception as e:
            print(f"      ERROR: {e}")
            all_results.append({"id": spec["id"], "status": "FAIL",
                                 "failures": [str(e)]})
            continue

        if sid is None:
            print("      WARNING: session id not found in agent output")
            all_results.append({"id": spec["id"], "status": "FAIL",
                                 "failures": ["session id not found in output"]})
            continue

        r = report_query(spec, sid, wall_clock)
        print_report(spec, r)
        all_results.append(r)

    # Summary
    print(f"\n{'═' * 72}")
    print(f"{'ID':<28} {'CATEGORY':<22} {'STATUS':<6}  FAILURES")
    print(f"{'─' * 72}")
    all_pass = True
    for r in all_results:
        status = r.get("status", "?")
        cat = r.get("category", "?")
        failures = "; ".join(r.get("failures", [])) or "ok"
        print(f"{r['id']:<28} {cat:<22} {status:<6}  {failures[:30]}")
        if status != "PASS":
            all_pass = False
    print(f"{'═' * 72}")

    # Write full results to disk
    RESULTS_FILE.write_text(
        json.dumps(all_results, indent=2, default=str)
    )
    print(f"\nFull results written to: {RESULTS_FILE.name}")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
