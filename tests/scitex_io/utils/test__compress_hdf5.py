#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io.utils._compress_hdf5.compress_hdf5.

Each test builds a small .h5 file, re-compresses it with gzip, and
asserts one specific aspect of the result. h5py is an optional
dependency, so the whole module is skipped if it is absent.
"""

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

from scitex_io import compress_hdf5 as compress_hdf5_public
from scitex_io.utils._compress_hdf5 import compress_hdf5


def _write_sample_h5(path):
    with h5py.File(path, "w") as f:
        f.attrs["title"] = "sample"
        f.create_dataset("zeros", data=np.zeros((2_000, 50), dtype="float64"))
        grp = f.create_group("nested")
        grp.attrs["note"] = "grp"
        grp.create_dataset("ramp", data=np.arange(1_000, dtype="int32"))


def test_public_import_matches_module_function():
    # Arrange
    expected = compress_hdf5
    # Act
    actual = compress_hdf5_public
    # Assert
    assert actual is expected


def test_compress_returns_output_path(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    returned = compress_hdf5(str(src), str(out), compression_level=4)
    # Assert
    assert returned == str(out)


def test_compress_creates_output_file(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out), compression_level=4)
    # Assert
    assert out.exists()


def test_compress_default_output_name(tmp_path):
    # Arrange
    src = tmp_path / "data.h5"
    _write_sample_h5(src)
    # Act
    returned = compress_hdf5(str(src))
    # Assert
    assert returned == str(tmp_path / "data.compressed.h5")


def test_compress_preserves_top_level_dataset(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out))
    # Assert
    with h5py.File(out, "r") as f:
        assert np.array_equal(f["zeros"][()], np.zeros((2_000, 50)))


def test_compress_preserves_nested_dataset(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out))
    # Assert
    with h5py.File(out, "r") as f:
        assert np.array_equal(f["nested/ramp"][()], np.arange(1_000, dtype="int32"))


def test_compress_preserves_file_attribute(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out))
    # Assert
    with h5py.File(out, "r") as f:
        assert f.attrs["title"] == "sample"


def test_compress_preserves_group_attribute(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out))
    # Assert
    with h5py.File(out, "r") as f:
        assert f["nested"].attrs["note"] == "grp"


def test_compress_applies_gzip_filter(tmp_path):
    # Arrange
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    _write_sample_h5(src)
    # Act
    compress_hdf5(str(src), str(out), compression_level=9)
    # Assert
    with h5py.File(out, "r") as f:
        assert f["zeros"].compression == "gzip"


def test_compress_shrinks_compressible_data(tmp_path):
    # Arrange — zeros compress dramatically with gzip.
    src = tmp_path / "in.h5"
    out = tmp_path / "out.h5"
    with h5py.File(src, "w") as f:
        f.create_dataset("zeros", data=np.zeros((5_000, 100), dtype="float64"))
    # Act
    compress_hdf5(str(src), str(out))
    # Assert
    assert out.stat().st_size < src.stat().st_size
