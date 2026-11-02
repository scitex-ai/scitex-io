#!/usr/bin/env bash
# Native release execution uses only the reviewed whole image and runtime.
set -euo pipefail
INNER="${1:?fixed inner release driver required}"
shift
case "$INNER" in run-in-sif.sh|build-in-sif.sh) ;; *) echo '::error::unregistered release driver' >&2; exit 1;; esac
V="${1:?Python version required}"
[[ "$V" =~ ^3\.(11|12|13)$ ]] && [ "$#" -eq 1 ]
: "${SCITEX_CI_SIF:?}" "${SCITEX_CI_SIF_SHA256:?}" "${SCITEX_CI_APPTAINER:?}" "${SCITEX_CI_APPTAINER_SHA256:?}"
[[ "$SCITEX_CI_SIF_SHA256" =~ ^[a-f0-9]{64}$ && "$SCITEX_CI_APPTAINER_SHA256" =~ ^[a-f0-9]{64}$ ]]
SIF="$(realpath -- "$SCITEX_CI_SIF")"
RUNTIME="$(realpath -- "$SCITEX_CI_APPTAINER")"
[ -f "$SIF" ] && [ -x "$RUNTIME" ]
[ "$(basename -- "$SIF")" = "ci-cpu-sha256-$SCITEX_CI_SIF_SHA256.sif" ]
VALUE="$(sha256sum -- "$SIF")"
[ "${VALUE%% *}" = "$SCITEX_CI_SIF_SHA256" ]
VALUE="$(sha256sum -- "$RUNTIME")"
[ "${VALUE%% *}" = "$SCITEX_CI_APPTAINER_SHA256" ]
# No host profile, auth key, or active-project environment enters the tests.
for name in GITHUB_RUN_ID GITHUB_RUN_ATTEMPT RELEASE_TAG RELEASE_COMMIT; do
    [ -n "${!name:-}" ] || { echo "::error::missing release context $name" >&2; exit 1; }
done
# The admitted runner owns this root. Bind only our exclusive child as /tmp,
# keeping large normal all/dev environments off the shared host root disk.
: "${RUNNER_TEMP:?owned runner temporary parent required}"
IO_CONTEXT_PARENT="$(realpath -- "$RUNNER_TEMP")"
[ -d "$IO_CONTEXT_PARENT" ] && [ ! -L "$IO_CONTEXT_PARENT" ]
SCRATCH_PREFIX="$IO_CONTEXT_PARENT/io-native-$V-"
source .github/ci/release-context.sh

driver_body() {
    mkdir "$TMPDIR/apptainer"
    export APPTAINER_TMPDIR="$TMPDIR/apptainer"
    "$RUNTIME" exec --cleanenv --pwd "$PWD" --bind "$PWD:$PWD" --bind "$TMPDIR:/tmp" \
        --env "GITHUB_RUN_ID=$GITHUB_RUN_ID" --env "GITHUB_RUN_ATTEMPT=$GITHUB_RUN_ATTEMPT" \
        --env "RELEASE_TAG=$RELEASE_TAG" --env "RELEASE_COMMIT=$RELEASE_COMMIT" \
        "$SIF" bash ".github/ci/$INNER" "$V"
}
run_owned_body
