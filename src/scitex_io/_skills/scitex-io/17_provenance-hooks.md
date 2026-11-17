---
description: |
  [TOPIC] Provenance hooks
  [DETAILS] Post-save / post-load observer hooks (what scitex-clew and
  @stx.session use to record input -> executable -> output triplets),
  which files fire them, the payload, and how provenance loss is made
  loud: observer_failures(), provenance_scope(), and
  SCITEX_IO_STRICT_PROVENANCE=1.
tags: [scitex-io-provenance-hooks, scitex-io-provenance, scitex-io-hooks, scitex-io, scitex-package]
---

# Provenance hooks

`stx.io.save` / `stx.io.load` notify registered observers (scitex-clew
registers itself through the `scitex_io.observers` entry point). This is
how a `@stx.session` run records its inputs and outputs without any
explicit call. If that notification breaks silently, the run's provenance
is silently incomplete, so scitex-io makes every loss visible.

## What fires

| Operation | Hook calls |
|---|---|
| `save(obj, "x.csv")` | one call for `x.csv` |
| `save(fig, "fig.png")` | one call for `fig.png` **and one per sidecar** (`fig.csv`, `fig_for_sigmaplot.csv`, `fig_<ax>_legend.png`, figrecipe `fig.yaml` + data files) |
| `save(..., symlink_from_cwd=True / symlink_to=...)` | no extra call; the link is listed in the target's payload `symlinks` |
| `save_text(text, "/abs/REPORT.md")` / `save_text(text, "./REPORT.md")` and every other public `save_*` helper (`save_image`, `save_mp4`, `save_listed_dfs_as_csv`, `save_listed_scalars_as_csv`, `scitex_io._save_modules.save_<fmt>`) | one call per written file, exactly like `save()` |
| `load("x.csv")` / `load("./link.csv")` | one call, `path` = the realpath of the target |
| `load("data/*.csv")` | one call **per matched file**, never for the pattern |

**Every write through scitex-io's public API is observed**, whatever the
path form: `path` is always the realpath, for relative and absolute
destinations alike. The `save_*` helpers keep their own path semantics
(relative = relative to the current working directory, NOT caller-anchored
like `save()`), and accept `track=` / `derived_from=` like `save()`.
`save_optuna_study_as_csv_and_pngs` writes through `save()` and fires per
file. STX-PA001 still discourages absolute paths (portability), but
capture does not depend on following that lint. Writes that bypass
scitex-io entirely (`open(...).write`, `df.to_csv`) are NOT observed —
that is what the STX-IO raw-IO lint rules flag.

Sidecars are detected two ways: scitex-io's own writers note the files
they write, and the primary's directory is compared before and after the
save for entries that share the primary's stem (`<stem>`, `<stem>.*`,
`<stem>_*`, `<stem>-*`). A nested `save()` inside a saver reports its own
files once.

## Hook signatures and payload

```python
import scitex_io as sio

def on_save(path, obj, kwargs):      # path = realpath (hash this)
    prov = kwargs["provenance"]
    # {"role": "primary" | "sidecar", "realpath": str, "requested": str,
    #  "primary": str, "symlinks": [str, ...], "in_scope": bool, "scope": str | None}
    # Sidecar calls get obj=None. kwargs["track"] is the save's track= flag.
    # kwargs["derived_from"] (only when the caller declared it): list of
    # realpaths this output was computed from -- same list on every sidecar.

def on_load(path, result, info=None):  # a 3rd parameter is optional
    # info = {"requested", "realpath", "symlink", "glob", "in_scope", "scope"}
    ...

sio.register_post_save_hook(on_save)
sio.register_post_load_hook(on_load)  # 2-arg hooks still work
```

## Declaring which inputs an output used (`derived_from`)

A run-level observer only knows "this output came from a run that read
these files". When you know an output used only some of them, say so:

```python
df_used = sio.load("used.csv")
df_other = sio.load("unused.csv")          # read, but not used below
sio.save(summary(df_used), "result.json",
         derived_from=[df_used])           # or ["used.csv"]
```

scitex-clew stores this per output, and `clew.slice(target, level=2)`
then drops `unused.csv` from `result.json`'s back-trace (level 1 keeps it).

* Items are file paths or objects **returned by `load()`**. An object is
  resolved to its source file through an identity registry (weak
  reference keyed by `id`), so a recycled `id` never resolves to a stale
  path. `dict` / `list` / `str` / `int` cannot be weakly referenced and are
  never resolved: pass their path.
* Anything unresolvable (unknown object, missing file, object loaded from
  two files) raises **before** the file is written.
* Nothing is inferred. Without `derived_from` the payload carries no
  declaration and the observer keeps every input of the run. In
  particular, re-saving a loaded object is NOT taken to mean "derived from
  its source": `df = load(a); df["y"] = load(b)["y"]; save(df, out)` would
  then silently lose `b`. If you merged other data into a loaded object in
  place, list those files too.

## Loss is loud, never debug-only

Whenever a hook raises, the file a save claims to have written is missing,
or the sidecar scan fails, scitex-io:

1. **counts** the event (per process, and per active scope),
2. logs a **WARNING** the first time it sees each `(kind, hook, exception
   type)`, with the traceback (repeats are counted and logged at DEBUG),
3. in strict mode, **raises** `scitex_io.ProvenanceError` instead.

```python
report = sio.observer_failures()
# {"total": 0, "by_kind": {}, "events": [], "unscoped_saves": 0,
#  "unscoped_loads": 0, "scope": None, "strict": False}
```

Kinds: `post_save`, `post_load`, `missing_output`, `sidecar_scan`. Each
entry in `events` has `kind`, `hook`, `error_type`, `error`,
`first_path`, `count`. Write this dict into run metadata: a run whose
provenance is incomplete has to say so. `sio.reset_observer_failures()`
zeroes the tally.

## Scopes (session / run windows)

```python
with sio.provenance_scope("2026Y-11M-16D-run") as scope:
    sio.save(df, "/abs/out.csv")
scope.failures()        # same shape, only this scope's failures
```

Inside a scope, hook payloads carry `in_scope=True, scope=<name>`. I/O
that observers see outside any scope is counted in `unscoped_saves` /
`unscoped_loads`, logged once at INFO, and flagged with `in_scope=False`
in the payload, so an observer can tell a save outside any session from a
recorded one.

## Strict mode

```bash
SCITEX_IO_STRICT_PROVENANCE=1 python my_script.py
```

Any provenance loss raises `ProvenanceError` (a `RuntimeError`) at the
failing `save` / `load`. The data file is already written when this
happens; only the record of it failed. Use strict mode in CI and in
reproducibility runs for a paper.
