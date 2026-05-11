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


# ---------------------------------------------------------------------------
# Missing-dependency fallback coverage.
#
# `_builtin_handlers` wraps every optional-loader/saver import in a
# `try/except Exception: <fn> = None` block, then warns + skips the
# registration when the helper is None. In [dev,all] every dep is
# installed so those branches never fire. To exercise them honestly,
# we reload the module with the underlying helper-module poisoned in
# `sys.modules` so the import raises, then assert the warn-and-skip
# path took effect.
# ---------------------------------------------------------------------------

import sys
import warnings


def _reload_with_poisoned(monkeypatch, dotted: str):
    """Force `import <dotted>` inside _builtin_handlers to raise.

    Returns the freshly-reimported module; restoration of sys.modules
    happens automatically when monkeypatch tears down.
    """
    # Drop the cached module so the reimport actually re-executes.
    monkeypatch.delitem(sys.modules, dotted, raising=False)

    # Build a meta-path importer that raises for the target dotted name.
    class _Fail:
        def find_spec(self, name, path=None, target=None):
            if name == dotted:
                raise ImportError(f"poisoned: {dotted}")
            return None

    finder = _Fail()
    monkeypatch.setattr(sys, "meta_path", [finder] + sys.meta_path)

    # Force reload of _builtin_handlers so its try/except blocks run again.
    monkeypatch.delitem(sys.modules, "scitex_io._builtin_handlers", raising=False)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        importlib.import_module("scitex_io._builtin_handlers")
    return w


def test_saver_missing_optional_emits_warning(monkeypatch):
    """Poison _save_modules._parquet so the saver = None branch + the
    saver-loop ImportWarning both fire."""
    captured = _reload_with_poisoned(monkeypatch, "scitex_io._save_modules._parquet")
    # At least one ImportWarning about a saver-for-extension should fire.
    msgs = [str(item.message) for item in captured]
    saver_warns = [m for m in msgs if "saver" in m and "not registered" in m]
    assert saver_warns, f"expected ImportWarning about parquet saver; got: {msgs!r}"


def test_loader_missing_optional_emits_warning(monkeypatch):
    """Poison the markdown loader module so the loader = None +
    warn-and-skip branches in the loader loop both run."""
    captured = _reload_with_poisoned(monkeypatch, "scitex_io._load_modules._markdown")
    msgs = [str(item.message) for item in captured]
    loader_warns = [m for m in msgs if "loader" in m and "not registered" in m]
    assert loader_warns, f"expected ImportWarning about a loader; got: {msgs!r}"


def test_recover_after_poisoned_import(monkeypatch):
    """After the poisoned reload + monkeypatch teardown, a clean
    reload re-registers everything."""
    _reload_with_poisoned(monkeypatch, "scitex_io._save_modules._parquet")
    monkeypatch.undo()  # remove the meta_path finder
    importlib.import_module("scitex_io._builtin_handlers")
    importlib.reload(sys.modules["scitex_io._builtin_handlers"])
    from scitex_io._registry import get_saver as _gs

    # After clean re-register, parquet saver should be back.
    assert _gs(".parquet") is not None
