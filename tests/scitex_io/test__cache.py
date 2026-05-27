#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-05-31"
# File: test__cache.py

"""Tests for the cache function in scitex.io module.

The production ``cache(id, *args, cache_root=...)`` takes a
``cache_root`` keyword so tests can sandbox the on-disk cache under
``tmp_path`` without monkey-patching ``Path.home``.
"""

from pathlib import Path

import numpy as np
import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

from scitex_io import cache

# ---------------------------------------------------------------------------
# Save (all vars defined) → returns the values
# ---------------------------------------------------------------------------


def test_cache_save_returns_values_as_tuple(tmp_path):
    # Arrange
    var1 = "test_string"
    var2 = 42
    var3 = [1, 2, 3, 4, 5]
    # Act
    result = cache("test_id", "var1", "var2", "var3", cache_root=tmp_path)
    # Assert
    assert result == ("test_string", 42, [1, 2, 3, 4, 5])


def test_cache_save_writes_pickle_file(tmp_path):
    # Arrange
    var1 = "test_string"
    # Act
    cache("test_id", "var1", cache_root=tmp_path)
    # Assert
    assert (tmp_path / "test_id.pkl").exists()


def test_cache_creates_intermediate_directories(tmp_path):
    # Arrange
    nested = tmp_path / "nested" / "dirs"
    var1 = "x"
    # Act
    cache("dir_test", "var1", cache_root=nested)
    # Assert
    assert (nested / "dir_test.pkl").exists()


# ---------------------------------------------------------------------------
# Load (some vars not defined) → reads back from cache
# ---------------------------------------------------------------------------


def test_cache_load_returns_saved_string(tmp_path):
    # Arrange
    var1 = "test_string"
    cache("test_id", "var1", cache_root=tmp_path)
    del var1
    # Act
    (loaded,) = cache("test_id", "var1", cache_root=tmp_path)
    # Assert
    assert loaded == "test_string"


def test_cache_load_returns_saved_int(tmp_path):
    # Arrange
    var2 = 42
    cache("test_id", "var2", cache_root=tmp_path)
    del var2
    # Act
    (loaded,) = cache("test_id", "var2", cache_root=tmp_path)
    # Assert
    assert loaded == 42


def test_cache_load_returns_saved_list(tmp_path):
    # Arrange
    var3 = [1, 2, 3, 4, 5]
    cache("test_id", "var3", cache_root=tmp_path)
    del var3
    # Act
    (loaded,) = cache("test_id", "var3", cache_root=tmp_path)
    # Assert
    assert loaded == [1, 2, 3, 4, 5]


def test_cache_overwrites_existing_data(tmp_path):
    # Arrange
    var1 = "original"
    cache("overwrite_test", "var1", cache_root=tmp_path)
    var1 = "updated"
    cache("overwrite_test", "var1", cache_root=tmp_path)
    del var1
    # Act
    (loaded,) = cache("overwrite_test", "var1", cache_root=tmp_path)
    # Assert
    assert loaded == "updated"


# ---------------------------------------------------------------------------
# Numpy round-trip
# ---------------------------------------------------------------------------


def test_cache_numpy_array_round_trip_preserves_values(tmp_path):
    # Arrange
    arr1 = np.ones((3, 3))
    cache("numpy_test", "arr1", cache_root=tmp_path)
    del arr1
    # Act
    (loaded,) = cache("numpy_test", "arr1", cache_root=tmp_path)
    # Assert
    assert np.array_equal(loaded, np.ones((3, 3)))


def test_cache_numpy_array_round_trip_preserves_shape(tmp_path):
    # Arrange
    arr2 = np.zeros((10, 5))
    cache("numpy_shape", "arr2", cache_root=tmp_path)
    del arr2
    # Act
    (loaded,) = cache("numpy_shape", "arr2", cache_root=tmp_path)
    # Assert
    assert loaded.shape == (10, 5)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


def test_cache_missing_file_with_undefined_vars_raises(tmp_path):
    # Arrange
    # Act
    ctx = pytest.raises(ValueError, match="Cache file not found")
    # Assert
    with ctx:
        cache("nonexistent_id", "var1", "var2", cache_root=tmp_path)


# ---------------------------------------------------------------------------
# Complex objects
# ---------------------------------------------------------------------------


def test_cache_dict_round_trip(tmp_path):
    # Arrange
    dict_var = {"a": 1, "b": [2, 3], "c": {"nested": True}}
    cache("complex_test", "dict_var", cache_root=tmp_path)
    del dict_var
    # Act
    (loaded,) = cache("complex_test", "dict_var", cache_root=tmp_path)
    # Assert
    assert loaded == {"a": 1, "b": [2, 3], "c": {"nested": True}}


def test_cache_set_round_trip(tmp_path):
    # Arrange
    set_var = {1, 2, 3, 4, 5}
    cache("complex_set", "set_var", cache_root=tmp_path)
    del set_var
    # Act
    (loaded,) = cache("complex_set", "set_var", cache_root=tmp_path)
    # Assert
    assert loaded == {1, 2, 3, 4, 5}


def test_cache_none_value_round_trip(tmp_path):
    # Arrange
    var1 = None
    cache("none_test", "var1", cache_root=tmp_path)
    del var1
    # Act
    (loaded,) = cache("none_test", "var1", cache_root=tmp_path)
    # Assert
    assert loaded is None


# ---------------------------------------------------------------------------
# Multiple IDs are isolated
# ---------------------------------------------------------------------------


def test_cache_multiple_ids_keep_first(tmp_path):
    # Arrange
    data1 = "first"
    cache("id1", "data1", cache_root=tmp_path)
    data1 = "second"
    cache("id2", "data1", cache_root=tmp_path)
    del data1
    # Act
    (loaded,) = cache("id1", "data1", cache_root=tmp_path)
    # Assert
    assert loaded == "first"


def test_cache_multiple_ids_keep_second(tmp_path):
    # Arrange
    data1 = "first"
    cache("id1", "data1", cache_root=tmp_path)
    data1 = "second"
    cache("id2", "data1", cache_root=tmp_path)
    del data1
    # Act
    (loaded,) = cache("id2", "data1", cache_root=tmp_path)
    # Assert
    assert loaded == "second"


# ---------------------------------------------------------------------------
# Special-character IDs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "test_id",
    [
        "test-with-dash",
        "test_with_underscore",
        "test.with.dot",
        "test@with@at",
    ],
)
def test_cache_special_character_id_round_trip(tmp_path, test_id):
    # Arrange
    data = f"data_for_{test_id}"
    cache(test_id, "data", cache_root=tmp_path)
    del data
    # Act
    (loaded,) = cache(test_id, "data", cache_root=tmp_path)
    # Assert
    assert loaded == f"data_for_{test_id}"


# ---------------------------------------------------------------------------
# Caller-frame access — verifies it reads inner-function locals
# ---------------------------------------------------------------------------


def test_cache_reads_caller_frame_locals(tmp_path):
    # Arrange
    def inner():
        inner_var1 = "inner"
        inner_var2 = 123
        return cache("frame_test", "inner_var1", "inner_var2", cache_root=tmp_path)

    # Act
    result = inner()
    # Assert
    assert result == ("inner", 123)


# ---------------------------------------------------------------------------
# Empty args
# ---------------------------------------------------------------------------


def test_cache_empty_args_returns_empty_tuple(tmp_path):
    # Arrange
    # (nothing to set up)
    # Act
    result = cache("empty_test", cache_root=tmp_path)
    # Assert
    assert result == ()
