#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP Resources for scitex-io documentation."""

__all__ = ["register_resources"]

CHEATSHEET = """\
# scitex-io Cheatsheet - Universal Scientific File I/O
=======================================================

## Quick Start
```python
import scitex_io as io

# Save any object - format detected from extension
io.save({"key": "value"}, "/tmp/data.json")
io.save(df, "/tmp/results.csv")
io.save(array, "/tmp/data.npy")

# Load - format detected automatically
data = io.load("/tmp/data.json")
df   = io.load("/tmp/results.csv")
arr  = io.load("/tmp/data.npy")
```

## Supported Save Formats
- **Spreadsheet**: .csv, .xlsx, .xls
- **NumPy**: .npy, .npz
- **Pickle**: .pkl, .pickle, .pkl.gz
- **Binary/ML**: .joblib, .pth, .pt, .mat, .cbm
- **Text/Config**: .json, .yaml, .yml, .txt, .md, .py, .css, .js, .tex
- **Bibliography**: .bib
- **Data/HDF**: .html, .hdf5, .h5, .zarr
- **Media**: .mp4
- **Images**: .png, .jpg, .jpeg, .gif, .tiff, .tif, .svg, .pdf

## Supported Load Formats
All save formats plus:
- **Documents**: .docx, .pdf, .log
- **Database**: .db (via scitex-db)
- **EEG**: .vhdr, .vmrk, .edf, .bdf, .gdf, .cnt, .egi, .eeg, .set
- **Other**: .tsv, .xlsm, .xlsb, .con, .xml

## Register Custom Formats
```python
from scitex_io import register_saver, register_loader

@register_saver(".myformat")
def save_myformat(obj, path, **kwargs):
    with open(path, "w") as f:
        f.write(str(obj))

@register_loader(".myformat")
def load_myformat(path, **kwargs):
    with open(path) as f:
        return f.read()
```

## List All Formats
```python
from scitex_io import list_formats
formats = list_formats()
# {"save": {"builtin": [...], "user": [...]},
#  "load": {"builtin": [...], "user": [...]}}
```

## Glob Loading
```python
from scitex_io import glob

# Load all CSVs matching a pattern
files = glob("/data/experiments/*.csv")
```

## Reload (Re-read Latest Version)
```python
from scitex_io import reload
data = reload("/tmp/data.json")
```

## Cache (Avoid Re-loading)
```python
from scitex_io import cache
data = cache("/large_dataset.hdf5")  # Cached after first load
```
"""

FORMATS = """\
# scitex-io Supported Formats
================================

## Save Formats (Built-in)

### Spreadsheet
- `.csv`  — pandas DataFrame or array-like (comma-separated)
- `.xlsx` — Excel workbook (openpyxl)
- `.xls`  — Excel workbook (legacy)

### NumPy
- `.npy`  — Single NumPy array
- `.npz`  — Multiple NumPy arrays (compressed)

### Pickle / Serialization
- `.pkl`, `.pickle`  — Python pickle (any serializable object)
- `.pkl.gz`          — Gzip-compressed pickle

### Binary / ML
- `.joblib` — Scikit-learn models and arrays (joblib)
- `.pth`, `.pt` — PyTorch tensors / model state dicts
- `.mat`    — MATLAB matrices (scipy.io)
- `.cbm`    — CatBoost models

### Text / Config
- `.json`  — JSON (dict, list, scalars)
- `.yaml`, `.yml` — YAML
- `.txt`   — Plain text (str or list of lines)
- `.md`    — Markdown (treated as text)
- `.py`    — Python source (treated as text)
- `.css`, `.js` — Web assets (treated as text)
- `.tex`   — LaTeX source

### Bibliography
- `.bib`   — BibTeX entries

### HDF / Data
- `.hdf5`, `.h5` — HDF5 datasets (h5py)
- `.zarr`  — Zarr arrays/groups
- `.html`  — HTML markup (str)

### Media
- `.mp4`   — Video (imageio)

### Images
- `.png`, `.jpg`, `.jpeg`, `.gif`
- `.tiff`, `.tif`
- `.svg`, `.pdf`  — Vector/document formats via matplotlib

---

## Load Formats (Built-in)

All save formats plus:

### Documents
- `.pdf`   — Text extraction (pdfminer or PyPDF2)
- `.docx`  — Word documents (python-docx)
- `.log`   — Log files (as text)

### Database
- `.db`    — databases via scitex-db (returns dict of DataFrames per table)

### EEG / Neurophysiology
- `.vhdr`, `.vmrk` — BrainVision
- `.edf`, `.bdf`   — European Data Format
- `.gdf`           — General Data Format
- `.cnt`           — Neuroscan
- `.egi`           — EGI/Philips
- `.eeg`           — BrainVision binary
- `.set`           — EEGLAB

### Tabular
- `.tsv`           — Tab-separated values
- `.xlsm`, `.xlsb` — Excel with macros / binary

### Other
- `.con`   — Continuous data files
- `.xml`   — XML documents

---

## Custom Formats

Register your own handlers using the registry API:

```python
from scitex_io import register_saver, register_loader

@register_saver(".myext")
def my_saver(obj, path, **kwargs): ...

@register_loader(".myext")
def my_loader(path, **kwargs): ...
```

User-registered handlers take priority over built-ins.
"""


def register_resources(mcp) -> None:
    """Register documentation resources for scitex-io MCP server."""

    @mcp.resource("scitex-io://cheatsheet")
    def cheatsheet() -> str:
        """scitex-io quick reference cheatsheet."""
        return CHEATSHEET

    @mcp.resource("scitex-io://formats")
    def formats() -> str:
        """All supported file formats for scitex-io."""
        return FORMATS


# EOF
