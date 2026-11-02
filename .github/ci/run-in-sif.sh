#!/usr/bin/env bash
# Complete IO all/dev suite in one fresh owned environment inside the SIF.
set -euo pipefail
V="${1:?Python version required}"
[[ "$V" =~ ^3\.(11|12|13)$ ]]
PY="/opt/venv-$V/bin/python"
test -x "$PY"
: "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${RELEASE_TAG:?}" "${RELEASE_COMMIT:?}"
[[ "$GITHUB_RUN_ID" =~ ^[0-9]+$ && "$GITHUB_RUN_ATTEMPT" =~ ^[0-9]+$ ]]
: "${CI_XDIST_WORKERS:?registered IO worker budget required}"
[[ "$CI_XDIST_WORKERS" =~ ^[1-4]$ ]]
export LC_ALL=C.UTF-8 LANG=C.UTF-8
export PATH="/opt/venv-$V/bin:$PATH"
SCRATCH_PREFIX="/tmp/io-test-$V-"
source .github/ci/release-context.sh

driver_body() {
    "$PY" -m venv "$TMPDIR/venv"
    local test_python="$TMPDIR/venv/bin/python"
    # Exactly one normal all/dev resolution. No core-only fallback or deps bypass.
    uv pip install --python "$test_python" -e '.[all,dev]'
    "$test_python" -m pip check
    "$test_python" -I .github/ci/probe-first-observer.py
    export PATH="$TMPDIR/venv/bin:$PATH" RUN_E2E=1 COVERAGE_FILE="$TMPDIR/.coverage"
    "$test_python" -c 'import matplotlib; matplotlib.use("Agg"); from matplotlib import font_manager; font_manager.fontManager'
    local workers
    workers="$("$test_python" - "$CI_XDIST_WORKERS" <<'WORKERS'
import math
import os
from pathlib import Path
import sys
budget = int(sys.argv[1])
limits = [budget, os.cpu_count() or 1]
if hasattr(os, "sched_getaffinity"):
    limits.append(len(os.sched_getaffinity(0)))
try:
    quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
    if quota != "max":
        limits.append(max(1, math.floor(int(quota) / int(period))))
except (FileNotFoundError, PermissionError, ValueError, ZeroDivisionError):
    pass
for controller in ("cpu", "cpu,cpuacct"):
    try:
        base = Path("/sys/fs/cgroup") / controller
        quota = int((base / "cpu.cfs_quota_us").read_text())
        period = int((base / "cpu.cfs_period_us").read_text())
        if quota > 0:
            limits.append(max(1, math.floor(quota / period)))
    except (FileNotFoundError, PermissionError, ValueError, ZeroDivisionError):
        pass
print(max(1, min(limits)))
WORKERS
    )"
    echo "IO reviewed worker budget=$CI_XDIST_WORKERS effective_workers=$workers (shared host, no exclusive CPU claim)"
    nice -n 19 ionice -c 3 "$test_python" -m pytest tests/ -n "$workers" --dist load -q \
        --cov=src/scitex_io --cov-report="xml:$TMPDIR/coverage.xml" --cov-report=term -p no:cacheprovider
}
run_owned_body
