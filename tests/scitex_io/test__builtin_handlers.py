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
def test_saver_registered_and_callable_fn_is_not_none(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_saver(ext)
    # Act
    # Assert
    # Assert
    assert fn is not None, f"Saver missing for {ext}"


@pytest.mark.parametrize("ext", EXPECTED_SAVE_EXTS)
def test_saver_registered_and_callable_callable_fn(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_saver(ext)
    # Act
    # Assert
    # Assert
    assert callable(fn)


@pytest.mark.parametrize("ext", EXPECTED_SAVE_EXTS)
def test_saver_registered_and_callable_ext_in_builtin_savers(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_saver(ext)
    # Act
    # Assert
    # Assert
    assert ext in _builtin_savers




@pytest.mark.parametrize("ext", EXPECTED_LOAD_EXTS)
def test_loader_registered_and_callable_fn_is_not_none(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_loader(ext)
    # Act
    # Assert
    # Assert
    assert fn is not None, f"Loader missing for {ext}"


@pytest.mark.parametrize("ext", EXPECTED_LOAD_EXTS)
def test_loader_registered_and_callable_callable_fn(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_loader(ext)
    # Act
    # Assert
    # Assert
    assert callable(fn)


@pytest.mark.parametrize("ext", EXPECTED_LOAD_EXTS)
def test_loader_registered_and_callable_ext_in_builtin_loaders(ext):
    # Arrange
    # Arrange
    # Act
    fn = get_loader(ext)
    # Act
    # Assert
    # Assert
    assert ext in _builtin_loaders




def test_module_exposes_saver_map_via_imports_bh_save_csv_is_not_none():
    # The module imported all save_<fmt> functions at top
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh.save_csv is not None


def test_module_exposes_saver_map_via_imports_bh_save_npy_is_not_none():
    # The module imported all save_<fmt> functions at top
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh.save_npy is not None


def test_module_exposes_saver_map_via_imports_bh_save_json_is_not_none():
    # The module imported all save_<fmt> functions at top
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh.save_json is not None


def test_module_exposes_saver_map_via_imports_bh_save_hdf5_is_not_none():
    # The module imported all save_<fmt> functions at top
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh.save_hdf5 is not None


def test_module_exposes_saver_map_via_imports_bh_save_zarr_is_not_none():
    # The module imported all save_<fmt> functions at top
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh.save_zarr is not None




def test_loader_funcs_present_bh_load_json_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_json is not None


def test_loader_funcs_present_bh_load_yaml_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_yaml is not None


def test_loader_funcs_present_bh_load_hdf5_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_hdf5 is not None


def test_loader_funcs_present_bh_load_zarr_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_zarr is not None


def test_loader_funcs_present_bh_load_pdf_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_pdf is not None


def test_loader_funcs_present_bh_load_docx_is_not_none():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert bh._load_docx is not None




def test_reimport_idempotent_get_saver_csv_is_not_none():
    # Arrange
    # Arrange
    # Act
    importlib.reload(bh)
    # Act
    # Assert
    # Assert
    assert get_saver(".csv") is not None


def test_reimport_idempotent_get_loader_json_is_not_none():
    # Arrange
    # Arrange
    # Act
    importlib.reload(bh)
    # Act
    # Assert
    # Assert
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


def _reload_with_poisoned(dotted: str):
    """Force ``import <dotted>`` inside ``_builtin_handlers`` to raise.

    Records ``sys.modules`` mutations and the ``meta_path`` change so
    the caller can pass them to ``_restore_after_poisoned`` for
    teardown.
    """
    saved_dotted = sys.modules.pop(dotted, None)
    saved_bh = sys.modules.pop("scitex_io._builtin_handlers", None)
    saved_meta_path = list(sys.meta_path)

    class _Fail:
        def find_spec(self, name, path=None, target=None):
            if name == dotted:
                raise ImportError(f"poisoned: {dotted}")
            return None

    finder = _Fail()
    sys.meta_path[:] = [finder] + sys.meta_path

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        importlib.import_module("scitex_io._builtin_handlers")
    state = {
        "dotted": dotted,
        "saved_dotted": saved_dotted,
        "saved_bh": saved_bh,
        "saved_meta_path": saved_meta_path,
        "finder": finder,
    }
    return w, state


def _restore_after_poisoned(state):
    """Reverse the mutations made by ``_reload_with_poisoned``."""
    sys.meta_path[:] = state["saved_meta_path"]
    sys.modules.pop("scitex_io._builtin_handlers", None)
    if state["saved_bh"] is not None:
        sys.modules["scitex_io._builtin_handlers"] = state["saved_bh"]
    sys.modules.pop(state["dotted"], None)
    if state["saved_dotted"] is not None:
        sys.modules[state["dotted"]] = state["saved_dotted"]


def test_saver_missing_optional_emits_warning():
    """Poison _save_modules._parquet so the saver = None branch + the
    saver-loop ImportWarning both fire."""
    # Arrange
    captured, state = _reload_with_poisoned("scitex_io._save_modules._parquet")
    try:
        msgs = [str(item.message) for item in captured]
        # Act
        saver_warns = [m for m in msgs if "saver" in m and "not registered" in m]
        # Assert
        assert saver_warns, f"expected ImportWarning about parquet saver; got: {msgs!r}"
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_loader_missing_optional_emits_warning():
    """Poison the markdown loader module so the loader = None +
    warn-and-skip branches in the loader loop both run."""
    # Arrange
    captured, state = _reload_with_poisoned("scitex_io._load_modules._markdown")
    try:
        msgs = [str(item.message) for item in captured]
        # Act
        loader_warns = [m for m in msgs if "loader" in m and "not registered" in m]
        # Assert
        assert loader_warns, f"expected ImportWarning about a loader; got: {msgs!r}"
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_recover_after_poisoned_import():
    """After the poisoned reload + teardown, a clean reload
    re-registers everything."""
    # Arrange
    _captured, state = _reload_with_poisoned("scitex_io._save_modules._parquet")
    _restore_after_poisoned(state)
    importlib.import_module("scitex_io._builtin_handlers")
    importlib.reload(sys.modules["scitex_io._builtin_handlers"])
    # Act
    from scitex_io._registry import get_saver as _gs

    # Assert
    assert _gs(".parquet") is not None
