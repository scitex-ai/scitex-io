#!/usr/bin/env python3
"""Real tests for scitex_io._save_modules._numpy."""

import numpy as np
import pytest

from scitex_io._save_modules._numpy import _save_npy, _save_npz


def test_save_npy_int(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    p = str(tmp_path / "x.npy")
    arr = np.arange(10, dtype=np.int32)
    _save_npy(arr, p)
    # Act
    back = np.load(p)
    # Assert
    assert np.array_equal(back, arr)


def test_save_npy_float(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    p = str(tmp_path / "f.npy")
    arr = np.linspace(0, 1, 7)
    # Act
    _save_npy(arr, p)
    # Assert
    assert np.allclose(np.load(p), arr)


def test_save_npy_object(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "o.npy")
    arr = np.array([{"a": 1}, {"b": 2}], dtype=object)
    _save_npy(arr, p)
    # Act
    # Act
    back = np.load(p, allow_pickle=True)
    # Assert
    # Assert
    assert back[0] == {"a": 1}


def test_save_npz_dict_np_array_equal_z_a_np_arange_3(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "x.npz")
    _save_npz({"a": np.arange(3), "b": np.eye(2)}, p)
    # Act
    z = np.load(p)
    # Act
    # Assert
    # Assert
    assert np.array_equal(z["a"], np.arange(3))


def test_save_npz_dict_np_array_equal_z_b_np_eye_2(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "x.npz")
    _save_npz({"a": np.arange(3), "b": np.eye(2)}, p)
    # Act
    z = np.load(p)
    # Act
    # Assert
    # Assert
    assert np.array_equal(z["b"], np.eye(2))




def test_save_npz_list_np_array_equal_z_0_np_arange_3(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "y.npz")
    _save_npz([np.arange(3), np.arange(4)], p)
    # Act
    z = np.load(p)
    # Act
    # Assert
    # Assert
    assert np.array_equal(z["0"], np.arange(3))


def test_save_npz_list_np_array_equal_z_1_np_arange_4(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "y.npz")
    _save_npz([np.arange(3), np.arange(4)], p)
    # Act
    z = np.load(p)
    # Act
    # Assert
    # Assert
    assert np.array_equal(z["1"], np.arange(4))




def test_save_npz_tuple(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    p = str(tmp_path / "t.npz")
    _save_npz((np.zeros(2), np.ones(2)), p)
    # Act
    z = np.load(p)
    # Assert
    assert np.array_equal(z["0"], np.zeros(2))


def test_save_npz_invalid_raises_raises_valueerror(tmp_path):
    # Arrange
    # Arrange
    # Act
    p = str(tmp_path / "bad.npz")
    # Act
    # Assert
    # Assert
    with pytest.raises(ValueError):
        _save_npz("not arrays", p)


def test_save_npz_invalid_raises_raises_valueerror(tmp_path):
    # Arrange
    # Arrange
    # Act
    p = str(tmp_path / "bad.npz")
    # Act
    # Assert
    # Assert
    with pytest.raises(ValueError):
        _save_npz([1, 2, 3], p)


