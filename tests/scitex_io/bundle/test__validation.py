#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io.bundle._validation`` — JSON-schema validation."""

import pytest

from scitex_io.bundle._validation import (
    SCHEMA_DIR,
    SCHEMA_VERSION,
    ValidationResult,
    load_schema,
)


def test_schema_dir_is_co_located_with_validation_module():
    # Arrange
    # Act
    name = SCHEMA_DIR.name
    # Assert
    assert name == "schemas"


def test_schema_version_is_a_dotted_string():
    # Arrange
    parts = SCHEMA_VERSION.split(".")
    # Act
    is_three_part = len(parts) == 3
    # Assert
    assert is_three_part


def test_load_schema_returns_a_dict_for_known_schema():
    # Arrange
    # Act
    schema = load_schema("node")
    # Assert
    assert isinstance(schema, dict)


def test_load_schema_caches_repeat_loads_returns_same_object():
    # Arrange
    first = load_schema("node")
    # Act
    second = load_schema("node")
    # Assert
    assert first is second


def test_load_schema_raises_file_not_found_for_unknown_schema():
    # Arrange
    name = "nope-this-schema-does-not-exist"
    # Act / Assert
    # Assert
    with pytest.raises(FileNotFoundError):
        load_schema(name)


def test_validation_result_has_errors_false_when_no_errors_added():
    # Arrange
    result = ValidationResult()
    # Act
    has = result.has_errors
    # Assert
    assert has is False
