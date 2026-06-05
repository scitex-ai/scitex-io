#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for the _plot_types subpackage."""


def test_plot_types_subpackage_importable():
    # Arrange
    # Act
    pkg_path = "scitex_io/bundle/kinds/_plot/_models/_plot_types".replace("/", ".")
    pkg_path = pkg_path.replace("tests.", "")
    import importlib
    mod = importlib.import_module(pkg_path)
    # Assert
    assert hasattr(mod, "__path__") or hasattr(mod, "__name__")
