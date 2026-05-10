# SciTeX IO (<code>scitex-io</code>)

<p align="center">
  <a href="https://scitex.ai">
    <img src="docs/scitex-logo-blue-cropped.png" alt="SciTeX" width="400">
  </a>
</p>

<p align="center"><b>Universal scientific data I/O with plugin registry</b></p>

<p align="center">
  <a href="https://scitex-io.readthedocs.io/">Full Documentation</a> · <code>uv pip install scitex-io[all]</code>
</p>

<p align="center">
<!-- scitex-badges:start -->
<a href="https://pypi.org/project/scitex-io/"><img src="https://img.shields.io/pypi/v/scitex-io.svg" alt="PyPI"></a>
<a href="https://pypi.org/project/scitex-io/"><img src="https://img.shields.io/pypi/pyversions/scitex-io.svg" alt="Python"></a>
<a href="https://github.com/ywatanabe1989/scitex-io/actions/workflows/test.yml"><img src="https://github.com/ywatanabe1989/scitex-io/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
<a href="https://github.com/ywatanabe1989/scitex-io/actions/workflows/install-test.yml"><img src="https://github.com/ywatanabe1989/scitex-io/actions/workflows/install-test.yml/badge.svg" alt="Install Test"></a>
<a href="https://codecov.io/gh/ywatanabe1989/scitex-io"><img src="https://codecov.io/gh/ywatanabe1989/scitex-io/graph/badge.svg" alt="Coverage"></a>
<a href="https://scitex-io.readthedocs.io/en/latest/"><img src="https://readthedocs.org/projects/scitex-io/badge/?version=latest" alt="Docs"></a>
<a href="https://www.gnu.org/licenses/agpl-3.0"><img src="https://img.shields.io/badge/license-AGPL_v3-blue.svg" alt="License: AGPL v3"></a>
<!-- scitex-badges:end -->
</p>

---

## Problem and Solution

| # | Problem | Solution |
|---|---------|----------|
| 1 | **Format zoo** -- save/load scattered across `pd.read_csv`, `np.load`, `pickle`, `json`, `h5py`, `torch.save`, `cv2.imread`, etc. Every format = a different API | **One call** -- `stx.io.save(obj, "x.ext")` / `stx.io.load("x.ext")` routes by extension across 30+ formats; plugin registry lets users register custom handlers |
| 2 | **FileNotFoundError after save** -- `save()` auto-routes to `{script}_out/` but `load()` resolves cwd-relative, so the naive round-trip breaks for new users | **Predictable paths** -- `symlink_from_cwd=True` flag, `CONFIG.SDIR_RUN` session path, or absolute path on both sides — documented prominently in the skill |
| 3 | **Figure + data diverge** -- save a PNG; the underlying DataFrame lives in a separate `.csv` that goes out of sync | **Auto-CSV export** -- `stx.io.save(fig, "plot.png")` writes `plot.png` + `plot.csv` + `plot.yaml` (figrecipe recipe) atomically, hash-tracked by Clew |

## Problem

Three problems recur in every scientific Python project:

1. **Format fragmentation.** Loading a CSV requires `pandas.read_csv()`, an HDF5 file requires `h5py.File()`, a NumPy array requires `numpy.load()`. Each format demands its own library, its own API, and its own boilerplate. Operating systems solved this decades ago — double-click any file and the OS dispatches to the right application. Python has no equivalent.

2. **Hard-coded parameters scattered across scripts.** Sample rates, thresholds, model hyperparameters, plot dimensions — magic numbers buried in code, duplicated across files, impossible to track or share. Changing one parameter means grepping through the entire project.

3. **Figures without provenance.** A saved PNG has no record of the code, parameters, or session that produced it. Months later, reproducing a figure means reverse-engineering which script with which settings generated it.

## Solution

scitex-io addresses all three:

- **`save()`/`load()`** — One interface for 30+ formats with automatic extension-based dispatch. A plugin registry lets you add custom formats without modifying the library.
- **`load_configs()`** — Loads all YAML files from a `config/` directory into a single `DotDict` with dot-notation access. Parameters are version-controlled, centralized, and separate from code.
- **`embed_metadata()`/`read_metadata()`** — Embeds provenance (timestamps, session IDs, parameters) directly into image and PDF files. The figure carries its own history.

<details>
<summary><b>Supported Formats (30+)</b></summary>

<br>

| Category | Extensions |
|----------|-----------|
| Spreadsheet | `.csv`, `.tsv`, `.xlsx`, `.xls`, `.xlsm`, `.xlsb` |
| Scientific | `.npy`, `.npz`, `.mat`, `.hdf5`, `.h5`, `.zarr` |
| Serialization | `.pkl`, `.pickle`, `.pkl.gz`, `.joblib` |
| ML/DL | `.pth`, `.pt`, `.cbm` |
| Config | `.json`, `.yaml`, `.yml`, `.xml` |
| Database | `.db` (SQLite3) |
| Documents | `.txt`, `.md`, `.pdf`, `.docx`, `.tex`, `.log` |
| Code | `.py`, `.sh`, `.css`, `.js` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.tiff`, `.tif`, `.svg` |
| Media | `.mp4` |
| Web | `.html` |
| Bibliography | `.bib` |
| EEG | `.vhdr`, `.vmrk`, `.edf`, `.bdf`, `.gdf`, `.cnt`, `.egi`, `.eeg`, `.set`, `.con` |

</details>

## Installation

Requires Python >= 3.9.

```bash
pip install scitex-io
```

For MCP server support:

```bash
pip install scitex-io[mcp]
```

## Architecture

```
scitex_io/
├── _save.py / _save_modules/      ← extension-based dispatcher + per-format savers
├── _loading/ / _load_modules/     ← unified load() + per-format loaders
├── _registry.py                   ← plugin registry (register_saver / register_loader)
├── _cache.py / _flush.py / _reload.py  ← path+mtime cache
├── _glob.py                       ← natural-sorted glob, brace expansion, parse_glob
├── _path.py                       ← auto-routing path resolver (script_out/, etc.)
├── _metadata.py / _metadata_modules/   ← embed_metadata / read_metadata (PNG/JPEG/SVG/PDF)
├── _builtin_handlers.py           ← bundled handlers wired to the registry
├── _image_csv_handler.py          ← figure → png + csv + yaml triplet
├── _linter_plugin.py              ← STX-IO001..007 rule plugins for scitex-linter
├── _cli/                          ← `scitex-io` Click CLI
├── _mcp/                          ← MCP server tools
└── _skills/                       ← agent-facing skill pages
```

`save()` and `load()` route by file extension through `_registry`;
every format is a small handler module discovered eagerly at import. The
registry is the extension point — see "Custom Format Registration" below.

## Quickstart

### Save and Load

```python
from scitex_io import save, load

# Universal save/load — format auto-detected from extension
import pandas as pd
df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
save(df, "data.csv")
loaded = load("data.csv")

# 30+ formats work the same way
import numpy as np
save(np.array([1, 2, 3]), "data.npy")
save({"key": "value"}, "config.yaml")
save({"nested": [1, 2]}, "data.json")
```

### Project Configuration

Hard-coded parameters belong in config files, not in code. Use **UPPER_CASE** keys — Python's convention for constants — to signal that these are user-defined values:

```
project/
  config/
    PATHS.yaml          # DATA_DIR: /data/experiment_01
    PREPROCESS.yaml     # SAMPLE_RATE: 1000, BANDPASS: [0.5, 40]
    MODEL.yaml          # HIDDEN_DIM: 256, DROPOUT: 0.3
    PLOT.yaml           # FIGSIZE: [180, 60], DPI: 300
    IS_DEBUG.yaml       # IS_DEBUG: true
```

```python
from scitex_io import load_configs

CONFIG = load_configs()          # loads ./config/*.yaml
CONFIG.PATHS.DATA_DIR            # "/data/experiment_01"
CONFIG.PREPROCESS.SAMPLE_RATE    # 1000
CONFIG.MODEL.HIDDEN_DIM          # 256

# Debug mode: DEBUG_ prefixed keys override their counterparts
# In MODEL.yaml: { HIDDEN_DIM: 256, DEBUG_HIDDEN_DIM: 32 }
CONFIG = load_configs(IS_DEBUG=True)
CONFIG.MODEL.HIDDEN_DIM          # 32 (debug value promoted)
```

Returns a `DotDict` — a nested dictionary with dot-notation access. Parameters become version-controlled, shareable, and separate from code.

### Metadata Embedding

Embed provenance into figures so they carry their own history:

```python
from scitex_io import embed_metadata, read_metadata, has_metadata

# Embed metadata into an image
embed_metadata("figure.png", {
    "experiment": "exp_042",
    "model": "resnet50",
    "accuracy": 0.94,
    "timestamp": "2026-03-11",
})

# Read it back — months later, from the file alone
meta = read_metadata("figure.png")
print(meta["experiment"])    # "exp_042"

# Check if a file has embedded metadata
has_metadata("figure.png")   # True
```

Supports PNG (tEXt chunks), JPEG (EXIF), SVG (XML metadata), and PDF (XMP metadata).

### Advanced Save Features

`save()` auto-routes relative paths based on execution context and supports symlinks and dry runs:

```python
from scitex_io import save

# Auto path routing — relative paths resolve based on context:
#   Script analysis.py  → analysis_out/results.csv
#   Notebook exp.ipynb  → exp_out/results.csv
#   Interactive/IPython → /tmp/{USER}/results.csv
#   Absolute paths      → used as-is
save(df, "results.csv")

# Create symlink from cwd to the auto-routed save location
save(df, "results.csv", symlink_from_cwd=True)

# Create symlink at a specific path
save(fig, "fig1.png", symlink_to="/data/latest/fig1.png")

# Skip auto CSV export for image saves
save(fig, "plot.png", no_csv=True)

# use_caller_path=True — resolve path from the calling script,
# not the immediate caller. Essential when save() is wrapped by a library.
save(df, "results.csv", use_caller_path=True)

# Dry run — print resolved path without writing
save(df, "results.csv", dry_run=True)
```

### Glob and Caching

```python
from scitex_io import glob, parse_glob, load

# Natural-sorted file matching (1, 2, 10 — not 1, 10, 2)
paths = glob("data/**/*.csv")
paths = glob("results/{exp1,exp2}/*.npy")  # brace expansion

# Parse named placeholders from paths
paths, parsed = parse_glob("sub_{id}/ses_{session}/*.vhdr")
# parsed = [{'id': '001', 'session': 'pre'}, ...]

# Glob patterns work directly in load()
dfs = load("results/*.csv")  # → list of DataFrames

# Caching is automatic (by path + mtime)
data = load("large.hdf5")        # disk read
data = load("large.hdf5")        # cache hit (instant)
```

<details>
<summary><b>Custom Format Registration</b></summary>

<br>

```python
from scitex_io import register_saver, register_loader, save, load

@register_saver(".custom")
def save_custom(obj, path, **kwargs):
    with open(path, "w") as f:
        f.write(str(obj))

@register_loader(".custom")
def load_custom(path, **kwargs):
    with open(path) as f:
        return f.read()

save("hello", "data.custom")
assert load("data.custom") == "hello"
```

</details>

## Four Interfaces

<details open>
<summary><strong>Python API</strong></summary>

<br>

```python
from scitex_io import save, load, list_formats, register_saver, register_loader
from scitex_io import load_configs, DotDict
from scitex_io import embed_metadata, read_metadata, has_metadata

save(obj, "path.ext")        # Save any object
data = load("path.ext")      # Load any file
fmts = list_formats()        # Show all registered formats
cfg  = load_configs()        # Load ./config/*.yaml as DotDict
embed_metadata("fig.png", d) # Embed provenance into figure
```

> **[Full API reference](https://scitex-io.readthedocs.io/en/latest/api/scitex_io.html)**

</details>

<details>
<summary><strong>CLI Commands</strong></summary>

<br>

```bash
scitex-io --help-recursive          # Show all commands
scitex-io info                      # Show registered formats
scitex-io configs                   # Load and display project configs
scitex-io configs -d ./my_configs   # Custom config directory
scitex-io configs --json            # Output as JSON
scitex-io list-python-apis -vv      # List Python APIs with signatures
scitex-io --version                 # Show version
scitex-io mcp start                 # Start MCP server
scitex-io mcp doctor                # Check MCP health
scitex-io mcp list-tools -vv        # List MCP tools with parameters
```

> **[Full CLI reference](https://scitex-io.readthedocs.io/en/latest/cli.html)**

</details>

<details>
<summary><strong>MCP Server — for AI Agents</strong></summary>

<br>

AI agents can save, load, and discover formats autonomously.

| Tool | Description |
|------|-------------|
| `io_list_formats` | List all registered save/load formats |
| `io_load` / `io_save` | Load / save data in any supported format |
| `io_load_configs` | Load YAML project configurations |
| `io_register_info` | Show how to register custom formats |
| `io_glob` / `io_parse_glob` | Natsorted globbing with `{placeholder}` parsing |
| `io_get_loader` / `io_get_saver` | Look up the registered handler for an extension |
| `io_read_metadata` / `io_has_metadata` / `io_embed_metadata` | Image provenance metadata |
| `io_get_cache_info` / `io_clear_load_cache` / `io_configure_cache` | Load-cache management |
| `io_explore_h5` / `io_explore_zarr` | Print group/dataset trees |
| `io_has_h5_key` / `io_has_zarr_key` | Cheap existence checks |
| `io_json2md` | Render JSON as Markdown |
| `io_skills_list` / `io_skills_get` | Discover and fetch skill pages |

```bash
scitex-io mcp start
```

> **[Full MCP specification](https://scitex-io.readthedocs.io/en/latest/mcp.html)**

</details>

<details>
<summary><strong>Skills — for AI Agent Discovery</strong></summary>

<br>

Skills provide structured documentation that AI agents can query to discover package capabilities, API signatures, and usage patterns.

```bash
scitex-io skills list              # List available skill pages
scitex-io skills get save-and-load # Get detailed save/load documentation
scitex-io skills get glob          # Get glob/parse_glob patterns
scitex-io skills get supported-formats  # Get all format tables
```

| Skill | Content |
|-------|---------|
| `save-and-load` | Core API, path routing, symlinks, `use_caller_path` |
| `centralized-config` | `load_configs()`, DotDict, DEBUG_ override |
| `metadata-embedding` | Provenance in PNG/JPEG/SVG/PDF |
| `cache` | Load caching, reload, flush |
| `glob` | Pattern matching with natural sort and parsing |
| `linting-rules` | STX-IO001–007 lint rules |
| `supported-formats` | All 30+ format tables |
| `path-resolution` | Auto save-path routing, `scitex.path` utilities |

Also available via MCP: `io_skills_list()` / `io_skills_get(name)`.

</details>

## Demo

```mermaid
flowchart LR
    A["scitex_io.save(obj, 'x.ext')"] --> R["registry: lookup(.ext)"]
    R --> H["per-format saver"]
    H --> F["file on disk + sidecar (csv/yaml)"]
    L["scitex_io.load('x.ext')"] --> R2["registry: lookup(.ext)"]
    R2 --> H2["per-format loader"]
    H2 --> O["Python object<br/>(DataFrame, ndarray, ...)"]
    G["glob('data/**/*.csv')"] --> N["natural-sorted paths"]
    N --> L
```

```python
>>> import pandas as pd, scitex_io as sio
>>> df = pd.DataFrame({"x": [1, 2, 3]})
>>> sio.save(df, "out.csv")          # routes by extension
>>> sio.load("out.csv").equals(df)
True
>>> sio.list_formats()[:5]
['.csv', '.tsv', '.xlsx', '.npy', '.npz']
```

A figure save additionally emits the underlying CSV + a figrecipe YAML
sidecar, keeping figure-and-data atomically in sync.

## Lint Rules

Detected by [scitex-linter](https://github.com/ywatanabe1989/scitex-linter) when this package is installed.

| Rule | Severity | Message |
|------|----------|---------|
| `STX-IO001` | warning | `np.save()` detected — use `stx.io.save()` for provenance tracking |
| `STX-IO002` | warning | `np.load()` detected — use `stx.io.load()` for provenance tracking |
| `STX-IO003` | warning | `pd.read_csv()` detected — use `stx.io.load()` for provenance tracking |
| `STX-IO004` | warning | `.to_csv()` detected — use `stx.io.save()` for provenance tracking |
| `STX-IO005` | warning | `pickle.dump()` detected — use `stx.io.save()` for provenance tracking |
| `STX-IO006` | warning | `json.dump()` detected — use `stx.io.save()` for provenance tracking |
| `STX-IO007` | warning | `.savefig()` detected — use `stx.io.save(fig, path)` for metadata embedding |

## Part of SciTeX

`scitex-io` is part of [**SciTeX**](https://scitex.ai). Install via
the umbrella with `pip install scitex[io]` to use as
`scitex.io` (Python) or `scitex io ...` (CLI).

```python
import scitex

@scitex.session
def main(CONFIG=scitex.INJECTED):
    data = scitex.io.load("input.csv")     # auto-tracked by clew
    result = process(data)
    scitex.io.save(result, "output.csv")   # auto-tracked by clew
    return 0
```

`scitex.io` delegates to `scitex_io` — they share the same API and registry.

The SciTeX system follows the Four Freedoms for Research below, inspired by [the Free Software Definition](https://www.gnu.org/philosophy/free-sw.en.html):

>Four Freedoms for Research
>
>0. The freedom to **run** your research anywhere — your machine, your terms.
>1. The freedom to **study** how every step works — from raw data to final manuscript.
>2. The freedom to **redistribute** your workflows, not just your papers.
>3. The freedom to **modify** any module and share improvements with the community.
>
>AGPL-3.0 — because we believe research infrastructure deserves the same freedoms as the software it runs on.

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
</p>

<!-- EOF -->
