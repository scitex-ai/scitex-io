#!/usr/bin/env bash
# Whole source distribution and wheel, plus isolated actual-wheel imports.
set -euo pipefail
V="${1:-3.12}"
[ "$V" = 3.12 ]
PY="/opt/venv-$V/bin/python"
test -x "$PY"
: "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${RELEASE_TAG:?}" "${RELEASE_COMMIT:?}"
export LC_ALL=C.UTF-8 LANG=C.UTF-8
export PATH="/opt/venv-$V/bin:$PATH"
SCRATCH_PREFIX="/tmp/io-build-$V-"
source .github/ci/release-context.sh

driver_body() {
    [ ! -e dist ] && [ ! -L dist ] || { echo '::error::stale release output refused' >&2; exit 1; }
    "$PY" -m venv "$TMPDIR/build-venv"
    local build_python="$TMPDIR/build-venv/bin/python"
    uv pip install --python "$build_python" build hatchling 'scitex-dev>=0.62.7'
    "$build_python" -m build --no-isolation --outdir dist
    local wheels=(dist/*.whl)
    [ "${#wheels[@]}" -eq 1 ] && [ -f "${wheels[0]}" ]
    "$PY" -m venv "$TMPDIR/wheel-venv"
    local wheel_python="$TMPDIR/wheel-venv/bin/python"
    uv pip install --python "$wheel_python" "${wheels[0]}"
    "$wheel_python" -m pip check
    "$build_python" -I .github/ci/probe-first-observer.py -- \
        "$wheel_python" -I - "$TMPDIR/wheel-venv" <<'PY'
from pathlib import Path
import sys
import scitex_io
from scitex_io._save_modules._yaml import _save_yaml
from scitex_io._observers import register_post_save_hook
root=Path(sys.argv[1]).resolve()
assert Path(scitex_io.__file__).resolve().is_relative_to(root)
assert callable(_save_yaml) and callable(register_post_save_hook)
print('Actual isolated whole IO wheel imports passed')
PY
    "$PY" -I .github/ci/release-identity.py write-proof --tag "$RELEASE_TAG" --commit "$RELEASE_COMMIT"
}
run_owned_body
