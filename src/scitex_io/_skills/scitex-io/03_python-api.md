---
description: |
  [TOPIC] scitex-io Python API surface
  [DETAILS] Top-level public symbols (save/load, registry, configs, glob, cache, metadata, path, utilities) with one-line summaries and links to deep-dive sub-skills.
tags: [scitex-io-python-api]
---

# Python API

All public symbols are importable from the top-level `scitex_io`
package (or, via the umbrella, `scitex.io`).

## Core I/O

```python
from scitex_io import save, load

save(obj, "results.csv")             # auto-dispatch by extension
save(fig, "plot.png")                # also writes plot.csv + plot.yaml
data = load("results.csv")           # auto-dispatch by extension
```

Common kwargs: `symlink_from_cwd=True`, `symlink_to=<path>`,
`no_csv=True` (skip the figure-CSV companion), `dry_run=True`,
`use_caller_path=True` (resolve from the outer caller, for wrappers).

Deep dive: [10_save-and-load.md](10_save-and-load.md).

## Format registry

```python
from scitex_io import (
    list_formats, register_saver, register_loader,
    get_saver, get_loader,
    unregister_saver, unregister_loader,
)

list_formats()                       # → list of registered extensions

@register_saver(".myfmt")
def _save_myfmt(obj, path, **kw): ...

@register_loader(".myfmt")
def _load_myfmt(path, **kw): ...
```

Deep dive: [15_supported-formats.md](15_supported-formats.md).

## Project configuration

```python
from scitex_io import load_configs, DotDict

CONFIG = load_configs()              # ./config/*.yaml → DotDict
CONFIG.PATHS.DATA_DIR
CONFIG = load_configs(IS_DEBUG=True) # promotes DEBUG_* keys
```

Deep dive: [11_centralized-config.md](11_centralized-config.md).

## Glob with natural sort

```python
from scitex_io import glob, parse_glob

paths = glob("data/**/*.csv")                          # natural-sorted
paths = glob("results/{exp1,exp2}/*.npy")              # brace expansion
paths, parsed = parse_glob("sub_{id}/ses_{ses}/*.vhdr")
dfs = load("results/*.csv")                            # glob in load()
```

Deep dive: [14_glob.md](14_glob.md).

## Caching

```python
from scitex_io import (
    cache, get_cache_info, configure_cache, clear_load_cache, reload, flush,
)

configure_cache(maxsize_bytes=2 * 2**30)
data = load("big.h5")                # disk read
data = load("big.h5")                # cache hit (path + mtime)
clear_load_cache()
```

Deep dive: [13_cache.md](13_cache.md).

## Metadata embedding

```python
from scitex_io import embed_metadata, read_metadata, has_metadata

embed_metadata("figure.png", {"experiment": "exp_042", "accuracy": 0.94})
meta = read_metadata("figure.png")
has_metadata("figure.png")           # → bool
```

Supports PNG (tEXt), JPEG (EXIF), SVG (XML), PDF (XMP).

Deep dive: [12_metadata-embedding.md](12_metadata-embedding.md).

## Path utilities

```python
from scitex_io import path           # may be None if optional dep missing

path.split_fpath("data/file.txt")    # → ("data/", "file", ".txt")
path.find(".", type="f", exp="*.csv")
path.find_latest(".", "model", ".pt")
path.find_the_git_root_dir()
```

Deep dive: [16_path-resolution.md](16_path-resolution.md).

## Save utilities

```python
from scitex_io import (
    save_image, save_text, save_mp4,
    save_listed_dfs_as_csv, save_listed_scalars_as_csv,
    save_optuna_study_as_csv_and_pngs,
)
```

These are the targeted savers behind `save()`'s extension dispatch;
call directly for advanced flags.

## See also

- [04_cli-reference.md](04_cli-reference.md) — same surface from the shell
- [21_linting-rules.md](21_linting-rules.md) — STX-IO001..014 + STX-PA001..005 rules
- Full RTD: <https://scitex-io.readthedocs.io/en/latest/api/scitex_io.html>
