#!/usr/bin/env bash
# run_tests.sh — run all (or selected) queries from Test Queries.json through agent7
#
# Usage:
#   ./run_tests.sh                  # run all queries
#   ./run_tests.sh --only A,B,F     # run only queries with id A, B, or F
#   ./run_tests.sh --no-clear       # skip all memory clears
#   ./run_tests.sh --only C --no-clear

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUERIES_FILE="$SCRIPT_DIR/Test Queries.json"
PYTHON="$SCRIPT_DIR/agent_core/.venv/bin/python3"
AGENT="$SCRIPT_DIR/agent_core/agent7.py"
STATE_DIR="$SCRIPT_DIR/agent_core/state"

# ── parse flags ──────────────────────────────────────────────────────────────
ONLY_IDS=""
NO_CLEAR=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --only)   ONLY_IDS="$2"; shift 2 ;;
        --no-clear) NO_CLEAR=1; shift ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

# ── helpers ──────────────────────────────────────────────────────────────────
clear_memory() {
    "$PYTHON" - <<'EOF'
import sys
sys.path.insert(0, "agent_core")
from memory import clear
clear()
EOF
    # also wipe artifacts
    rm -f "$STATE_DIR/artifacts/"*.bin "$STATE_DIR/artifacts/"*.json 2>/dev/null || true
    echo "  [memory cleared]"
}

# Queries whose run-2 must NOT clear memory (they depend on run-1 state)
depends_on_prior_run() {
    local id="$1" run="$2"
    [[ "$id" == "C" && "$run" == "2" ]] || [[ "$id" == "F" && "$run" == "2" ]]
}

# ── load queries via python ──────────────────────────────────────────────────
QUERY_LINES=()
while IFS= read -r _ql; do
    QUERY_LINES+=("$_ql")
done < <("$PYTHON" - "$QUERIES_FILE" "$ONLY_IDS" <<'EOF'
import json, sys
path = sys.argv[1]
only = set(x.strip().upper() for x in sys.argv[2].split(",")) if sys.argv[2] else set()
with open(path) as f:
    queries = json.load(f)
for q in queries:
    if only and q["id"].upper() not in only:
        continue
    # output tab-separated: id \t run \t expected_iterations \t query
    print(f'{q["id"]}\t{q["run"]}\t{q["expected_iterations"]}\t{q["query"]}')
EOF
)

if [[ ${#QUERY_LINES[@]} -eq 0 ]]; then
    echo "No queries matched. Check --only filter."
    exit 1
fi

# ── run loop ─────────────────────────────────────────────────────────────────
# bash 3.2 compatible results store (parallel arrays)
RESULT_KEYS=()
RESULT_VALS=()
PASS=0
FAIL=0

for line in "${QUERY_LINES[@]}"; do
    IFS=$'\t' read -r QID QRUN QITERS QTEXT <<< "$line"
    KEY="${QID}-run-${QRUN}"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Query ${KEY}   (expected ~${QITERS} iterations)"
    echo "  ${QTEXT}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # clear memory unless --no-clear or this run depends on prior run state
    if [[ $NO_CLEAR -eq 0 ]] && ! depends_on_prior_run "$QID" "$QRUN"; then
        clear_memory
    fi

    # run the agent; stream output live
    set +e
    "$PYTHON" "$AGENT" "$QTEXT"
    EXIT_CODE=$?
    set -e

    if [[ $EXIT_CODE -eq 0 ]]; then
        RESULT_KEYS+=("$KEY")
        RESULT_VALS+=("PASS")
        ((PASS++)) || true
    else
        RESULT_KEYS+=("$KEY")
        RESULT_VALS+=("FAIL (exit $EXIT_CODE)")
        ((FAIL++)) || true
    fi
done

# ── summary ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
_ri=0
while [[ $_ri -lt ${#RESULT_KEYS[@]} ]]; do
    printf "  %-15s %s\n" "${RESULT_KEYS[$_ri]}" "${RESULT_VALS[$_ri]}"
    ((_ri++)) || true
done | sort
echo ""
printf "  Total: %d passed, %d failed\n" "$PASS" "$FAIL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[[ $FAIL -eq 0 ]]
