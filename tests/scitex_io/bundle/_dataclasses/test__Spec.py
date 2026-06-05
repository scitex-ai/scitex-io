#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for ``scitex_io.bundle._dataclasses``.

These are the format-agnostic dataclasses (``Spec``, ``DataInfo``,
``SizeMM``, ``BBox``, …) that bundle handlers across the ecosystem
build on. Domain-specific schemas (Stats, Encoding, Theme) layer on
top of these in their respective standalone packages.
"""

import dataclasses

import pytest

import scitex_io.bundle._dataclasses as dc


@pytest.mark.parametrize(
    "name",
    [
        "BBox",
        "SizeMM",
        "Axes",
        "Spec",
        "SpecRefs",
        "TextContent",
        "ShapeParams",
        "DATA_INFO_VERSION",
        "DataSource",
        "DataFormat",
        "DataInfo",
        "ColumnDef",
    ],
)
def test_dataclasses_namespace_exposes_symbol(name):
    """Every name in ``__all__`` resolves at the subpackage root."""
    # Arrange
    # Act
    attr = getattr(dc, name, None)
    # Assert
    assert attr is not None


@pytest.mark.parametrize(
    "name",
    [
        "BBox",
        "SizeMM",
        "Axes",
        "Spec",
        "SpecRefs",
        "DataSource",
        "DataFormat",
        "DataInfo",
        "ColumnDef",
    ],
)
def test_class_is_a_dataclass(name):
    """Each declared class is an actual ``@dataclass`` (not a stub)."""
    # Arrange
    cls = getattr(dc, name)
    # Act
    is_dc = dataclasses.is_dataclass(cls)
    # Assert
    assert is_dc


def test_data_info_version_is_a_dotted_string():
    """``DATA_INFO_VERSION`` follows semver-ish ``major.minor.patch``."""
    # Arrange
    parts = dc.DATA_INFO_VERSION.split(".")
    # Act
    is_three_part = len(parts) == 3
    # Assert
    assert is_three_part
