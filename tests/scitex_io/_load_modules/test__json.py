#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2025-06-02 14:20:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__json.py

"""Tests for JSON file loading functionality.

This module tests the _load_json function from scitex_io._load_modules._json,
which handles loading JSON files with proper validation and error handling.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


@pytest.fixture
def basic_json_loaded(tmp_path):
    """Write {"key": "value", "number": 42, "list": [1,2,3]} and load it."""
    from scitex_io._load_modules._json import _load_json

    data = {"key": "value", "number": 42, "list": [1, 2, 3]}
    p = tmp_path / "basic.json"
    p.write_text(json.dumps(data))
    return data, _load_json(str(p))


def test_load_json_basic_round_trips_whole_dict(basic_json_loaded):
    # Arrange
    data, loaded = basic_json_loaded
    # Act
    result = loaded
    # Assert
    assert result == data


def test_load_json_basic_returns_string_value(basic_json_loaded):
    # Arrange
    _, loaded = basic_json_loaded
    # Act
    result = loaded["key"]
    # Assert
    assert result == "value"


def test_load_json_basic_returns_integer_value(basic_json_loaded):
    # Arrange
    _, loaded = basic_json_loaded
    # Act
    result = loaded["number"]
    # Assert
    assert result == 42


def test_load_json_basic_returns_list_value(basic_json_loaded):
    # Arrange
    _, loaded = basic_json_loaded
    # Act
    result = loaded["list"]
    # Assert
    assert result == [1, 2, 3]


_COMPLEX_DATA = {
    "nested": {"level1": {"level2": {"value": "deep"}}},
    "array_of_objects": [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}],
    "null_value": None,
    "boolean": True,
    "float": 3.14159,
}


@pytest.fixture
def complex_json_loaded(tmp_path):
    from scitex_io._load_modules._json import _load_json

    p = tmp_path / "complex.json"
    p.write_text(json.dumps(_COMPLEX_DATA))
    return _load_json(str(p))


def test_load_json_complex_round_trips_whole_dict(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = loaded
    # Assert
    assert result == _COMPLEX_DATA


def test_load_json_complex_preserves_deep_nested_value(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = loaded["nested"]["level1"]["level2"]["value"]
    # Assert
    assert result == "deep"


def test_load_json_complex_preserves_array_length(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = len(loaded["array_of_objects"])
    # Assert
    assert result == 2


def test_load_json_complex_preserves_null_value(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = loaded["null_value"]
    # Assert
    assert result is None


def test_load_json_complex_preserves_boolean_value(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = loaded["boolean"]
    # Assert
    assert result is True


def test_load_json_complex_preserves_float_value(complex_json_loaded):
    # Arrange
    loaded = complex_json_loaded
    # Act
    result = loaded["float"]
    # Assert
    assert abs(result - 3.14159) < 1e-6


def test_load_json_invalid_extension_raises_filenotfounderror():
    # Arrange
    # Arrange
    # Act
    from scitex_io._load_modules._json import _load_json
    # Act
    # Assert
    # Assert
    with pytest.raises(
        FileNotFoundError
    ):  # Extension validation done by load(), not _load_ .json
        # _load_X just opens file; raises FileNotFoundError for non-existent files
        _load_json("test.txt")


def test_load_json_invalid_extension_raises_filenotfounderror():
    # Arrange
    # Arrange
    # Act
    from scitex_io._load_modules._json import _load_json
    # Act
    # Assert
    # Assert
    with pytest.raises(
        FileNotFoundError
    ):  # Extension validation done by load(), not _load_ .json
        # _load_X just opens file; raises FileNotFoundError for non-existent files
        _load_json("/path/to/file.yaml")




def test_load_json_invalid_json_content():
    """Test handling of invalid JSON content."""
    # Arrange
    # Act
    # Assert
    from scitex_io._load_modules._json import _load_json

    # Create a file with invalid JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("This is not valid JSON {incomplete:")
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            _load_json(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_json_empty_file():
    """Test loading an empty JSON file."""
    # Arrange
    # Act
    # Assert
    from scitex_io._load_modules._json import _load_json

    # Create an empty file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(json.JSONDecodeError):
            _load_json(temp_path)
    finally:
        os.unlink(temp_path)


_UNICODE_DATA = {"japanese": "こんにちは", "emoji": "🎉🐍", "mixed": "Hello 世界"}


@pytest.fixture
def unicode_json_loaded(tmp_path):
    from scitex_io._load_modules._json import _load_json

    p = tmp_path / "unicode.json"
    p.write_text(json.dumps(_UNICODE_DATA, ensure_ascii=False), encoding="utf-8")
    return _load_json(str(p))


def test_load_json_unicode_round_trips_whole_dict(unicode_json_loaded):
    # Arrange
    loaded = unicode_json_loaded
    # Act
    result = loaded
    # Assert
    assert result == _UNICODE_DATA


def test_load_json_unicode_preserves_japanese_string(unicode_json_loaded):
    # Arrange
    loaded = unicode_json_loaded
    # Act
    result = loaded["japanese"]
    # Assert
    assert result == "こんにちは"


def test_load_json_unicode_preserves_emoji_string(unicode_json_loaded):
    # Arrange
    loaded = unicode_json_loaded
    # Act
    result = loaded["emoji"]
    # Assert
    assert result == "🎉🐍"


def test_load_json_nonexistent_file():
    """Test loading a nonexistent file."""
    # Arrange
    # Act
    from scitex_io._load_modules._json import _load_json

    # Assert
    with pytest.raises(FileNotFoundError):
        _load_json("/nonexistent/path/file.json")


@pytest.fixture
def large_json_loaded(tmp_path):
    from scitex_io._load_modules._json import _load_json

    large_data = {
        f"key_{i}": {"value": i, "data": list(range(100))} for i in range(100)
    }
    p = tmp_path / "large.json"
    p.write_text(json.dumps(large_data))
    return _load_json(str(p))


def test_load_json_large_returns_all_top_level_keys(large_json_loaded):
    # Arrange
    loaded = large_json_loaded
    # Act
    result = len(loaded)
    # Assert
    assert result == 100


def test_load_json_large_preserves_nested_value_for_known_key(large_json_loaded):
    # Arrange
    loaded = large_json_loaded
    # Act
    result = loaded["key_50"]["value"]
    # Assert
    assert result == 50


def test_load_json_large_preserves_nested_array_length(large_json_loaded):
    # Arrange
    loaded = large_json_loaded
    # Act
    result = len(loaded["key_99"]["data"])
    # Assert
    assert result == 100


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_json.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-14 07:55:40 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_json.py
#
# import json
# from typing import Any
#
#
# def _load_json(lpath: str, **kwargs) -> Any:
#     """Load JSON file.
#
#     Extension validation is handled by load() function, not here.
#     This allows loading files without extensions when ext='json' is specified.
#     """
#     with open(lpath, "r") as f:
#         return json.load(f)
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_json.py
# --------------------------------------------------------------------------------
