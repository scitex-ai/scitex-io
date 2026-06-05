#!/usr/bin/env python3
# Timestamp: "2025-05-31"
# File: test__reload.py

"""Tests for scitex.io._reload module.

Real-collaborator tests: we register a real ``types.ModuleType`` in
``sys.modules`` so ``importlib.reload`` is actually invoked, and capture
its print output via ``capsys`` to assert the branch that executed.
"""

import sys
import types

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

from scitex_io._reload import reload


# ---------------------------------------------------------------------------
# Real module reload — happy path via on-disk module
# ---------------------------------------------------------------------------


@pytest.fixture
def real_module(tmp_path):
    """Build a real importable on-disk module + cleanup after the test."""
    mod_name = "scitex_io_test_pkg_reload"
    mod_path = tmp_path / f"{mod_name}.py"
    mod_path.write_text("VALUE = 1\n")
    sys.path.insert(0, str(tmp_path))
    try:
        import importlib

        mod = importlib.import_module(mod_name)
        yield mod_name, mod
    finally:
        sys.modules.pop(mod_name, None)
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))


def test_real_module_reload_verbose_prints_success(real_module, capsys):
    # Arrange
    mod_name, mod = real_module
    # Act
    reload(mod, verbose=True)
    # Assert
    assert "Successfully reloaded module" in capsys.readouterr().out


def test_real_module_reload_silent_when_verbose_false(real_module, capsys):
    # Arrange
    mod_name, mod = real_module
    # Act
    reload(mod, verbose=False)
    # Assert
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Function input — reload of its containing module
# ---------------------------------------------------------------------------


def test_function_reload_uses_function_module_name(real_module, capsys):
    # Arrange
    mod_name, _mod = real_module

    def fn():
        return None

    fn.__module__ = mod_name
    # Act
    reload(fn, verbose=True)
    # Assert
    out = capsys.readouterr().out
    assert f"Successfully reloaded module: {mod_name}" in out


def test_function_module_not_in_sys_modules_prints_error(capsys):
    # Arrange
    def fn():
        return None

    fn.__module__ = "scitex_io_test_missing_module"
    sys.modules.pop("scitex_io_test_missing_module", None)
    # Act
    reload(fn)
    # Assert
    out = capsys.readouterr().out
    assert "Module scitex_io_test_missing_module not found in sys.modules" in out


# ---------------------------------------------------------------------------
# Class input — reload of its containing module
# ---------------------------------------------------------------------------


def test_class_reload_uses_class_module_name(real_module, capsys):
    # Arrange
    mod_name, _mod = real_module

    class TheClass:
        pass

    TheClass.__module__ = mod_name
    # Act
    reload(TheClass, verbose=True)
    # Assert
    out = capsys.readouterr().out
    assert f"Successfully reloaded module: {mod_name}" in out


# ---------------------------------------------------------------------------
# Unrecognised input — the bare object branch
# ---------------------------------------------------------------------------


def test_unrecognised_object_prints_error(capsys):
    # Arrange
    target = object()
    # Act
    reload(target)
    # Assert
    out = capsys.readouterr().out
    assert "neither a recognized module nor a function/class" in out


def test_unrecognised_object_returns_none(capsys):
    # Arrange
    target = object()
    # Act
    result = reload(target)
    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# Module not in sys.modules at all
# ---------------------------------------------------------------------------


def test_module_not_in_sys_modules_returns_without_reload(capsys):
    # Arrange
    mod_name = "scitex_io_test_orphan_module"
    sys.modules.pop(mod_name, None)
    orphan = types.ModuleType(mod_name)  # noqa: F841 — used in act
    # Act
    reload(orphan)
    # Assert
    out = capsys.readouterr().out
    assert "neither a recognized module" in out


# ---------------------------------------------------------------------------
# Real-world: reloading a stdlib module
# ---------------------------------------------------------------------------


def test_reload_real_json_module_does_not_raise():
    # Arrange
    import json

    # Act
    reload(json)
    # Assert
    assert sys.modules["json"] is json or hasattr(sys.modules["json"], "loads")
