#!/usr/bin/env python3
"""Real tests for scitex_io._save_modules._numpy."""

import numpy as np
import pytest

from scitex_io._save_modules._numpy import _save_npy, _save_npz


def test_save_npy_int(tmp_path):
    p = str(tmp_path / "x.npy")
    arr = np.arange(10, dtype=np.int32)
    _save_npy(arr, p)
    back = np.load(p)
    np.testing.assert_array_equal(back, arr)


def test_save_npy_float(tmp_path):
    p = str(tmp_path / "f.npy")
    arr = np.linspace(0, 1, 7)
    _save_npy(arr, p)
    np.testing.assert_allclose(np.load(p), arr)


def test_save_npy_object(tmp_path):
    p = str(tmp_path / "o.npy")
    arr = np.array([{"a": 1}, {"b": 2}], dtype=object)
    _save_npy(arr, p)
    back = np.load(p, allow_pickle=True)
    assert back[0] == {"a": 1}


def test_save_npz_dict(tmp_path):
    p = str(tmp_path / "x.npz")
    _save_npz({"a": np.arange(3), "b": np.eye(2)}, p)
    z = np.load(p)
    np.testing.assert_array_equal(z["a"], np.arange(3))
    np.testing.assert_array_equal(z["b"], np.eye(2))


def test_save_npz_list(tmp_path):
    p = str(tmp_path / "y.npz")
    _save_npz([np.arange(3), np.arange(4)], p)
    z = np.load(p)
    np.testing.assert_array_equal(z["0"], np.arange(3))
    np.testing.assert_array_equal(z["1"], np.arange(4))


def test_save_npz_tuple(tmp_path):
    p = str(tmp_path / "t.npz")
    _save_npz((np.zeros(2), np.ones(2)), p)
    z = np.load(p)
    np.testing.assert_array_equal(z["0"], np.zeros(2))


def test_save_npz_invalid_raises(tmp_path):
    p = str(tmp_path / "bad.npz")
    with pytest.raises(ValueError):
        _save_npz("not arrays", p)
    with pytest.raises(ValueError):
        _save_npz([1, 2, 3], p)
