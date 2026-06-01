# Changelog

All notable changes to `scitex-io` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.20]

- fix(sqlite3): `stx.io.load("*.db")` now soft-imports `scitex_db.SQLite3`
  when available, restoring the rich SQLite API (`get_rows`,
  `load_arrays`, `insert_many`, …) at the `stx.io.load(*.db)` entry
  point. Falls back to the previous minimal `sqlite3.Connection`
  context-manager wrapper when `scitex-db` is not installed, so
  `scitex-io` keeps working in environments that don't need the rich
  API. No hard dependency on `scitex-db` is added — the import is
  guarded.
  - Unblocks downstream code that calls `db_.get_rows(...)` /
    `db_.load_arrays(...)` inside a `with stx.io.load(path) as db_:`
    block (e.g. `neurovista/scripts/io/load_pac.py`), which
    previously raised
    `AttributeError: 'sqlite3.Connection' object has no attribute 'get_rows'`
    against scitex-io ≥ 0.2.x.
  - Added structural tests for both code paths (rich + fallback) and
    a runtime smoke that round-trips a tiny in-memory SQLite DB.

## [0.2.17]

- perf: accessing `register_post_save_hook`/`register_post_load_hook` no longer eager-registers the built-in format handlers (catboost/zarr/pandas/…). The observer hook registry is registry-independent, so `__getattr__` now skips `_ensure_builtin_handlers_registered()` for `._observers` attrs. Cuts the hot path for observer packages (e.g. scitex-clew registers hooks at import): `import scitex_clew` dropped ~3700ms → ~100ms.

## [0.2.16]

- feat(bundle): host the `scitex_io.bundle` subpackage incl. scitex-stats bundle integration (SOC R5 / Task 8) — makes `scitex_io.bundle` available on PyPI (previously only on develop), unblocking the umbrella to pin `scitex-io==0.2.16` instead of a git+https dev ref.
- feat(hooks): neutral post-save / post-load hook registry (`register_post_save_hook` / `register_post_load_hook`) for observer packages (SOC R6); scitex-clew self-registers.

## [0.2.15] — 2026-05-23

### Added
- **Case-insensitive `DotDict` lookup** (#32, #33). `load_configs()`
  results and any `DotDict` now resolve string keys case-insensitively
  via `key.upper()` (e.g. `CONFIG.path` matches a `PATH` key), and
  raise loudly on case collisions so ambiguous configs fail fast
  instead of silently picking one.

### Fixed
- **Test suite green on Python 3.11–3.13.** Restored two `DotDict`
  tests whose mutating operation (`setdefault` / `pop`) had been
  dropped during an earlier test-quality refactor, and added a
  registry-isolation fixture so a leaked custom `.json` saver no
  longer fails a sibling test. `catboost_info/` (a regenerated ML
  test artifact) is now gitignored.

## [0.2.14] — 2026-05-07

### Fixed
- **Top-level `scitex_io._load_cache` shim restored.** The published
  umbrella `scitex.io._load` imports
  `from scitex_io._load_cache import cache_data, get_cached_data,
  load_npy_cached`. After standalonization the implementation moved
  to `scitex_io._loading._load_cache`, breaking every umbrella
  consumer's CI on Python 3.12/3.13 (clean sites that pull from
  PyPI). The shim re-exports the three names from the new path.

## [0.2.13] — 2026-05-07

### Fixed
- **`logger.success()` now works under stdlib Python on every
  supported version.** Previously `_save.py` used
  `logger = logging.getLogger()` (stdlib), which has no `.success()`
  method — every save raised
  `AttributeError: 'RootLogger' object has no attribute 'success'`
  on a clean Python 3.10 install. Switched to
  `from scitex_logging import getLogger` so the SciTeX-extended
  logger (with `.success()`, `.fail()`) is used instead.
- **`color_text(..., c="yellow")` → `color_text(..., "yellow")`**
  in the dry-run success message. The kwarg was named `color`,
  not `c`; the call was raising `TypeError: missing 1 required
  positional argument: 'color'` on every dry-run save.

## [0.2.12] — 2026-05-07

### Fixed
- **Notebook save routing** (`scitex_io.save` from inside a `.ipynb`)
  now lands at the canonical `<notebook_dir>/<stem>_out/<file>`
  instead of the legacy `<cwd>/name/path_out/<file>` shape.
  Root cause: `get_notebook_info_simple()` was a stub returning a
  dict `{"path": None, "name": None}`, but the caller in `_save.py`
  unpacked it as a 2-tuple — iterating dict keys produced
  `notebook_name="path"`, `notebook_dir="name"`. Fixed by
  implementing real notebook-name detection (env-var override,
  VS Code `__vsc_ipynb_file__`, `ipynbname`, `sys.argv` scan) and
  hardening the caller to verify the 2-tuple shape.
- **Symlink helpers** (`symlink_from_cwd=True`, `symlink_to=...`)
  now actually create the symlink. Two bugs fixed:
  - `sh(["ln", "-sfr", src, dst])` was running with `shell=True`,
    which on POSIX uses only the first list element as the command
    and silently discards the rest. Switched to `shell=False`.
  - `_symlink_from_cwd` success message used `color_text("...")`
    without the required `color` arg — that raised mid-routine and
    surfaced as a "missing 1 required positional argument" error
    on every save with `symlink_from_cwd=True`.

### Added
- **`SCITEX_NOTEBOOK_PATH` env var** — explicit notebook path for
  contexts where automatic detection fails (CI, `jupyter nbconvert`,
  custom kernels). Example:
  `SCITEX_NOTEBOOK_PATH=demo.ipynb jupyter nbconvert --execute --inplace demo.ipynb`.
- **`SCITEX_IO_QUIET_NOTEBOOK_WARN` env var** — silences the
  one-time hint that fires when notebook detection falls back to
  `<cwd>/notebook_out/`.
- **20 new unit tests** in `tests/scitex_io/test__save_routing.py`
  covering: 2-tuple return contract, env-var override, env-var
  fall-through, sys.argv detection, abs-path bypass, jupyter
  routing with/without detection, fallback warning, once-per-
  process latch, env-var silencer, symlink creation,
  `symlink_to` custom path, `symlink_from_cwd` round-trip,
  `dry_run`, `makedirs=False`, defensive guard against the legacy
  `name/path_out/` shape.

### Documentation
- **Path-resolution skill leaf** (`_skills/scitex-io/16_path-resolution.md`)
  expanded with a "Jupyter notebook routing" section: detection
  layers, env-var override, fallback behavior, recommended
  in-cell pattern (absolute path or `Path.cwd()` anchor).

## [0.2.11]

- Initial CHANGELOG entry — see git log for prior history.
