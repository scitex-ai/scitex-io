#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-06-12 13:05:00 (ywatanabe)"
# File: /ssh:sp:/home/ywatanabe/proj/.claude-worktree/scitex_repo/src/scitex/io/_save_modules/__init__.py
# ----------------------------------------
import os

__FILE__ = "./src/scitex/io/_save_modules/__init__.py"
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Save modules for scitex.io.save functionality

This package contains format-specific save handlers for various file types.
Each module provides a save_<format> function that handles saving objects
to that specific format.
"""

# Core deps always available
from scitex_dev import try_import_optional

from ._csv import _save_csv as save_csv
from ._html import save_html
from ._json import _save_json as save_json
from ._numpy import _save_npy as save_npy
from ._numpy import _save_npz as save_npz
from ._pickle import (
    _save_pickle as save_pickle,
)
from ._pickle import (
    _save_pickle_gz as save_pickle_compressed,
)
from ._tex import _save_tex as save_tex
from ._text import _save_text as save_text

_PKG = "scitex-io"
_HERE = __name__

# Optional: openpyxl / xlrd
save_excel = try_import_optional("._excel", "save_excel", package=_HERE)

# Optional: joblib
save_joblib = try_import_optional("._joblib", "_save_joblib", package=_HERE)

# Optional: torch
save_torch = try_import_optional("._torch", "_save_torch", package=_HERE)

# Optional: PyYAML
save_yaml = try_import_optional("._yaml", "_save_yaml", package=_HERE)

# Optional: h5py
save_hdf5 = try_import_optional(
    "._hdf5", "_save_hdf5", package=_HERE, extra="scientific", pkg=_PKG
)

# Optional: scipy
save_matlab = try_import_optional(
    "._matlab", "_save_matlab", package=_HERE, extra="scientific", pkg=_PKG
)

# Optional: catboost
save_catboost = try_import_optional("._catboost", "_save_catboost", package=_HERE)

# Optional: matplotlib / PIL
save_image = try_import_optional(
    "._image", "save_image", package=_HERE, extra="scientific", pkg=_PKG
)

# Optional: matplotlib / imageio
save_mp4 = try_import_optional(
    "._mp4", "_mk_mp4", package=_HERE, extra="scientific", pkg=_PKG
)

# Optional: zarr
save_zarr = try_import_optional(
    "._zarr", "_save_zarr", package=_HERE, extra="scientific", pkg=_PKG
)

# Optional: bibtexparser
save_bibtex = try_import_optional("._bibtex", "save_bibtex", package=_HERE)

# Optional: pandas (listed df utilities)
save_listed_dfs_as_csv = try_import_optional(
    "._listed_dfs_as_csv", "_save_listed_dfs_as_csv", package=_HERE
)

save_listed_scalars_as_csv = try_import_optional(
    "._listed_scalars_as_csv", "_save_listed_scalars_as_csv", package=_HERE
)

# Optional: optuna
save_optuna_study_as_csv_and_pngs = try_import_optional(
    "._optuna_study_as_csv_and_pngs",
    "save_optuna_study_as_csv_and_pngs",
    package=_HERE,
    extra="optuna",
    pkg=_PKG,
)

# Define what gets imported with "from scitex.io._save_modules import *"
__all__ = [
    "save_csv",
    "save_excel",
    "save_npy",
    "save_npz",
    "save_pickle",
    "save_pickle_compressed",
    "save_joblib",
    "save_torch",
    "save_json",
    "save_yaml",
    "save_hdf5",
    "save_matlab",
    "save_catboost",
    "save_text",
    "save_tex",
    "save_html",
    "save_image",
    "save_mp4",
    "save_zarr",
    "save_bibtex",
    "save_listed_dfs_as_csv",
    "save_listed_scalars_as_csv",
    "save_optuna_study_as_csv_and_pngs",
]

# EOF
