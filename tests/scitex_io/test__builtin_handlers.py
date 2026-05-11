#!/usr/bin/env python3
"""Tests for scitex_io._builtin_handlers — registry population on import."""

import importlib

import pytest

import scitex_io._builtin_handlers as bh  # ensure import side effects run
from scitex_io._registry import (
    _builtin_loaders,
    _builtin_savers,
    get_loader,
    get_saver,
)

# Extensions which the builtin handlers module registers
EXPECTED_SAVE_EXTS = [
    ".csv",
    ".xlsx",
    ".xls",
    ".npy",
    ".npz",
    ".pkl",
    ".pickle",
    ".pkl.gz",
    ".joblib",
    ".pth",
    ".pt",
    ".mat",
    ".cbm",
    ".json",
    ".yaml",
    ".yml",
    ".txt",
    ".md",
    ".py",
    ".css",
    ".js",
    ".log",
    ".cfg",
    ".ini",
    ".toml",
    ".sh",
    ".tex",
    ".bib",
    ".html",
    ".hdf5",
    ".h5",
    ".zarr",
    ".mp4",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".tiff",
    ".tif",
    ".svg",
    ".pdf",
    ".parquet",
    ".feather",
]

EXPECTED_LOAD_EXTS = [
    "",
    ".yaml",
    ".yml",
    ".json",
    ".xml",
    ".bib",
    ".cbm",
    ".pth",
    ".pt",
    ".joblib",
    ".pkl",
    ".pickle",
    ".gz",
    ".csv",
    ".tsv",
    ".xls",
    ".xlsx",
    ".xlsm",
    ".xlsb",
    ".parquet",
    ".feather",
    ".db",
    ".npy",
    ".npz",
    ".mat",
    ".hdf5",
    ".h5",
    ".zarr",
    ".con",
    ".txt",
    ".tex",
    ".log",
    ".cfg",
    ".ini",
    ".toml",
    ".md",
    ".docx",
    ".pdf",
    ".jpg",
    ".png",
    ".tiff",
    ".tif",
    ".vhdr",
    ".vmrk",
    ".edf",
    ".bdf",
    ".gdf",
    ".cnt",
    ".egi",
    ".eeg",
    ".set",
]


@pytest.mark.parametrize("ext", EXPECTED_SAVE_EXTS)
def test_saver_registered_and_callable(ext):
    fn = get_saver(ext)
    assert fn is not None, f"Saver missing for {ext}"
    assert callable(fn)
    # Builtin tier is populated
    assert ext in _builtin_savers


@pytest.mark.parametrize("ext", EXPECTED_LOAD_EXTS)
def test_loader_registered_and_callable(ext):
    fn = get_loader(ext)
    assert fn is not None, f"Loader missing for {ext}"
    assert callable(fn)
    assert ext in _builtin_loaders


def test_module_exposes_saver_map_via_imports():
    # The module imported all save_<fmt> functions at top
    assert bh.save_csv is not None
    assert bh.save_npy is not None
    assert bh.save_json is not None
    assert bh.save_hdf5 is not None
    assert bh.save_zarr is not None


def test_loader_funcs_present():
    assert bh._load_json is not None
    assert bh._load_yaml is not None
    assert bh._load_hdf5 is not None
    assert bh._load_zarr is not None
    assert bh._load_pdf is not None
    assert bh._load_docx is not None


def test_reimport_idempotent():
    """Re-importing must not raise; registry stays populated."""
    importlib.reload(bh)
    assert get_saver(".csv") is not None
    assert get_loader(".json") is not None
