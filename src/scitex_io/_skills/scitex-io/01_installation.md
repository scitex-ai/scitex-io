---
description: |
  [TOPIC] Installing scitex-io
  [DETAILS] pip install (standalone vs umbrella), optional MCP extras, format-specific extras (h5/zarr/pdf/eeg), and how to verify the install.
tags: [scitex-io-installation]
---

# Installation

## pip install

```bash
pip install scitex-io                  # core: 30+ formats, save/load, registry
pip install 'scitex-io[mcp]'           # adds the MCP server (`scitex-io mcp start`)
pip install 'scitex-io[all]'           # everything
```

Requires Python >= 3.9.

## Standalone vs umbrella

`scitex-io` is a standalone package, but it is also part of the
[scitex umbrella](https://pypi.org/project/scitex/). The same module
is reachable via two import paths:

```python
# Standalone — pip install scitex-io
import scitex_io
scitex_io.save(df, "results.csv")

# Umbrella — pip install scitex
import scitex
scitex.io.save(df, "results.csv")
```

`pip install scitex-io` alone does **not** expose the `scitex`
namespace; `import scitex.io` raises `ModuleNotFoundError`. To get
both paths, install both: `pip install scitex scitex-io` (or
`pip install scitex[io]`).

## Optional format extras

Heavy / format-specific dependencies are imported lazily via
`scitex_dev.try_import_optional`. A missing dep does not crash
`import scitex_io`; the format becomes unavailable at runtime and a
clear `ImportError` (with `pip install scitex-io[<extra>]` hint) fires
only at use-site. Each gated dep exposes a `<NAME>_AVAILABLE` boolean
for code that wants to feature-flag without raising.

Install extras as needed:

```bash
pip install 'scitex-io[scientific]'   # HDF5 + Zarr + scipy + matplotlib
pip install 'scitex-io[optuna]'       # Optuna study load/save
pip install pypdf Pillow              # PDF / image metadata
pip install mne                       # EEG (.edf, .vhdr, .set, …)
pip install opencv-python             # MP4 video
pip install python-docx               # .docx
pip install pdfplumber PyMuPDF        # PDF table + fitz-based extractors
```

`scitex-io list-formats` shows what is currently registered in your
environment.

## Verify

```bash
scitex-io --version
scitex-io show-info
scitex-io skills list
```

## See also

- [02_quick-start.md](02_quick-start.md) — first save/load in 30 seconds
- [03_python-api.md](03_python-api.md) — full Python surface
- [04_cli-reference.md](04_cli-reference.md) — every subcommand
- [20_env-vars.md](20_env-vars.md) — `SCITEX_IO_*` environment variables
