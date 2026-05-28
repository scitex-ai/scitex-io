#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for the _dataclasses subpackage."""


def test_dataclasses_subpackage_importable():
    # Arrange
    # Act
    pkg_path = "scitex_io/bundle/kinds/_plot/_dataclasses".replace("/", ".")
    pkg_path = pkg_path.replace("tests.", "")
    import importlib
    mod = importlib.import_module(pkg_path)
    # Assert
    assert hasattr(mod, "__path__") or hasattr(mod, "__name__")
