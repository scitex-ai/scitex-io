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
# With the per-extension lazy registry, optional-handler resolution is
# deferred until ``get_saver(ext)`` / ``get_loader(ext)`` is actually
# called. Failed lazy imports emit a one-shot ``ImportWarning`` and
# memoise ``None`` so the failure is silent on subsequent calls. To
# exercise that branch honestly we poison the underlying helper module
# in ``sys.modules``, force ``_builtin_handlers`` to re-register its
# lazy specs, then trigger the lookup that resolves them.
# ---------------------------------------------------------------------------

import sys
import warnings


def _reload_with_poisoned(dotted: str):
    """Re-import ``_builtin_handlers`` with ``dotted`` poisoned.

    ``dotted``'s ``find_spec`` raises ``ImportError`` so the lazy
    resolve in ``_registry`` will see a missing dependency. Records
    ``sys.modules`` mutations so the caller can pass them to
    ``_restore_after_poisoned`` for teardown.
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

    # Re-import builtin handlers so the lazy specs are reset (and
    # any previously memoised callable for the poisoned extension is
    # replaced with its tuple form).
    importlib.import_module("scitex_io._builtin_handlers")
    state = {
        "dotted": dotted,
        "saved_dotted": saved_dotted,
        "saved_bh": saved_bh,
        "saved_meta_path": saved_meta_path,
        "finder": finder,
    }
    return state


def _restore_after_poisoned(state):
    """Reverse the mutations made by ``_reload_with_poisoned``."""
    sys.meta_path[:] = state["saved_meta_path"]
    sys.modules.pop("scitex_io._builtin_handlers", None)
    if state["saved_bh"] is not None:
        sys.modules["scitex_io._builtin_handlers"] = state["saved_bh"]
    sys.modules.pop(state["dotted"], None)
    if state["saved_dotted"] is not None:
        sys.modules[state["dotted"]] = state["saved_dotted"]


def test_saver_missing_optional_returns_none():
    """Poison ``_save_modules._parquet`` and verify the lazy
    ``get_saver`` lookup returns ``None``. (Sibling test owns the
    warning assertion.)"""
    # Arrange
    state = _reload_with_poisoned("scitex_io._save_modules._parquet")
    try:
        from scitex_io._registry import get_saver as _gs
        # Act
        result = _gs(".parquet")
        # Assert
        assert result is None
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_saver_missing_optional_emits_warning():
    """Poison ``_save_modules._parquet`` and verify the lazy
    ``get_saver`` lookup emits an ``ImportWarning`` mentioning the
    saver registration. (Sibling test owns the ``None`` return.)"""
    # Arrange
    state = _reload_with_poisoned("scitex_io._save_modules._parquet")
    try:
        from scitex_io._registry import get_saver as _gs
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            # Act
            _gs(".parquet")
        msgs = [str(item.message) for item in captured]
        saver_warns = [
            m for m in msgs if "saver" in m and "not registered" in m
        ]
        # Assert
        assert saver_warns
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_loader_missing_optional_emits_warning():
    """Poison the markdown loader module and verify the lazy
    ``get_loader`` lookup emits an ``ImportWarning`` and returns ``None``."""
    # Arrange
    state = _reload_with_poisoned("scitex_io._load_modules._markdown")
    try:
        from scitex_io._registry import get_loader as _gl

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            # Act
            _gl(".md")
        msgs = [str(item.message) for item in captured]
        loader_warns = [
            m for m in msgs if "loader" in m and "not registered" in m
        ]
        # Assert
        assert loader_warns
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_loader_missing_optional_returns_none():
    """Poison the markdown loader module and verify the lazy
    ``get_loader`` lookup returns ``None``. (Sibling test owns the
    warning.)"""
    # Arrange
    state = _reload_with_poisoned("scitex_io._load_modules._markdown")
    try:
        from scitex_io._registry import get_loader as _gl
        # Act
        result = _gl(".md")
        # Assert
        assert result is None
    finally:
        _restore_after_poisoned(state)
        importlib.reload(sys.modules["scitex_io._builtin_handlers"])


def test_recover_after_poisoned_import():
    """After the poisoned reload + teardown, a clean reload
    re-registers everything."""
    # Arrange
    state = _reload_with_poisoned("scitex_io._save_modules._parquet")
    _restore_after_poisoned(state)
    importlib.import_module("scitex_io._builtin_handlers")
    importlib.reload(sys.modules["scitex_io._builtin_handlers"])
    # Act
    from scitex_io._registry import get_saver as _gs

    # Assert
    assert _gs(".parquet") is not None
