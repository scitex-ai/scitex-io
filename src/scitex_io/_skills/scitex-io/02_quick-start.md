---
description: |
  [TOPIC] scitex-io 30-second quick-start
  [DETAILS] First save/load round-trip across CSV, NumPy, pickle, YAML, plus the FileNotFoundError gotcha and the symlink_from_cwd fix.
tags: [scitex-io-quick-start]
---

# Quick Start

## One call, 30+ formats

```python
from scitex_io import save, load
import pandas as pd
import numpy as np

# Save: format auto-detected from extension
save(pd.DataFrame({"x": [1, 2, 3]}), "data.csv")
save(np.array([1, 2, 3]),             "arr.npy")
save({"key": "value"},                "config.yaml")
save({"nested": [1, 2]},              "data.json")

# Load: same call, any format
df  = load("data.csv")
arr = load("arr.npy")
cfg = load("config.yaml")
```

Run `scitex-io list-formats` (or `scitex_io.list_formats()`) to see
every extension currently registered.

## The round-trip gotcha

`save()` auto-routes relative paths into a per-script output dir:

| Context           | Output directory                                   |
|-------------------|----------------------------------------------------|
| Script            | `{script_name}_out/{path}`                         |
| Jupyter notebook  | `{notebook_dir}/{notebook_base}_out/{path}`        |
| Interactive REPL  | `~/.scitex/io/runtime/cache/{path}` (honours `$SCITEX_DIR`) |
| Absolute path     | used as-is                                         |

`load()` resolves relative paths against **cwd**. Naive round-trip
breaks:

```python
save(df, "results.csv")     # writes analysis_out/results.csv
df = load("results.csv")    # FileNotFoundError — looks in cwd
```

Three idiomatic fixes:

```python
# 1. Symlink from cwd (recommended for ad-hoc work)
save(df, "results.csv", symlink_from_cwd=True)
df = load("results.csv")    # works via the cwd symlink

# 2. Use absolute paths on both sides
import scitex_io
spath = scitex_io.path.mk_spath("results.csv")
save(df, spath); df = load(spath)

# 3. Use @scitex.session (CONFIG.SDIR_RUN is the canonical path)
import scitex
@scitex.session
def main(CONFIG=scitex.INJECTED):
    scitex.io.save(df, "results.csv")
    return scitex.io.load(CONFIG.SDIR_RUN / "results.csv")
```

See [16_path-resolution.md](16_path-resolution.md) for the full
auto-routing model.

## Next steps

- [10_save-and-load.md](10_save-and-load.md) — full save/load semantics
- [11_centralized-config.md](11_centralized-config.md) — `load_configs()` for project YAML
- [12_metadata-embedding.md](12_metadata-embedding.md) — provenance baked into figure files
- [04_cli-reference.md](04_cli-reference.md) — CLI surface
