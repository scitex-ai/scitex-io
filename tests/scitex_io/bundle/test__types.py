#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for ``scitex_io.bundle`` — generic bundle plumbing.

These tests pin the format-agnostic primitives that figrecipe.io and
scitex_stats.io layer on top of. Domain-specific bundle round-trip
semantics live in their respective standalone test suites.
"""

import pytest

import scitex_io.bundle as bundle


@pytest.mark.parametrize(
    "name",
    [
        # Types.
        "BundleType",
        "BundleError",
        "BundleValidationError",
        "BundleNotFoundError",
        "NestedBundleNotFoundError",
        "EXTENSIONS",
        "DIR_EXTENSIONS",
        "FIGURE",
        "PLOT",
        "STATS",
        # Dataclasses.
        "Spec",
        "SpecRefs",
        "DataInfo",
        "DataSource",
        "DataFormat",
        "ColumnDef",
        "Axes",
        "BBox",
        "SizeMM",
        "TextContent",
        "ShapeParams",
        "DATA_INFO_VERSION",
    ],
)
def test_bundle_namespace_exposes_symbol(name):
    """Every declared name is reachable as ``scitex_io.bundle.<name>``."""
    # Arrange
    # Act
    attr = getattr(bundle, name, None)
    # Assert
    assert attr is not None


def test_extensions_tuple_contains_compound_zip_extensions():
    """``EXTENSIONS`` is the list of bundle ``*.zip`` formats this plumbing supports."""
    # Arrange
    expected = (".figure.zip", ".plot.zip", ".stats.zip")
    # Act
    actual = bundle.EXTENSIONS
    # Assert
    assert actual == expected


def test_dir_extensions_tuple_contains_directory_bundle_extensions():
    """``DIR_EXTENSIONS`` is the legacy/working-directory equivalent."""
    # Arrange
    expected = (".figure", ".plot", ".stats")
    # Act
    actual = bundle.DIR_EXTENSIONS
    # Assert
    assert actual == expected


def test_bundle_type_normalize_lowercases():
    """``BundleType.normalize`` lowercases the input."""
    # Arrange
    raw = "FIGURE"
    # Act
    normalized = bundle.BundleType.normalize(raw)
    # Assert
    assert normalized == "figure"


def test_bundle_validation_error_is_value_error_subclass():
    """``BundleValidationError`` inherits from ``ValueError`` so generic handlers catch it."""
    # Arrange
    # Act
    is_value_error = issubclass(bundle.BundleValidationError, ValueError)
    # Assert
    assert is_value_error


def test_bundle_not_found_error_is_file_not_found_error_subclass():
    """``BundleNotFoundError`` inherits from ``FileNotFoundError``."""
    # Arrange
    # Act
    is_fnf = issubclass(bundle.BundleNotFoundError, FileNotFoundError)
    # Assert
    assert is_fnf
