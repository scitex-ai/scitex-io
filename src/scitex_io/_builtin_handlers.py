#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register built-in format handlers with the registry — *lazily*.

Each extension maps to a ``(module_path, attr_name)`` spec; the matching
format module is only imported when ``get_saver(".ext")`` or
``get_loader(".ext")`` is actually called. This keeps ``import scitex_io``
cheap — a JSON-only ``save({"a":1}, "/tmp/x.json")`` does not transitively
import PIL, pymupdf, pdfminer, pdfplumber, h5py, pyarrow, plotly, or
scipy.

User registrations still override these via the public ``register_saver``
/ ``register_loader`` API (those are *not* lazy — the user passes the
already-imported callable in).
"""

from __future__ import annotations

import importlib as _importlib
import warnings as _warnings

from ._registry import _builtin_loaders, _builtin_savers, _register_builtin_lazy

# ---------------------------------------------------------------------------
# SAVE HANDLERS
# ---------------------------------------------------------------------------
# Each entry is ``(module_path, attr_name)``. The module is *not* imported
# until ``get_saver(ext)`` is called for an extension that maps to it.
_LAZY_SAVERS: dict[str, tuple[str, str]] = {
    # Spreadsheet (cheap: pandas is already a hard dep)
    ".csv": ("scitex_io._save_modules._csv", "_save_csv"),
    # Spreadsheet (heavy: openpyxl)
    ".xlsx": ("scitex_io._save_modules._excel", "save_excel"),
    ".xls": ("scitex_io._save_modules._excel", "save_excel"),
    # Columnar (heavy: pyarrow)
    ".parquet": ("scitex_io._save_modules._parquet", "_save_parquet"),
    ".feather": ("scitex_io._save_modules._feather", "_save_feather"),
    # NumPy (numpy is a hard dep)
    ".npy": ("scitex_io._save_modules._numpy", "_save_npy"),
    ".npz": ("scitex_io._save_modules._numpy", "_save_npz"),
    # Pickle (stdlib)
    ".pkl": ("scitex_io._save_modules._pickle", "_save_pickle"),
    ".pickle": ("scitex_io._save_modules._pickle", "_save_pickle"),
    ".pkl.gz": ("scitex_io._save_modules._pickle", "_save_pickle_gz"),
    # Binary (heavy: joblib, torch, scipy, catboost)
    ".joblib": ("scitex_io._save_modules._joblib", "_save_joblib"),
    ".pth": ("scitex_io._save_modules._torch", "_save_torch"),
    ".pt": ("scitex_io._save_modules._torch", "_save_torch"),
    ".mat": ("scitex_io._save_modules._matlab", "_save_matlab"),
    ".cbm": ("scitex_io._save_modules._catboost", "_save_catboost"),
    # Text (stdlib)
    ".json": ("scitex_io._save_modules._json", "_save_json"),
    ".yaml": ("scitex_io._save_modules._yaml", "_save_yaml"),
    ".yml": ("scitex_io._save_modules._yaml", "_save_yaml"),
    ".txt": ("scitex_io._save_modules._text", "_save_text"),
    ".md": ("scitex_io._save_modules._text", "_save_text"),
    ".py": ("scitex_io._save_modules._text", "_save_text"),
    ".css": ("scitex_io._save_modules._text", "_save_text"),
    ".js": ("scitex_io._save_modules._text", "_save_text"),
    ".log": ("scitex_io._save_modules._text", "_save_text"),
    ".mmd": ("scitex_io._save_modules._text", "_save_text"),
    ".dot": ("scitex_io._save_modules._text", "_save_text"),
    ".gv": ("scitex_io._save_modules._text", "_save_text"),
    ".def": ("scitex_io._save_modules._text", "_save_text"),
    ".cfg": ("scitex_io._save_modules._text", "_save_text"),
    ".ini": ("scitex_io._save_modules._text", "_save_text"),
    ".toml": ("scitex_io._save_modules._text", "_save_text"),
    ".sh": ("scitex_io._save_modules._text", "_save_text"),
    ".bash": ("scitex_io._save_modules._text", "_save_text"),
    ".zsh": ("scitex_io._save_modules._text", "_save_text"),
    ".rst": ("scitex_io._save_modules._text", "_save_text"),
    ".tsv": ("scitex_io._save_modules._text", "_save_text"),
    ".tex": ("scitex_io._save_modules._tex", "save_tex"),
    # Bibliography (heavy: bibtexparser)
    ".bib": ("scitex_io._save_modules._bibtex", "save_bibtex"),
    # Data
    ".html": ("scitex_io._save_modules._html", "save_html"),
    # Scientific (heavy: h5py, zarr)
    ".hdf5": ("scitex_io._save_modules._hdf5", "_save_hdf5"),
    ".h5": ("scitex_io._save_modules._hdf5", "_save_hdf5"),
    ".zarr": ("scitex_io._save_modules._zarr", "_save_zarr"),
    # Media (heavy: matplotlib + imageio)
    ".mp4": ("scitex_io._save_modules._mp4", "_mk_mp4"),
    # Images (heavy: PIL/matplotlib) — _save.py routes images through
    # ``handle_image_with_csv`` rather than the registry, but the
    # registry entries are still here so ``list_formats`` reports them
    # and the rare direct ``get_saver(".png")`` lookup works.
    ".png": ("scitex_io._save_modules._image", "save_image"),
    ".jpg": ("scitex_io._save_modules._image", "save_image"),
    ".jpeg": ("scitex_io._save_modules._image", "save_image"),
    ".gif": ("scitex_io._save_modules._image", "save_image"),
    ".tiff": ("scitex_io._save_modules._image", "save_image"),
    ".tif": ("scitex_io._save_modules._image", "save_image"),
    ".svg": ("scitex_io._save_modules._image", "save_image"),
    ".pdf": ("scitex_io._save_modules._image", "save_image"),
}

for _ext, (_mod, _attr) in _LAZY_SAVERS.items():
    _register_builtin_lazy(_builtin_savers, _ext, _mod, _attr)


# ---------------------------------------------------------------------------
# LOAD HANDLERS
# ---------------------------------------------------------------------------
_LAZY_LOADERS: dict[str, tuple[str, str]] = {
    # Default — empty-ext loads as text
    "": ("scitex_io._load_modules._txt", "_load_txt"),
    # Config (PyYAML / stdlib)
    ".yaml": ("scitex_io._load_modules._yaml", "_load_yaml"),
    ".yml": ("scitex_io._load_modules._yaml", "_load_yaml"),
    ".json": ("scitex_io._load_modules._json", "_load_json"),
    ".xml": ("scitex_io._load_modules._xml", "_load_xml"),
    # Bibliography (heavy: bibtexparser)
    ".bib": ("scitex_io._load_modules._bibtex", "_load_bibtex"),
    # ML/DL (heavy: catboost, torch, joblib)
    ".cbm": ("scitex_io._load_modules._catboost", "_load_catboost"),
    ".pth": ("scitex_io._load_modules._torch", "_load_torch"),
    ".pt": ("scitex_io._load_modules._torch", "_load_torch"),
    ".joblib": ("scitex_io._load_modules._joblib", "_load_joblib"),
    ".pkl": ("scitex_io._load_modules._pickle", "_load_pickle"),
    ".pickle": ("scitex_io._load_modules._pickle", "_load_pickle"),
    ".gz": ("scitex_io._load_modules._pickle", "_load_pickle"),
    # Tabular (pandas hard dep; pyarrow for parquet/feather)
    ".csv": ("scitex_io._load_modules._pandas", "_load_csv"),
    ".tsv": ("scitex_io._load_modules._pandas", "_load_tsv"),
    ".xls": ("scitex_io._load_modules._pandas", "_load_excel"),
    ".xlsx": ("scitex_io._load_modules._pandas", "_load_excel"),
    ".xlsm": ("scitex_io._load_modules._pandas", "_load_excel"),
    ".xlsb": ("scitex_io._load_modules._pandas", "_load_excel"),
    ".parquet": ("scitex_io._load_modules._pandas", "_load_parquet"),
    ".feather": ("scitex_io._load_modules._pandas", "_load_feather"),
    ".db": ("scitex_io._load_modules._sqlite3", "_load_db_sqlite3"),
    # Scientific (heavy: scipy, h5py, zarr)
    ".npy": ("scitex_io._load_modules._numpy", "_load_npy"),
    ".npz": ("scitex_io._load_modules._numpy", "_load_npy"),
    ".mat": ("scitex_io._load_modules._matlab", "_load_matlab"),
    ".hdf5": ("scitex_io._load_modules._hdf5", "_load_hdf5"),
    ".h5": ("scitex_io._load_modules._hdf5", "_load_hdf5"),
    ".zarr": ("scitex_io._load_modules._zarr", "_load_zarr"),
    ".con": ("scitex_io._load_modules._con", "_load_con"),
    # Documents (text formats — `.md` overridden below by markdown loader)
    ".txt": ("scitex_io._load_modules._txt", "_load_txt"),
    ".tex": ("scitex_io._load_modules._txt", "_load_txt"),
    ".log": ("scitex_io._load_modules._txt", "_load_txt"),
    ".mmd": ("scitex_io._load_modules._txt", "_load_txt"),
    ".dot": ("scitex_io._load_modules._txt", "_load_txt"),
    ".gv": ("scitex_io._load_modules._txt", "_load_txt"),
    ".def": ("scitex_io._load_modules._txt", "_load_txt"),
    ".cfg": ("scitex_io._load_modules._txt", "_load_txt"),
    ".ini": ("scitex_io._load_modules._txt", "_load_txt"),
    ".toml": ("scitex_io._load_modules._txt", "_load_txt"),
    ".sh": ("scitex_io._load_modules._txt", "_load_txt"),
    ".bash": ("scitex_io._load_modules._txt", "_load_txt"),
    ".zsh": ("scitex_io._load_modules._txt", "_load_txt"),
    ".rst": ("scitex_io._load_modules._txt", "_load_txt"),
    ".py": ("scitex_io._load_modules._txt", "_load_txt"),
    ".css": ("scitex_io._load_modules._txt", "_load_txt"),
    ".js": ("scitex_io._load_modules._txt", "_load_txt"),
    ".event": ("scitex_io._load_modules._txt", "_load_txt"),
    # Specialised document loaders (heavy: docx, pdf stack)
    ".md": ("scitex_io._load_modules._markdown", "_load_markdown"),
    ".docx": ("scitex_io._load_modules._docx", "_load_docx"),
    ".pdf": ("scitex_io._load_modules._pdf", "_load_pdf"),
    # Images (heavy: PIL)
    ".jpg": ("scitex_io._load_modules._image", "_load_image"),
    ".png": ("scitex_io._load_modules._image", "_load_image"),
    ".tiff": ("scitex_io._load_modules._image", "_load_image"),
    ".tif": ("scitex_io._load_modules._image", "_load_image"),
    # EEG (heavy: mne)
    ".vhdr": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".vmrk": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".edf": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".bdf": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".gdf": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".cnt": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".egi": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".eeg": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
    ".set": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
}

for _ext, (_mod, _attr) in _LAZY_LOADERS.items():
    _register_builtin_lazy(_builtin_loaders, _ext, _mod, _attr)


# Clean up loop variables so they don't leak as module attributes.
del _ext, _mod, _attr


# ---------------------------------------------------------------------------
# Backward-compat module-level attribute access.
#
# Historically ``_builtin_handlers`` exposed every imported saver/loader as
# a module-level name (e.g. ``bh.save_csv``, ``bh._load_json``). Lazy
# registration no longer imports those at module load time, but tests and
# downstream code still poke at the attributes — so resolve them on first
# attribute access via PEP 562.
# ---------------------------------------------------------------------------
_SAVER_ATTRS: dict[str, tuple[str, str]] = {
    # name_on_this_module: (module_path, attr_in_module)
    "save_csv": ("scitex_io._save_modules._csv", "_save_csv"),
    "save_excel": ("scitex_io._save_modules._excel", "save_excel"),
    "save_parquet": ("scitex_io._save_modules._parquet", "_save_parquet"),
    "save_feather": ("scitex_io._save_modules._feather", "_save_feather"),
    "save_npy": ("scitex_io._save_modules._numpy", "_save_npy"),
    "save_npz": ("scitex_io._save_modules._numpy", "_save_npz"),
    "save_pickle": ("scitex_io._save_modules._pickle", "_save_pickle"),
    "save_pickle_compressed": (
        "scitex_io._save_modules._pickle",
        "_save_pickle_gz",
    ),
    "save_joblib": ("scitex_io._save_modules._joblib", "_save_joblib"),
    "save_torch": ("scitex_io._save_modules._torch", "_save_torch"),
    "save_matlab": ("scitex_io._save_modules._matlab", "_save_matlab"),
    "save_catboost": ("scitex_io._save_modules._catboost", "_save_catboost"),
    "save_json": ("scitex_io._save_modules._json", "_save_json"),
    "save_yaml": ("scitex_io._save_modules._yaml", "_save_yaml"),
    "save_text": ("scitex_io._save_modules._text", "_save_text"),
    "save_tex": ("scitex_io._save_modules._tex", "save_tex"),
    "save_bibtex": ("scitex_io._save_modules._bibtex", "save_bibtex"),
    "save_html": ("scitex_io._save_modules._html", "save_html"),
    "save_hdf5": ("scitex_io._save_modules._hdf5", "_save_hdf5"),
    "save_zarr": ("scitex_io._save_modules._zarr", "_save_zarr"),
    "save_mp4": ("scitex_io._save_modules._mp4", "_mk_mp4"),
    "save_image": ("scitex_io._save_modules._image", "save_image"),
}

_LOADER_ATTRS: dict[str, tuple[str, str]] = {
    "_load_txt": ("scitex_io._load_modules._txt", "_load_txt"),
    "_load_yaml": ("scitex_io._load_modules._yaml", "_load_yaml"),
    "_load_json": ("scitex_io._load_modules._json", "_load_json"),
    "_load_xml": ("scitex_io._load_modules._xml", "_load_xml"),
    "_load_bibtex": ("scitex_io._load_modules._bibtex", "_load_bibtex"),
    "_load_catboost": ("scitex_io._load_modules._catboost", "_load_catboost"),
    "_load_torch": ("scitex_io._load_modules._torch", "_load_torch"),
    "_load_joblib": ("scitex_io._load_modules._joblib", "_load_joblib"),
    "_load_pickle": ("scitex_io._load_modules._pickle", "_load_pickle"),
    "_load_csv": ("scitex_io._load_modules._pandas", "_load_csv"),
    "_load_tsv": ("scitex_io._load_modules._pandas", "_load_tsv"),
    "_load_excel": ("scitex_io._load_modules._pandas", "_load_excel"),
    "_load_parquet": ("scitex_io._load_modules._pandas", "_load_parquet"),
    "_load_feather": ("scitex_io._load_modules._pandas", "_load_feather"),
    "_load_db_sqlite3": ("scitex_io._load_modules._sqlite3", "_load_db_sqlite3"),
    "_load_npy": ("scitex_io._load_modules._numpy", "_load_npy"),
    "_load_matlab": ("scitex_io._load_modules._matlab", "_load_matlab"),
    "_load_hdf5": ("scitex_io._load_modules._hdf5", "_load_hdf5"),
    "_load_zarr": ("scitex_io._load_modules._zarr", "_load_zarr"),
    "_load_con": ("scitex_io._load_modules._con", "_load_con"),
    "_load_markdown": ("scitex_io._load_modules._markdown", "_load_markdown"),
    "_load_docx": ("scitex_io._load_modules._docx", "_load_docx"),
    "_load_pdf": ("scitex_io._load_modules._pdf", "_load_pdf"),
    "_load_image": ("scitex_io._load_modules._image", "_load_image"),
    "_load_eeg_data": ("scitex_io._load_modules._eeg", "_load_eeg_data"),
}

_ATTR_SPECS = {**_SAVER_ATTRS, **_LOADER_ATTRS}


def __getattr__(name: str):
    """PEP 562 lazy attribute resolver for back-compat saver/loader names.

    Resolves ``bh.save_csv``, ``bh._load_json`` etc. on demand, caches the
    result on the module, and emits an ``ImportWarning`` (returning
    ``None``) on missing optional dependencies — mirroring the old
    behaviour of the try/except blocks this module used to carry.
    """
    spec = _ATTR_SPECS.get(name)
    if spec is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )
    module_path, attr_name = spec
    try:
        module = _importlib.import_module(module_path)
        value = getattr(module, attr_name, None)
        if value is None:
            raise ImportError(
                f"module {module_path!r} has no attribute {attr_name!r}"
            )
    except Exception as exc:
        _warnings.warn(
            f"scitex_io: {name} not available (missing optional dependency: {exc})",
            ImportWarning,
            stacklevel=2,
        )
        value = None
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(_ATTR_SPECS))
