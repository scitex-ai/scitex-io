---
description: |
  [TOPIC] Environment variables
  [DETAILS] Env vars read by scitex-io at import/runtime: the user-facing
  SCITEX_IO_STRICT_PROVENANCE / SCITEX_IO_QUIET_NOTEBOOK_WARN knobs plus
  optional-dependency presence flags (SCITEX_*_AVAILABLE).
tags: [scitex-io-env-vars, scitex-io, scitex-package]
---

# scitex-io — Environment Variables

## User-facing knobs

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_IO_STRICT_PROVENANCE` | `1`/`true`/`yes`/`on`: any provenance loss (raising observer hook, missing output, failed sidecar scan) raises `scitex_io.ProvenanceError` instead of a one-time WARNING. See [17_provenance-hooks](17_provenance-hooks.md). | unset (warn + count) | bool |
| `SCITEX_IO_QUIET_NOTEBOOK_WARN` | Silence the once-per-process hint when a notebook path cannot be detected. | unset | bool (presence) |

## Internal flags

The remaining `SCITEX_*` strings are optional-dependency probes (feature flags
set implicitly by whether a sibling package imports cleanly) and completion
markers, not config knobs.

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_ERRORS_AVAILABLE` | Presence flag: set when `scitex_errors` importable; gates rich error types. | unset | bool (presence) |
| `SCITEX_LOGGING_AVAILABLE` | Presence flag: set when `scitex_logging` importable; gates logger attach. | unset | bool (presence) |
| `SCITEX_IO_COMPLETE` | Internal sentinel for standalone-vs-umbrella detection. | unset | bool (presence) |
| `SCITEX_ONLY` | Cross-package sentinel used by downstream loaders; scitex-io only reads it. | unset | bool (presence) |

## Notes

- Only the user-facing knobs above are meant to be set by end users.
- Add any future user-facing knobs under the `SCITEX_IO_*` prefix per ecosystem convention.

## Audit

```bash
grep -rhoE 'SCITEX_[A-Z0-9_]+' $HOME/proj/scitex-io/src/ | sort -u
```
