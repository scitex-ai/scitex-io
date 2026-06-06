# Changelog

All notable changes to `scitex-io` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.1] — 2026-06-07

### Changed
- **`mne` is no longer a core dependency.** Bare `pip install
  scitex-io` no longer pulls mne + sklearn + pooch + decorator (~150MB
  install footprint) just because two niche loaders
  (`_load_modules/_con.py`, `_load_modules/_eeg.py`) use it. Install
  with `pip install 'scitex-io[mne]'` to opt back in. The loaders
  already imported optionally; this PR makes the dep optional at the
  packaging layer too. Companion fix: `_load_eeg_data` now raises a
  clear `ImportError` naming the `[mne]` extra when called without mne
  installed and without a `mne_module=` injection (previously
  AttributeError'd on the first `mne_module.io.*` call).

  Motivation: same SIF-dogfood signal as scitex-gen v0.1.13
  (proj-paper-ripple-wm, 2026-06-07). Bare ecosystem installs in slim
  research containers shouldn't drag heavy optional chains in for
  niche loaders.

- **Publish workflow gates on STRUCTURAL checks only.** The
  `pypi-publish-and-github-release-on-tag` workflow's pre-publish
  `pytest tests/ -x` step has been dropped. It duplicated the PR
  matrix and fast-failed on the known-tolerated
  `tests/develop/test_audit.py::test_audit_all_clean` F that every
  scitex-* repo carries as accepted drift under the
  {CLEAN, UNSTABLE} merge framework. The `test` job is now a
  matrix install-smoke (pip install -e .[all,dev]) — that's the
  structural correctness gate the publish pipeline owes the user.
  Functional coverage continues to run on every PR via the matrix
  workflow. Same fix as scitex-gen PR #23.

- **`[all]` and `[dev]` extras now list deps literally** (no
  `scitex-io[mcp]`-style self-references, which fail to resolve
  during `pip install -e` because the package isn't on PyPI at
  install time). `[dev]` ⊇ `[all]` by enumeration — the suite covers
  every optional code path. Invariant captured inline as a comment.

- **`faulthandler_timeout = 120` in pytest config.** Pytest dumps
  every thread's stack on a 120s deadlock — so CI logs name the
  exact wedged test instead of leaving us reading the runner clock.
  Same hygiene as scitex-gen v0.1.13. Cost: zero on green runs.

## [0.3.0] — 2026-06-07

Minor bump motivated by two intentional behaviour breaks, both
no-silent-failure antipattern removals. Both surfaces are also the
documented release reason — the changes were lead-mandated and
called out in commit messages before the version bump.

### Removed
- **Silent-fallback `.db` loader stub (#59).** Deleted
  `src/scitex_io/_load_modules/_sqlite3.py` — the 8-line primitive
  `SQLite3` class that wrapped a raw `sqlite3.Connection` and
  shadowed `scitex_db`'s full SQLite3 wrapper. Calling
  `stx.io.load("foo.db")` used to return that raw Connection wrapped
  in the stub; user code lost access to `get_rows` / `load_array` /
  `save_array` and silently bypassed scitex-db's compression / array
  / blob / transaction layer. Replaced by the existing
  optional-provider mechanism (`_optional_providers.py`,
  `_register_scitex_db()` via
  `scitex_dev.try_import_optional("scitex_db", extra="db",
  pkg="scitex-io")`).
  - When **scitex-db is installed**: `stx.io.load("foo.db")`
    delegates to `scitex_db.SQLite3(path, **kwargs)`; kwargs flow
    through to support `mode='ro'` / `timeout=` (companion
    `scitex-db v0.1.12`).
  - When **scitex-db is absent**: registration silently no-ops and
    `stx.io.load("foo.db")` fails through the standard registry
    error path: `ValueError("No load handler registered for
    '.db'. Use register_loader('.db', your_fn) to add one.")`.
    Install `scitex-io[db]` to get the scitex-db dispatch.
  - **Breaking** for any caller relying on the silent stub return
    value. Umbrella consumers are not affected (the `scitex`
    umbrella core-pins `scitex-db>=0.1.11` already, so the dispatch
    is always active there).
- **Silent-empty `load_configs` fallback on processing errors
  (#65).** Removed the outer `try/except Exception: print(...);
  return DotDict({})` from
  `src/scitex_io/_loading/_load_configs.py`. The swallow turned
  every YAML processing bug — malformed YAML, an int-keyed mapping
  crashing the debug-promotion walker, a missing required file
  under `categories/` — into a silent empty `DotDict({})` and a
  cryptic downstream `'DotDict' object has no attribute 'X'` three
  frames away from the actual failure.

### Changed
- **`load_configs` raises `ConfigLoadError` on processing errors
  (#65).** New `scitex_io._loading._load_configs.ConfigLoadError`
  exception class. Each error names the offending YAML file in the
  message and chains the original exception as `__cause__`. The
  `IS_DEBUG.yaml` read is wrapped the same way so a malformed flag
  file surfaces with its path in the error. Case-collision
  `ValueError` from `_normalize_to_upper` keeps propagating as
  before — no behaviour change for that path. **Breaking** for any
  caller depending on the silent-empty return value (the
  documented antipattern being removed); the typical consumer
  pattern of `CONFIG = load_configs(); CONFIG.MODEL.HIDDEN_DIM` is
  unchanged on the happy path.

### Fixed
- **`apply_debug_values` no longer crashes on non-string YAML keys
  (#64).** YAML mapping keys can be non-string — neurovista's
  `SEIZURE.yaml` carries literal integer event-code tables
  (`INT2STR: {-1: interictal, 1: seizure, 2: sle}`). When
  `load_configs` ran with `IS_DEBUG=True` (any of: explicit kwarg,
  `CI=True`, or `IS_DEBUG.yaml` with `IS_DEBUG: true`), the inner
  `apply_debug_values` walker raised
  `AttributeError: 'int' object has no attribute 'startswith'` on
  the first int key. Now guards with `isinstance(key, str)` before
  `key.startswith(("DEBUG_", "debug_"))` — the `DEBUG_<KEY>` rule
  only applies to string keys by definition. Combined with the
  `load_configs` fail-loud rewrite above, every config bug now
  surfaces at load time with the offending file + root exception
  in the traceback instead of as a downstream `AttributeError`.

## [0.2.21] — 2026-06-04

### Fixed
- **`scitex_io.save(symlink_from_cwd=True)` no longer self-loops on repeat invocation (#55, #56).** Two consecutive `save(obj, "./x.csv", symlink_from_cwd=True)` calls from the same cwd produced a `./x.csv -> x.csv` self-loop symlink, and a third call then tripped `OSError [Errno 40]` inside `clean()`. Root cause was twofold: (a) `spath_cwd = clean(spath_cwd)` called `Path.resolve()`, which on call 2 silently followed call 1's symlink and rebound the cwd anchor onto the routed target file — so the next rm deleted the just-written artefact; (b) `_symlink()` received the un-normalised `spath` (containing `./` from `os.path.join(sdir, "./x.csv")`), and `ln -sfr` collapsed the relative target to the symlink's own basename, producing the self-loop. Fix: switch `spath_cwd` to `os.path.normpath` (anchor stays at the literal cwd location), pre-emptively `unlink` any pre-existing broken/self-loop symlink, and pass `spath_final` (cleaned) into `_symlink()` with a defence-in-depth self-loop guard. Regression test pins double-save + third-save round-trip and stale-self-loop cleanup.

## [0.2.20] — 2026-06-01

### Changed
- **`scitex_io.save()` fails LOUD now (#51).** The outer `try/except` previously caught every exception, logged it as `ERRO`, and returned `False`. Callers doing `path = sio.save(obj, p)` proceeded as if the save had succeeded, and the failure surfaced much later — typically as a `FileNotFoundError` in a downstream consumer. The exception now re-raises at the call site; the log still carries the `spath` / `specified_path` debug trail for forensics. **Breaking** for any caller relying on the `False`-on-error sentinel; an internal audit found only test-suite users of the sentinel, which were updated in the same PR.

### Fixed
- **Per-extension lazy registry — JSON save no longer imports PIL / pymupdf / pdfminer / pdfplumber / pyarrow / h5py / plotly / scipy (#52).** `_builtin_handlers.py` used to eagerly `from ._save_modules import save_X` for every saver at first `import scitex_io`, and `_load_modules/__init__.py` scanned its own directory and `importlib.import_module()`-ed every `.py` in it. A JSON-only `stx.io.save({"a":1}, "/tmp/x.json")` consequently pulled in ~200 heavy modules, several of which transitively link `libgthread-2.0.so.0` and fail on minimal containers (paper-scitex-clew WSL2 incident, 2026-06-01). Switched to a per-extension lazy `(module_path, attr_name)` registry that resolves+memoises on first `get_saver()`/`get_loader()` lookup. Verification: `import scitex_io as sio; sio.save({"a":1}, "/tmp/x.json")` followed by `sys.modules` filter for `PIL|pymupdf|pdfminer|pdfplumber|pyarrow|h5py|plotly|scipy` returns **0 entries** (before: ~200).

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
