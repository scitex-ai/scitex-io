#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-register all built-in format handlers at import time.

This module is imported by __init__.py to populate the registry
with all supported formats. User registrations override these.
Handlers that are None (missing optional dependency) are silently skipped.
"""

import warnings as _warnings

from ._registry import register_loader, register_saver

# === SAVE HANDLERS ===
from ._save_modules import (
    save_catboost,
    save_csv,
    save_excel,
    save_hdf5,
    save_html,
    save_image,
    save_joblib,
    save_json,
    save_matlab,
    save_mp4,
    save_npy,
    save_npz,
    save_pickle,
    save_pickle_compressed,
    save_tex,
    save_text,
    save_torch,
    save_yaml,
    save_zarr,
)

try:
    from ._save_modules._parquet import _save_parquet as save_parquet
except Exception:
    save_parquet = None

try:
    from ._save_modules._feather import _save_feather as save_feather
except Exception:
    save_feather = None

try:
    from ._save_modules._bibtex import save_bibtex
except Exception:
    save_bibtex = None

_SAVER_MAP = {
    # Spreadsheet
    ".csv": save_csv,
    ".xlsx": save_excel,
    ".xls": save_excel,
    # Columnar
    ".parquet": save_parquet,
    ".feather": save_feather,
    # NumPy
    ".npy": save_npy,
    ".npz": save_npz,
    # Pickle
    ".pkl": save_pickle,
    ".pickle": save_pickle,
    ".pkl.gz": save_pickle_compressed,
    # Binary
    ".joblib": save_joblib,
    ".pth": save_torch,
    ".pt": save_torch,
    ".mat": save_matlab,
    ".cbm": save_catboost,
    # Text
    ".json": save_json,
    ".yaml": save_yaml,
    ".yml": save_yaml,
    ".txt": save_text,
    ".md": save_text,
    ".py": save_text,
    ".css": save_text,
    ".js": save_text,
    ".log": save_text,
    ".mmd": save_text,
    ".dot": save_text,
    ".gv": save_text,
    ".def": save_text,
    ".cfg": save_text,
    ".ini": save_text,
    ".toml": save_text,
    ".sh": save_text,
    ".bash": save_text,
    ".zsh": save_text,
    ".rst": save_text,
    ".tsv": save_text,
    ".tex": save_tex,
    # Bibliography
    ".bib": save_bibtex,
    # Data
    ".html": save_html,
    ".hdf5": save_hdf5,
    ".h5": save_hdf5,
    ".zarr": save_zarr,
    # Media
    ".mp4": save_mp4,
    # Images (handled via _handle_image_with_csv in _save.py)
    ".png": save_image,
    ".jpg": save_image,
    ".jpeg": save_image,
    ".gif": save_image,
    ".tiff": save_image,
    ".tif": save_image,
    ".svg": save_image,
    ".pdf": save_image,
}

for _ext, _fn in _SAVER_MAP.items():
    if _fn is not None:
        register_saver(_ext, _fn, builtin=True)
    else:
        _warnings.warn(
            f"scitex_io: saver for '{_ext}' not registered (missing optional dependency)",
            ImportWarning,
            stacklevel=1,
        )


# === LOAD HANDLERS ===

try:
    from ._load_modules._bibtex import _load_bibtex
except Exception:
    _load_bibtex = None

try:
    from ._load_modules._catboost import _load_catboost
except Exception:
    _load_catboost = None

try:
    from ._load_modules._con import _load_con
except Exception:
    _load_con = None

try:
    from ._load_modules._docx import _load_docx
except Exception:
    _load_docx = None

try:
    from ._load_modules._eeg import _load_eeg_data
except Exception:
    _load_eeg_data = None

try:
    from ._load_modules._hdf5 import _load_hdf5
except Exception:
    _load_hdf5 = None

try:
    from ._load_modules._image import _load_image
except Exception:
    _load_image = None

try:
    from ._load_modules._joblib import _load_joblib
except Exception:
    _load_joblib = None

try:
    from ._load_modules._json import _load_json
except Exception:
    _load_json = None

try:
    from ._load_modules._markdown import _load_markdown
except Exception:
    _load_markdown = None

try:
    from ._load_modules._matlab import _load_matlab
except Exception:
    _load_matlab = None

try:
    from ._load_modules._numpy import _load_npy
except Exception:
    _load_npy = None

try:
    from ._load_modules._pandas import (
        _load_csv,
        _load_excel,
        _load_feather,
        _load_parquet,
        _load_tsv,
    )
except Exception:
    _load_csv = None
    _load_excel = None
    _load_feather = None
    _load_parquet = None
    _load_tsv = None

try:
    from ._load_modules._pdf import _load_pdf
except Exception:
    _load_pdf = None

try:
    from ._load_modules._pickle import _load_pickle
except Exception:
    _load_pickle = None

try:
    from ._load_modules._sqlite3 import _load_db_sqlite3
except Exception:
    _load_db_sqlite3 = None

try:
    from ._load_modules._torch import _load_torch
except Exception:
    _load_torch = None

try:
    from ._load_modules._txt import _load_txt
except Exception:
    _load_txt = None

try:
    from ._load_modules._xml import _load_xml
except Exception:
    _load_xml = None

try:
    from ._load_modules._yaml import _load_yaml
except Exception:
    _load_yaml = None

try:
    from ._load_modules._zarr import _load_zarr
except Exception:
    _load_zarr = None

_LOADER_MAP = {
    # Default
    "": _load_txt,
    # Config
    ".yaml": _load_yaml,
    ".yml": _load_yaml,
    ".json": _load_json,
    ".xml": _load_xml,
    # Bibliography
    ".bib": _load_bibtex,
    # ML/DL
    ".cbm": _load_catboost,
    ".pth": _load_torch,
    ".pt": _load_torch,
    ".joblib": _load_joblib,
    ".pkl": _load_pickle,
    ".pickle": _load_pickle,
    ".gz": _load_pickle,
    # Tabular
    ".csv": _load_csv,
    ".tsv": _load_tsv,
    ".xls": _load_excel,
    ".xlsx": _load_excel,
    ".xlsm": _load_excel,
    ".xlsb": _load_excel,
    ".parquet": _load_parquet,
    ".feather": _load_feather,
    ".db": _load_db_sqlite3,
    # Scientific
    ".npy": _load_npy,
    ".npz": _load_npy,
    ".mat": _load_matlab,
    ".hdf5": _load_hdf5,
    ".h5": _load_hdf5,
    ".zarr": _load_zarr,
    ".con": _load_con,
    # Documents (text formats — `.md` overridden below by markdown loader)
    ".txt": _load_txt,
    ".tex": _load_txt,
    ".log": _load_txt,
    ".mmd": _load_txt,
    ".dot": _load_txt,
    ".gv": _load_txt,
    ".def": _load_txt,
    ".cfg": _load_txt,
    ".ini": _load_txt,
    ".toml": _load_txt,
    ".sh": _load_txt,
    ".bash": _load_txt,
    ".zsh": _load_txt,
    ".rst": _load_txt,
    ".py": _load_txt,
    ".css": _load_txt,
    ".js": _load_txt,
    ".event": _load_txt,
    # Specialized document loaders
    ".md": _load_markdown,
    ".docx": _load_docx,
    ".pdf": _load_pdf,
    # Images
    ".jpg": _load_image,
    ".png": _load_image,
    ".tiff": _load_image,
    ".tif": _load_image,
    # EEG
    ".vhdr": _load_eeg_data,
    ".vmrk": _load_eeg_data,
    ".edf": _load_eeg_data,
    ".bdf": _load_eeg_data,
    ".gdf": _load_eeg_data,
    ".cnt": _load_eeg_data,
    ".egi": _load_eeg_data,
    ".eeg": _load_eeg_data,
    ".set": _load_eeg_data,
}

for _ext, _fn in _LOADER_MAP.items():
    if _fn is not None:
        register_loader(_ext, _fn, builtin=True)
    else:
        _warnings.warn(
            f"scitex_io: loader for '{_ext}' not registered (missing optional dependency)",
            ImportWarning,
            stacklevel=1,
        )
