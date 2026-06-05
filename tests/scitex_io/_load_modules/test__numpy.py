#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:26:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__numpy.py

"""Tests for NumPy file loading functionality.

This module tests the _load_npy function and its helpers from scitex_io._load_modules._numpy,
which handle loading NPY and NPZ files with proper handling of single vs multiple arrays.
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
import numpy as np


def test_load_npy_basic_array_round_trips():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array = np.array([1, 2, 3, 4, 5])
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_array)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert np.array_equal(loaded_array, test_array)
    finally:
        os.unlink(temp_path)


def test_load_npy_2d_round_trips_values():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array_2d = np.random.rand(10, 20)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_array_2d)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert np.allclose(loaded_array, test_array_2d)
    finally:
        os.unlink(temp_path)


def test_load_npy_2d_round_trips_shape():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array_2d = np.random.rand(10, 20)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_array_2d)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert loaded_array.shape == (10, 20)
    finally:
        os.unlink(temp_path)


def test_load_npy_3d_round_trips_values():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array_3d = np.random.rand(5, 10, 15)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_array_3d)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert np.allclose(loaded_array, test_array_3d)
    finally:
        os.unlink(temp_path)


def test_load_npz_single_array_returns_array_directly():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array = np.array([[1, 2, 3], [4, 5, 6]])
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        np.savez(f.name, test_array)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert isinstance(loaded_array, np.ndarray)
    finally:
        os.unlink(temp_path)


def test_load_npz_single_array_round_trips_values():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_array = np.array([[1, 2, 3], [4, 5, 6]])
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        np.savez(f.name, test_array)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert np.array_equal(loaded_array, test_array)
    finally:
        os.unlink(temp_path)


def test_load_npz_multiple_arrays_exposes_files_attribute():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    array1 = np.array([1, 2, 3])
    array2 = np.array([[4, 5], [6, 7]])
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        np.savez(f.name, first=array1, second=array2)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_npy(temp_path)
        # Assert
        assert set(loaded_data.files) == {"first", "second"}
    finally:
        os.unlink(temp_path)


def test_load_npz_multiple_arrays_first_array_round_trips():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    array1 = np.array([1, 2, 3])
    array2 = np.array([[4, 5], [6, 7]])
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        np.savez(f.name, first=array1, second=array2)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_npy(temp_path)
        # Assert
        assert np.array_equal(loaded_data["first"], array1)
    finally:
        os.unlink(temp_path)


def test_load_npy_object_array_round_trips_dict_element():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_data = np.array([{"key": "value"}, [1, 2, 3], "string"], dtype=object)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_data)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_npy(temp_path)
        # Assert
        assert loaded_data[0] == {"key": "value"}
    finally:
        os.unlink(temp_path)


def test_load_npy_object_array_round_trips_list_element():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    test_data = np.array([{"key": "value"}, [1, 2, 3], "string"], dtype=object)
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, test_data)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_npy(temp_path)
        # Assert
        assert loaded_data[1] == [1, 2, 3]
    finally:
        os.unlink(temp_path)


def test_load_npy_invalid_txt_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    # Act
    ctx = pytest.raises(ValueError, match="File must have .npy or .npz extension")
    # Assert
    with ctx:
        _load_npy("test.txt")


def test_load_npy_invalid_mat_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    # Act
    ctx = pytest.raises(ValueError, match="File must have .npy or .npz extension")
    # Assert
    with ctx:
        _load_npy("/path/to/file.mat")


def test_load_npy_nonexistent_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_npy("/nonexistent/path/file.npy")


def test_load_npy_structured_array_dtype_round_trips():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    dt = np.dtype([("name", "U10"), ("age", "i4"), ("weight", "f4")])
    structured_array = np.array(
        [("Alice", 25, 55.5), ("Bob", 30, 70.2), ("Charlie", 35, 80.1)], dtype=dt
    )
    with tempfile.NamedTemporaryFile(suffix=".npy", delete=False) as f:
        np.save(f.name, structured_array)
        temp_path = f.name
    try:
        # Act
        loaded_array = _load_npy(temp_path)
        # Assert
        assert loaded_array.dtype == dt
    finally:
        os.unlink(temp_path)


def test_load_npz_compressed_array_round_trips():
    # Arrange
    from scitex_io._load_modules._numpy import _load_npy

    large_array = np.random.rand(100, 100)
    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as f:
        np.savez_compressed(f.name, data=large_array)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_npy(temp_path)
        # Assert
        assert np.allclose(loaded_data["data"], large_array)
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
