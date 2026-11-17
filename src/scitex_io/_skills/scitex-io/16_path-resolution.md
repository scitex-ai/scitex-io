---
description: |
  [TOPIC] Path resolution
  [DETAILS] Auto save-path routing in scitex-io and scitex.path
  utilities for path splitting, finding, versioning, and symlinks.
tags: [scitex-io-path-resolution, scitex-io, scitex-package]
---

# Path Resolution

## Auto save-path routing (scitex-io)

`sio.save(obj, "relative/path.csv")` auto-routes the actual write
location based on caller context:

| Context | Output directory |
|---------|-----------------|
| Script | `{script_name}_out/{path}` (e.g. `analysis_out/results.csv`) |
| `@stx.session` | `{script_name}_out/FINISHED_{status}/{session_id}/{path}` |
| Jupyter (`*.ipynb`) | `{notebook_dir}/{notebook_base}_out/{path}` (see "Jupyter notebook routing" below) |
| Interactive REPL | `$SCITEX_DIR/io/runtime/cache/{path}` (default `~/.scitex/io/runtime/cache/`) |
| Absolute path | Used as-is, no routing |

### The round-trip gotcha (important for new users + agents)

```python
sio.save(df, "results.csv")    # writes to analysis_out/results.csv
df = sio.load("results.csv")   # ❌ FileNotFoundError — looks in cwd
```

`save()` routes by caller context; `load()` resolves relative paths
against **the current working directory**. Three idiomatic fixes:

1. **Drop a symlink at cwd** — one-flag round trip by filename:

   ```python
   sio.save(df, "results.csv", symlink_from_cwd=True)
   df = sio.load("results.csv")   # ✓ works via the cwd symlink
   ```

2. **Use the absolute path** returned by save's provenance (or
   `stx.path.mk_spath`):

   ```python
   spath = stx.path.mk_spath("results.csv")  # analysis_out/results.csv
   sio.save(df, spath)
   df = sio.load(spath)            # ✓ absolute on both sides
   ```

3. **Stay within `@stx.session`** — every output lives under
   `FINISHED_SUCCESS/{session_id}/`, so scripts produce a clean,
   timestamped, hash-tracked directory by design. The session decorator
   injects a `CONFIG` with paths already resolved:

   - `CONFIG.SDIR_OUT` — base output dir (e.g., `analysis_out/`)
   - `CONFIG.SDIR_RUN` — this run's dir (e.g., `analysis_out/FINISHED_SUCCESS/<session_id>/`)

   ```python
   @stx.session
   def main(CONFIG=stx.session.INJECTED):
       sio.save(df, "results.csv")                       # auto-routed
       df = sio.load(CONFIG.SDIR_RUN / "results.csv")    # explicit session-path load
   ```

Once you learn the routing, it's a feature, not a bug: every
`sio.save` call produces a clean side-effect-free directory layout
that's trivial to archive, hash-verify via Clew, and reproduce.

### Jupyter notebook routing

Convention:

```
<dir>/<stem>.ipynb         →   sio.save(obj, "name.ext")
                                    ↓
<dir>/<stem>_out/name.ext
```

i.e. each notebook gets a sibling `<stem>_out/` directory in the same
folder. To make this work, scitex-io needs to recover the notebook's
own filename from inside the kernel — a hard problem because the
kernel runs in a separate process from the notebook UI / nbconvert
driver.

**Detection layers** (first hit wins, see
`scitex_io._notebook.resolve_notebook`):

1. `SCITEX_NOTEBOOK_PATH` env var — explicit override (relative paths
   resolve against the kernel's cwd; must be an existing `.ipynb`).
2. `__vsc_ipynb_file__` — VS Code Jupyter injects this into the
   user namespace.
3. `__session__` global / `$JPY_SESSION_NAME` — set for kernels a
   Jupyter server (Lab / Notebook) starts.
4. A `*.ipynb` argument of the process that LAUNCHED the kernel
   (`$JPY_PARENT_PID`, else the parent pid), relative to that
   process's cwd — covers `jupyter nbconvert --execute`, `papermill`,
   `jupyter execute` and nbclient scripts. Accepted only when that
   notebook's code cells contain the cell being executed, so a
   launcher naming a different notebook is never trusted. (The kernel's
   own `sys.argv` is `ipykernel_launcher -f …` and is never used.)
5. A running Jupyter server is asked which notebook owns the kernel
   (`scitex_context.get_notebook_path`).

This is the SAME rule scitex-session uses for `@session` in a notebook,
so `save()` and the session agree on `<stem>_out/`. Both repositories
run the byte-identical `tests/**/conformance/notebook-path-vectors.json`
(+ `run_notebook_vectors.py`); a change to the rule must update both
implementations and those files in both repositories together.

**If none match**, scitex-io falls back to `<cwd>/notebook_out/` and
logs a one-time WARNING naming the sources it tried and how to fix it.
Silence with `SCITEX_IO_QUIET_NOTEBOOK_WARN=1`.

**Explicit override (e.g. a launcher that hides the notebook path):**

```bash
SCITEX_NOTEBOOK_PATH=demo.ipynb \
  jupyter nbconvert --to notebook --execute --inplace demo.ipynb
```

**Recommended for in-cell usage that needs to be portable:** pass an
absolute path to `sio.save` — it bypasses routing entirely.

```python
from pathlib import Path
ROOT = Path.cwd()                       # or any anchor you trust
sio.save(fig, ROOT / "_assets" / "01_demo.png")
```

## scitex_io path utilities

```python
from scitex_io import path  # or scitex_io._path

path.split_fpath("data/file.txt")     # → ("data/", "file", ".txt")
path.find(".", type="f", exp="*.csv") # → list of matching files
path.find_latest(".", "model", ".pt") # → "model_v003.pt" (latest version)
path.touch("new_file.txt")            # create or update mtime
path.find_the_git_root_dir()          # → git repo root
```

## scitex.path (full path toolkit)

`scitex.path` (in scitex-python) provides a richer API:

### Path components

```python
import scitex

scitex.path.split("data/file.txt")       # → (Path("data"), "file", ".txt")
scitex.path.clean("/home/./user/../x")   # → "/home/x"
scitex.path.this_path()                  # → Path of calling script
```

### File finding

```python
stx.path.find_file(".", "*.csv")       # recursive, excludes lib/env/build
stx.path.find_dir(".", "config*")      # find directories
stx.path.find_git_root()               # git repo root
```

### Save path creation

```python
stx.path.mk_spath("results.csv")      # → {script_name}_out/results.csv
stx.path.mk_spath("fig.png", makedirs=True)
```

### Versioning

```python
stx.path.increment_version(".", "model", ".pt")
# If model_v001.pt exists → returns path to model_v002.pt

stx.path.find_latest(".", "model", ".pt")
# → path to model_v002.pt (highest version)
```

### Symlinks

```python
stx.path.symlink("src", "dst")                    # create symlink
stx.path.symlink("src", "dst", relative=True)     # relative symlink
stx.path.is_symlink("link")                       # check
stx.path.readlink("link")                         # target
stx.path.resolve_symlinks("link")                 # full resolution
stx.path.list_symlinks("dir/", recursive=True)    # find all symlinks
stx.path.fix_broken_symlinks("dir/", remove=True) # cleanup broken
```

### Other

```python
stx.path.getsize("file.csv")                      # bytes or np.nan
stx.path.get_data_path_from_a_package("pkg", "data.csv")  # package resource
```
