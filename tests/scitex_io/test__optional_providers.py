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
