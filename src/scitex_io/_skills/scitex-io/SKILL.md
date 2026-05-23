---
name: scitex-io
description: |
  [WHAT] Universal one-call file I/O for 30+ scientific formats — CSV,
  Parquet, Feather, NumPy .npy/.npz, pickle, YAML, JSON, HDF5, Zarr,
  MATLAB .mat, images, matplotlib figures, PyTorch .pt, MNE .fif, EDF,
  video. Also YAML config loading with UPPER_CASE normalisation,
  figure metadata embedding, load-time caching, natural-sorted glob.
  [WHEN] reading or writing any data file — as a drop-in replacement
  for pd.read_csv, np.load, pickle.load, json.load, fig.savefig,
  torch.save. Trigger phrases: "load", "save", "read", "write", "open
  a file", "save this figure", "cache this result", "load my config",
  "glob these files", "FileNotFoundError after sio.save",
  "symlink_from_cwd", "script_out directory".
  [HOW] sio.save(obj, path) / sio.load(path) auto-dispatch by
  extension. save() with a relative path is caller-anchored: from a
  script /path/to/x.py it writes /path/to/x_out/<path>; from a
  notebook /path/to/x.ipynb it writes /path/to/x_out/<path>; from
  IPython / REPL it writes $SCITEX_DIR/io/runtime/cache/<path>
  (default ~/.scitex/io/runtime/cache/). Intermediate dirs auto-
  created. load() resolves relative paths against cwd — use
  symlink_from_cwd=True on save, or absolute paths on both sides,
  to round-trip.
tags: [scitex-io]
allowed-tools: mcp__scitex__io_*
primary_interface: python
interfaces:
  python: 3
  cli: 1
  mcp: 1
  skills: 2
  http: 0
---

# scitex-io

Universal scientific data I/O with plugin registry. One `save()`/`load()` for 30+ formats.

## Installation & import (two equivalent paths)

The same module is reachable via two install paths; use whichever
matches your dependency story. Verified 2026-04-23 in a clean
container.

```python
# Standalone — pip install scitex-io
import scitex_io as sio
sio.save(df, "results.csv")

# Umbrella — pip install scitex
import scitex.io as sio
sio.save(df, "results.csv")
```

`pip install scitex-io` alone **does not** expose the `scitex`
namespace; `import scitex.io` raises `ModuleNotFoundError`. If you
want the `scitex.io` form, install both (`pip install scitex
scitex-io`) or install the umbrella which pulls scitex-io in
as an extra.

See [../../general/02_interface-python-api.md] for the ecosystem-wide
rule and the empirical verification table.

## Sub-skills

### Onboarding (canonical 01–04)
* [01_installation](01_installation.md) — pip install + extras + verify
* [02_quick-start](02_quick-start.md) — first save/load round-trip
* [03_python-api](03_python-api.md) — full Python surface
* [04_cli-reference](04_cli-reference.md) — every CLI subcommand

### Core workflow
* [10_save-and-load](10_save-and-load.md) — Core save/load API, registry, custom formats
* [11_centralized-config](11_centralized-config.md) — `load_configs()` and DotDict
* [12_metadata-embedding](12_metadata-embedding.md) — Provenance in PNG/JPEG/SVG/PDF
* [13_cache](13_cache.md) — Load caching, reload, flush
* [14_glob](14_glob.md) — Pattern matching with natural sort
* [15_supported-formats](15_supported-formats.md) — All 30+ format tables
* [16_path-resolution](16_path-resolution.md) — Auto save-path, scitex.path utilities

### Standards
* [21_linting-rules](21_linting-rules.md) — STX-IO001..014 + STX-PA001..005 lint rules

## MCP Tools

| Tool | Purpose |
|------|---------|
| `io_save` / `io_load` | Save / load data (auto-detect format) |
| `io_load_configs` | Load `./config/*.yaml` as a `DotDict` (UPPER_CASE normalised) |
| `io_list_formats` / `io_get_saver` / `io_get_loader` | Discover registered handlers |
| `io_register_info` | Show registration info for a format |
| `io_glob` / `io_parse_glob` | Natural-sorted globbing with placeholder parsing |
| `io_get_cache_info` / `io_clear_load_cache` / `io_configure_cache` | Load-cache management |
| `io_embed_metadata` / `io_read_metadata` / `io_has_metadata` | Figure provenance |
| `io_explore_h5` / `io_explore_zarr` | Group / dataset trees |
| `io_has_h5_key` / `io_has_zarr_key` | Cheap existence checks |
| `io_json2md` | Render JSON as Markdown |
| `io_skills_list` / `io_skills_get` | Discover and fetch skill pages |

## CLI

```bash
scitex-io info data.csv           # Format, shape, dtypes
scitex-io configs show ./config/  # Display merged configs
scitex-io mcp start               # Start MCP server
scitex-io skills list              # List skill pages
```


## Environment

- [20_env-vars.md](20_env-vars.md) — SCITEX_* env vars read by scitex-io at runtime
