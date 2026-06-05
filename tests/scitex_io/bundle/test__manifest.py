#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io.bundle._manifest`` — manifest.json read/write."""

from scitex_io.bundle._manifest import (
    MANIFEST_FILENAME,
    create_manifest,
    get_type_from_manifest,
    read_manifest,
    write_manifest,
)


def test_manifest_filename_constant_is_manifest_json():
    # Arrange
    # Act
    name = MANIFEST_FILENAME
    # Assert
    assert name == "manifest.json"


def test_create_manifest_records_declared_type():
    # Arrange
    # Act
    manifest = create_manifest("plot", "1.2.3")
    # Assert
    assert manifest["scitex"]["type"] == "plot"


def test_create_manifest_records_declared_version():
    # Arrange
    # Act
    manifest = create_manifest("plot", "1.2.3")
    # Assert
    assert manifest["scitex"]["version"] == "1.2.3"


def test_write_manifest_then_read_manifest_round_trip(tmp_path):
    # Arrange
    write_manifest(tmp_path, "stats", "1.0.0")
    # Act
    read = read_manifest(tmp_path)
    # Assert
    assert read is not None and read["scitex"]["type"] == "stats"


def test_get_type_from_manifest_returns_declared_type(tmp_path):
    # Arrange
    write_manifest(tmp_path, "figure", "2.0.0")
    # Act
    bundle_type = get_type_from_manifest(tmp_path)
    # Assert
    assert bundle_type == "figure"


def test_get_type_from_manifest_returns_none_for_missing_manifest(tmp_path):
    # Arrange
    # Act
    bundle_type = get_type_from_manifest(tmp_path)
    # Assert
    assert bundle_type is None
