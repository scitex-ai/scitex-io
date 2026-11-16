---
description: |
  [TOPIC] Linting rules
  [DETAILS] STX-IO001–019 + STX-PA001–005 lint rules detected by
  scitex-dev's linter (already a hard dep of scitex-io)
  (np.save → sio.save, etc.), including the research-script-scoped raw
  file I/O family (open(), pathlib read/write, shutil copy/move,
  os.rename/remove) that bypasses provenance.
tags: [scitex-io-linting-rules, scitex-io, scitex-package]
---

# Linting Rules

Detected by [`scitex-dev`](https://github.com/ywatanabe1989/scitex-dev)'s linter via the `scitex_dev.linter.plugins` entry point. `scitex-dev` is already a hard dependency of `scitex-io`, so no extra install is required.

```bash
scitex-dev linter check-files src/           # lint a tree
scitex-dev linter list-rules --category io   # show live rule definitions
```

## I/O rules (STX-IO0xx)

| Rule | Detects | Suggestion |
|------|---------|------------|
| STX-IO001 | `np.save/savez/savez_compressed/savetxt`, `arr.tofile(path)` | → `sio.save(arr, path)` |
| STX-IO002 | `np.load/loadtxt/genfromtxt/fromfile` | → `sio.load(path)` |
| STX-IO003 | `pd.read_csv/parquet/excel/hdf/pickle/json/feather/table/orc` | → `sio.load(path)` |
| STX-IO004 | `df.to_csv/parquet/excel/hdf/pickle/json/feather/html/orc`, `pd.ExcelWriter(...)` | → `sio.save(df, path)` |
| STX-IO005 | `pickle.dump/dumps/load/loads` (and `cPickle`) | → `sio.save(obj, "file.pkl")` / `sio.load(...)` |
| STX-IO006 | `json.dump/dumps/load/loads` | → `sio.save(obj, "file.json")` / `sio.load(...)` |
| STX-IO007 | `.savefig()` | → `sio.save(fig, path)` for metadata embedding |
| STX-IO008 | `torch.save/load` | → `sio.save(obj, "file.pt")` / `sio.load(...)` |
| STX-IO009 | `joblib.dump/load` | → `sio.save(obj, "file.joblib")` / `sio.load(...)` |
| STX-IO010 | `yaml.dump/safe_dump/dump_all/load/safe_load/full_load` | → `sio.save(obj, "file.yaml")` / `sio.load(...)` |
| STX-IO011 | `scipy.io.savemat/loadmat` under any alias (`sio.`, `spio.`, `scipy.io.`, `from scipy.io import savemat`) | → `sio.save(d, "file.mat")` / `sio.load(...)` |
| STX-IO012 | `cv2.imwrite/imread`, `Image.open`, PIL `img.save(path)`, `plt.imsave/imread`, `imageio.imwrite/imread` | → `sio.save(img, "file.png")` / `sio.load(...)` |
| STX-IO013 | `h5py.File()` | → `sio.save(obj, "file.h5")` / `sio.load(...)` |
| STX-IO014 | `sio.save/load(obj, "./x.<unknown>")` — extension has no registered handler (read live from the registry, so user-registered extensions count) | → `register_saver('.ext')` / `register_loader('.ext')`, or use a built-in extension |
| STX-IO015 | `sqlite3.connect()` | → register a `.db` saver/loader and route through `sio.save/load` |
| STX-IO016 † | `Path.write_text/write_bytes`, `Path(...).open("w")` | → `sio.save(obj, "./out.ext")` |
| STX-IO017 † | `Path.read_text/read_bytes`, `Path(...).open()` | → `sio.load("./in.ext")` |
| STX-IO018 † | `shutil.copy/copy2/copyfile/copytree/move` | → `sio.save(sio.load(src), dst)` so both ends are recorded |
| STX-IO019 † | `os.rename/renames/replace/remove/unlink`, `Path.rename/replace/unlink` on a data path (a literal non-data path such as `run.lock` is ignored) | → save at the final path; never delete a recorded output |

Bare calls of from-imported functions (`from numpy import save; save(...)`)
get the same rule as the attribute form.

## Path rules (STX-PA0xx)

| Rule | Detects | Suggestion |
|------|---------|------------|
| STX-PA001 | Absolute path in `sio.save/load(...)` | Use `./relative/path.ext` — paths resolve to `script_out/` |
| STX-PA002 † | `open(path)` / `io.open` / `codecs.open` — anywhere in a research script, including helpers defined above `main` | → `sio.save/load(...)` for auto-logging |
| STX-PA003 | `os.makedirs/mkdir` | Remove — `sio.save` auto-creates dirs (info-level) |
| STX-PA004 | `os.chdir()` | Remove — run scripts from project root |
| STX-PA005 | `sio.save(obj, "file.ext")` (no `./` prefix) | Use `./file.ext` for explicit relative intent (info-level) |

All IO rules: severity `warning`, category `io`. All PA rules: category `path`; PA003/PA005 are `info`, the rest `warning`. In a `project-type: research` project the `io` and `path` categories are promoted to `error`.

## † Research-script scope (raw file I/O)

Rules marked † carry `scope="research-script"` (scitex-dev ≥ 0.63.0 plugin
SPI): the scitex-dev engine reports them only in **research scripts** — a
module with an `@stx.session` / `@stx.module` entry point, or a file under
`scripts/` of a `project-type: research` project. Tests and library code
(`src/`) are never flagged. Research scripts must not bypass `stx.io`:
a file written by `Path.write_text` or copied by `shutil.copy` gets no clew
edge, so `clew chain` on the result is empty.

The plugin declares the `raw-io` capability. scitex-dev **refuses** to lint
a research project when no installed plugin declares it (scitex-io missing
or older than 0.5.0) instead of reporting a clean run.

A genuine non-data file op (a lock file, a log the session already
captures) is opted out on its line, with a reason:

```python
os.remove("run.lock")              # literal non-data path: not flagged anyway
Path(tmp).unlink()  # stx-allow: STX-IO019  (reason: scratch file, never an output)
```

## Recognized package aliases

The linter accepts these forms interchangeably for save/load detection and PA rule application:

```python
sio.save(arr, "./a.npy")           # canonical short alias (import scitex_io as sio)
scitex_io.save(arr, "./a.npy")     # bare top-level (also: scitex_io.io.save(...))
scitex.io.save(arr, "./a.npy")     # via umbrella (import scitex)
```

The linter also accepts the legacy short-alias form
(`scitex` imported as `stx`) for backward compatibility, but new code
should use bare `import scitex` per the general ecosystem rule.

## Custom format hint

Every IO rule's suggestion now includes a register-handler reminder:

```python
from scitex_io import register_saver, register_loader

@register_saver(".myext")
def save_myext(obj, path, **kw): ...

@register_loader(".myext")
def load_myext(path, **kw): ...
```

`STX-IO014` specifically fires when `sio.save/load` is called with an extension scitex-io has no registered handler for — pointing the user at `register_saver` / `register_loader` for that exact extension.

## Why

`sio.save/load` provides provenance tracking, auto-CSV export for figures, metadata embedding, centralized format dispatch, and (for `save`) script-relative output routing. Direct library calls bypass these.
