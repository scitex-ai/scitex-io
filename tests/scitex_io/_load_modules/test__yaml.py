#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:22:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__yaml.py

"""Tests for YAML file loading functionality.

This module tests the _load_yaml function from scitex_io._load_modules._yaml,
which handles loading YAML files with validation and optional key lowercasing.
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
import yaml


@pytest.fixture
def basic_yaml_data():
    """Write a simple yaml file under tmp_path-like NamedTemporaryFile."""
    # Arrange
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: value\nnumber: 42\nlist:\n  - 1\n  - 2\n  - 3\n")
        path = f.name
    try:
        yield path
    finally:
        os.unlink(path)


def test_load_yaml_basic_returns_value_for_key():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: value\nnumber: 42\n")
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["key"] == "value"
    finally:
        os.unlink(temp_path)


def test_load_yaml_basic_returns_int_for_number():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: value\nnumber: 42\n")
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["number"] == 42
    finally:
        os.unlink(temp_path)


def test_load_yaml_basic_returns_list_for_list_key():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("list:\n  - 1\n  - 2\n  - 3\n")
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["list"] == [1, 2, 3]
    finally:
        os.unlink(temp_path)


def test_load_yaml_yml_extension_returns_value_for_test_key():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("test: yml_extension")
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["test"] == "yml_extension"
    finally:
        os.unlink(temp_path)


@pytest.fixture
def complex_yaml_path():
    # Arrange
    yaml_data = """
nested:
  level1:
    level2:
      value: deep
array_of_objects:
  - id: 1
    name: first
  - id: 2
    name: second
null_value: null
boolean: true
float: 3.14159
multiline: |
  This is a
  multiline string
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_data)
        path = f.name
    try:
        yield path
    finally:
        os.unlink(path)


def test_load_yaml_complex_returns_deep_for_nested_path(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert loaded_data["nested"]["level1"]["level2"]["value"] == "deep"


def test_load_yaml_complex_array_objects_have_length_two(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert len(loaded_data["array_of_objects"]) == 2


def test_load_yaml_complex_null_value_is_none(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert loaded_data["null_value"] is None


def test_load_yaml_complex_boolean_value_is_true(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert loaded_data["boolean"] is True


def test_load_yaml_complex_float_value_is_close_to_pi(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert abs(loaded_data["float"] - 3.14159) < 1e-6


def test_load_yaml_complex_multiline_contains_substring(complex_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    loaded_data = _load_yaml(complex_yaml_path)
    # Assert
    assert "multiline string" in loaded_data["multiline"]


@pytest.fixture
def mixed_case_yaml_path():
    # Arrange
    yaml_data = """
UpperCase: value1
MixedCase: value2
lowercase: value3
ALLCAPS: value4
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_data)
        path = f.name
    try:
        yield path
    finally:
        os.unlink(path)


def test_load_yaml_without_lower_preserves_uppercase_key(mixed_case_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    normal_data = _load_yaml(mixed_case_yaml_path)
    # Assert
    assert "UpperCase" in normal_data


def test_load_yaml_with_lower_lowercases_uppercase_key(mixed_case_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    lower_data = _load_yaml(mixed_case_yaml_path, lower=True)
    # Assert
    assert "uppercase" in lower_data


def test_load_yaml_with_lower_preserves_value_for_lowered_key(mixed_case_yaml_path):
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    lower_data = _load_yaml(mixed_case_yaml_path, lower=True)
    # Assert
    assert lower_data["uppercase"] == "value1"


def test_load_yaml_nonexistent_path_raises_filenotfounderror_for_txt():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_yaml("test.txt")


def test_load_yaml_nonexistent_path_raises_filenotfounderror_for_json():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_yaml("/path/to/file.json")


def test_load_yaml_invalid_yaml_content_raises_yamlerror():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("key: [unclosed bracket\nother: {unclosed: brace")
        temp_path = f.name
    try:
        # Act
        ctx = pytest.raises(yaml.YAMLError)
        # Assert
        with ctx:
            _load_yaml(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_yaml_empty_file_returns_none():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data is None
    finally:
        os.unlink(temp_path)


def test_load_yaml_unicode_japanese_value():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    yaml_data = "japanese: こんにちは\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(yaml_data)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["japanese"] == "こんにちは"
    finally:
        os.unlink(temp_path)


def test_load_yaml_unicode_emoji_value():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    yaml_data = "emoji: 🎉🐍\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(yaml_data)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["emoji"] == "🎉🐍"
    finally:
        os.unlink(temp_path)


def test_load_yaml_unicode_mixed_value():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    yaml_data = "mixed: Hello 世界\n"
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write(yaml_data)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_yaml(temp_path)
        # Assert
        assert loaded_data["mixed"] == "Hello 世界"
    finally:
        os.unlink(temp_path)


def test_load_yaml_nonexistent_explicit_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._yaml import _load_yaml

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_yaml("/nonexistent/path/file.yaml")


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
