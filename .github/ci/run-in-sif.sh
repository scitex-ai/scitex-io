#!/usr/bin/env bash
# Runs INSIDE the reused CI SIF (apptainer exec). $1 = python version.
#
# The SIF (~/.scitex/dev/containers/ci-cpu.sif, on punim0264) bakes the curated
# ecosystem dependency union — the scientific core (numpy/scipy/pandas/
# matplotlib/torch/…), the scitex basics (io/logging/config/dict/decorators/
# gen/nn/stats/str/dsp), scitex-dev[all,dev], figrecipe, and the pytest
# toolchain — FULLY installed in a per-version venv at /opt/venv-$V. It is
# READ-ONLY, so CI runs the CHECKOUT's code by prepending it on PYTHONPATH:
# that shadows any baked copy for imports + coverage, while the baked installs
# still supply the importlib.metadata surface (entry points, __version__) that
# a bare PYTHONPATH cannot.
#
# No install, no --writable-tmpfs: nothing is written into the SIF (the baked
# venv is root-owned — a runtime install hits Permission denied even on a
# tmpfs overlay).
#
# Fail-loud: a SIF without the baked venv is a hard error (rebuild the SIF) —
# never a per-run install fallback. A dep this package imports that is missing
# from the SIF is ALSO a hard error: bake it into the SIF (top up ci-cpu.def),
# never `pip install` it here.
set -euo pipefail

V="${1:?python version arg required (3.11/3.12/3.13)}"
VENV="/opt/venv-$V"
test -x "$VENV/bin/python" || {
    echo "::error::baked venv python missing in $VENV — rebuild: scitex-container apptainer build ci-cpu"
    exit 1
}
test -x "$VENV/bin/pytest" || {
    echo "::error::baked pytest missing in $VENV — rebuild: scitex-container apptainer build ci-cpu"
    exit 1
}

export LC_ALL=C.UTF-8 LANG=C.UTF-8

# Real writable scratch. The runner profile exports TMPDIR to a host path that
# does NOT resolve inside the container; tests (tmp_path) and mktemp need a
# working tmp. Node-local /tmp is writable + ephemeral.
export TMPDIR="/tmp/ci-$V"
mkdir -p "$TMPDIR"

# A VIRTUAL_ENV leaked from the runner profile is a broken symlink in here;
# unset it so no tool (uv, pip) tries to follow it.
unset VIRTUAL_ENV || true

# venv bin on PATH (python3, pytest, baked console scripts); PYTHONPATH
# prepends the checkout so imports + coverage use the PR code.
export PATH="$VENV/bin:$PATH"
export PYTHONPATH="$PWD/src"

echo "py=$("$VENV"/bin/python -V) pytest=$(command -v pytest)"
exec pytest tests/ --cov=src/scitex_io --cov-report=xml --cov-report=term
