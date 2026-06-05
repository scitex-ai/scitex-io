#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the neutral post-save / post-load hook registry.

Per SOC.md R6: producers expose neutral hook APIs; observers
self-register. These tests verify the producer side fires hooks
correctly and is robust to misbehaving observers.
"""

from __future__ import annotations

import os
import tempfile

import pytest

import scitex_io
from scitex_io._observers import (
    _post_load_hooks,
    _post_save_hooks,
    register_post_load_hook,
    register_post_save_hook,
)


@pytest.fixture
def isolated_hooks():
    # Arrange
    saved_save = list(_post_save_hooks)
    saved_load = list(_post_load_hooks)
    _post_save_hooks.clear()
    _post_load_hooks.clear()
    # Act / yield
    yield
    # Assert / cleanup
    _post_save_hooks[:] = saved_save
    _post_load_hooks[:] = saved_load


def test_register_post_save_hook_fires_on_successful_save(isolated_hooks):
    # Arrange
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(str(p)))
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "save_hook.txt")
    # Act
    scitex_io.save("hello", fpath, verbose=False)
    # Assert
    assert any("save_hook.txt" in p for p in seen)


def test_register_post_load_hook_fires_on_successful_load(isolated_hooks):
    # Arrange
    seen = []
    register_post_load_hook(lambda p, r: seen.append(str(p)))
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "load_hook.txt")
    scitex_io.save("hello", fpath, verbose=False)
    # Act
    scitex_io.load(fpath)
    # Assert
    assert any("load_hook.txt" in p for p in seen)


def test_raising_save_hook_does_not_break_save(isolated_hooks):
    # Arrange
    register_post_save_hook(
        lambda p, obj, kw: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "robust_save.txt")
    # Act
    result = scitex_io.save("hello", fpath, verbose=False)
    # Assert
    assert result is not None and result is not False


def test_raising_load_hook_does_not_break_load(isolated_hooks):
    # Arrange
    register_post_load_hook(lambda p, r: (_ for _ in ()).throw(RuntimeError("boom")))
    tmpdir = tempfile.mkdtemp()
    fpath = os.path.join(tmpdir, "robust_load.txt")
    scitex_io.save("hello", fpath, verbose=False)
    # Act
    data = scitex_io.load(fpath)
    # Assert
    assert data == ["hello"]
