#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for pure-I/O bundle kinds (image, text, shape, table)."""

import pytest

import scitex_io.bundle.kinds as kinds


@pytest.mark.parametrize(
    "name",
    [
        "render_image",
        "load_image",
        "render_shape",
        "render_text",
        "export_to_latex",
    ],
)
def test_kinds_namespace_exposes_symbol(name):
    # Arrange
    # Act
    attr = getattr(kinds, name, None)
    # Assert
    assert attr is not None
