#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for the LaTeX export subpackage."""

import pytest

import scitex_io.bundle.kinds._table._latex as latex


@pytest.mark.parametrize(
    "name",
    [
        "LaTeXExportOptions",
        "LaTeXResult",
        "export_to_latex",
        "export_multiple",
        "validate_latex",
    ],
)
def test_latex_namespace_exposes_symbol(name):
    # Arrange
    # Act
    attr = getattr(latex, name, None)
    # Assert
    assert attr is not None
