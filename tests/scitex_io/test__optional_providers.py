#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._optional_providers — optional ecosystem synergy.

Two behaviours are contracted:

- **figrecipe present** → ``.fig.zip`` / ``.plt.zip`` dispatch through the
  registry and ``save``/``load`` round-trip a figure bundle.
- **figrecipe absent** → those extensions stay unregistered and
  ``_register_figrecipe`` reports ``False`` rather than raising.
"""

import os

import pytest

import scitex_io
from scitex_io import _optional_providers
from scitex_io._registry import get_loader, get_saver

figrecipe = pytest.importorskip("figrecipe", reason="figrecipe optional extra")


@pytest.fixture(autouse=True)
def _ensure_registered():
    # Arrange: trigger _ensure_builtin_handlers_registered (idempotent).
    scitex_io.list_formats()
    yield


@pytest.fixture
def line_plot_figure():
    # Arrange: a minimal recorded figure figrecipe can serialise.
    fig, ax = figrecipe.subplots()
    ax.plot([1, 2, 3], [4, 5, 6])
    return fig


class TestFigrecipePresent:
    def test_fig_zip_is_a_declared_compound_ext(self):
        # Arrange
        exts = _optional_providers.OPTIONAL_COMPOUND_EXTS
        # Act
        # Assert
        assert ".fig.zip" in exts

    def test_plt_zip_is_a_declared_compound_ext(self):
        # Arrange
        exts = _optional_providers.OPTIONAL_COMPOUND_EXTS
        # Act
        # Assert
        assert ".plt.zip" in exts

    def test_saver_registered_for_plt_zip(self):
        # Arrange
        # Act
        saver = get_saver(".plt.zip")
        # Assert
        assert callable(saver)

    def test_saver_registered_for_fig_zip(self):
        # Arrange
        # Act
        saver = get_saver(".fig.zip")
        # Assert
        assert callable(saver)

    def test_loader_registered_for_plt_zip(self):
        # Arrange
        # Act
        loader = get_loader(".plt.zip")
        # Assert
        assert callable(loader)

    def test_loader_registered_for_fig_zip(self):
        # Arrange
        # Act
        loader = get_loader(".fig.zip")
        # Assert
        assert callable(loader)

    def test_register_figrecipe_returns_true_when_present(self):
        # Arrange
        # Act
        registered = _optional_providers._register_figrecipe()
        # Assert
        assert registered is True

    def test_save_writes_plt_zip_bundle(self, line_plot_figure, tmp_path):
        # Arrange
        path = os.path.join(str(tmp_path), "panel.plt.zip")
        # Act
        out = scitex_io.save(line_plot_figure, path, verbose=False)
        # Assert
        assert os.path.exists(str(out))

    def test_load_reproduces_figure_from_plt_zip(self, line_plot_figure, tmp_path):
        # Arrange
        path = os.path.join(str(tmp_path), "panel.plt.zip")
        scitex_io.save(line_plot_figure, path, verbose=False)
        # Act
        loaded_fig, _loaded_ax = scitex_io.load(path, cache=False)
        # Assert
        assert loaded_fig is not None


class TestGracefulAbsent:
    """figrecipe absent is simulated with a real importer that returns None."""

    def test_register_figrecipe_returns_false_when_importer_yields_none(self):
        # Arrange: a real importer standing in for "package not installed".
        def absent_importer():
            return None

        # Act
        registered = _optional_providers._register_figrecipe(importer=absent_importer)
        # Assert
        assert registered is False

    def test_absent_provider_does_not_register_a_saver(self):
        # Arrange
        before = get_saver(".plt.zip")

        def absent_importer():
            return None

        # Act
        _optional_providers._register_figrecipe(importer=absent_importer)
        # Assert: an absent provider never mutates the registry.
        assert get_saver(".plt.zip") is before


def test_stats_missing_bundle_entrypoints_do_not_advertise_callbacks(tmp_path):
    """Refuse a real submodule import; retain the existing registry identities."""
    # Arrange: use real IO and installed Stats in an isolated interpreter.
    import subprocess
    import sys

    script = """
import sys
sys.path[:] = PATHS
import importlib
import importlib.abc
import json
import scitex_stats
from scitex_stats.io import load_stats_bundle, save_stats_bundle
from scitex_io import _optional_providers as providers
from scitex_io._registry import get_loader, get_saver
before = (get_loader('.stats.zip'), get_saver('.stats.zip'))
class MissingStatsIO(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'scitex_stats.io' or fullname.startswith('scitex_stats.io.'):
            raise ImportError('controlled missing Stats IO entrypoints', name=fullname)
for name in tuple(sys.modules):
    if name == 'scitex_stats.io' or name.startswith('scitex_stats.io.'):
        del sys.modules[name]
sys.meta_path.insert(0, MissingStatsIO())
registered = providers._register_scitex_stats()
after = (get_loader('.stats.zip'), get_saver('.stats.zip'))
sys.stdout.write(json.dumps([registered, after[0] is before[0], after[1] is before[1]]))
""".replace("PATHS", repr(sys.path), 1)
    # Act
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", script],
        cwd=tmp_path, capture_output=True, text=True, timeout=7,
    )
    # Assert: no fake Stats package, callback, or registry function was supplied.
    import json

    assert (result.returncode, json.loads(result.stdout)) == (0, [False, True, True])


def test_stats_available_bundle_entrypoints_register_real_callbacks():
    # Arrange: genuine declared companion exports, not replacement functions.
    from scitex_stats.io import load_stats_bundle, save_stats_bundle

    # Act
    registered = _optional_providers._register_scitex_stats()
    # Assert
    assert (registered, callable(load_stats_bundle), callable(save_stats_bundle), callable(get_loader(".stats.zip")), callable(get_saver(".stats.zip"))) == (True, True, True, True, True)
