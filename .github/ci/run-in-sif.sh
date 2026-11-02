#!/usr/bin/env bash
# Complete IO all/dev suite in one fresh owned environment inside the SIF.
set -euo pipefail
V="${1:?Python version required}"
[[ "$V" =~ ^3\.(11|12|13)$ ]]
PY="/opt/venv-$V/bin/python"
test -x "$PY"
: "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${RELEASE_TAG:?}" "${RELEASE_COMMIT:?}"
[[ "$GITHUB_RUN_ID" =~ ^[0-9]+$ && "$GITHUB_RUN_ATTEMPT" =~ ^[0-9]+$ ]]
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
    export PATH="$TMPDIR/venv/bin:$PATH" RUN_E2E=1
    "$test_python" -c 'import matplotlib; matplotlib.use("Agg"); from matplotlib import font_manager; font_manager.fontManager'
    local workers
    workers="$(nproc)"
    [ "$workers" -le 32 ] || workers=32
    nice -n 19 ionice -c 3 "$test_python" -m pytest tests/ -n "$workers" --dist load -q \
        --cov=src/scitex_io --cov-report=xml --cov-report=term -p no:cacheprovider
}
run_owned_body
