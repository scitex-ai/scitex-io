#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:35:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__pickle.py

"""Tests for pickle file loading functionality.

This module tests the _load_pickle function from scitex_io._load_modules._pickle,
which handles loading pickle files including gzip-compressed pickles.
"""

import gzip
import os
import pickle
import tempfile
from collections import OrderedDict, namedtuple
from datetime import date, datetime

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

# Define namedtuple at module level for pickling support
Point = namedtuple("Point", ["x", "y"])


def test_load_pickle_basic_returns_equal_dict():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    test_data = {"string": "Hello World", "integer": 42, "list": [1, 2, 3]}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(test_data, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data == test_data
    finally:
        os.unlink(temp_path)


def test_load_pickle_pickle_extension_returns_equal_list():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    test_data = ["item1", "item2", "item3"]
    with tempfile.NamedTemporaryFile(suffix=".pickle", delete=False) as f:
        pickle.dump(test_data, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data == test_data
    finally:
        os.unlink(temp_path)


def test_load_pickle_compressed_pkl_gz_round_trips():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    large_data = {f"key_{i}": list(range(10)) for i in range(20)}
    with tempfile.NamedTemporaryFile(suffix=".pkl.gz", delete=False) as f:
        with gzip.open(f.name, "wb") as gz:
            pickle.dump(large_data, gz)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data == large_data
    finally:
        os.unlink(temp_path)


def test_load_pickle_namedtuple_round_trips_x_field():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    point1 = Point(10, 20)
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump({"point": point1}, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data["point"].x == 10
    finally:
        os.unlink(temp_path)


def test_load_pickle_ordered_dict_round_trips_first_key():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    od = OrderedDict([("a", 1), ("b", 2), ("c", 3)])
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(od, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data["a"] == 1
    finally:
        os.unlink(temp_path)


def test_load_pickle_datetime_round_trips_year():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    dt = datetime(2024, 1, 15, 12, 30, 45)
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump({"dt": dt}, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data["dt"].year == 2024
    finally:
        os.unlink(temp_path)


def test_load_pickle_invalid_txt_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    # Act
    ctx = pytest.raises(
        ValueError, match="File must have .pkl, .pickle, or .pkl.gz extension"
    )
    # Assert
    with ctx:
        _load_pickle("test.txt")


def test_load_pickle_invalid_json_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    # Act
    ctx = pytest.raises(
        ValueError, match="File must have .pkl, .pickle, or .pkl.gz extension"
    )
    # Assert
    with ctx:
        _load_pickle("/path/to/file.json")


def test_load_pickle_corrupted_file_raises_unpicklingerror():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        f.write(b"This is not valid pickle data")
        temp_path = f.name
    try:
        # Act
        ctx = pytest.raises(pickle.UnpicklingError)
        # Assert
        with ctx:
            _load_pickle(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_pickle_nonexistent_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_pickle("/nonexistent/path/file.pkl")


def test_load_pickle_numpy_1d_array_round_trips():
    # Arrange
    import numpy as np

    from scitex_io._load_modules._pickle import _load_pickle

    numpy_data = {"array_1d": np.array([1, 2, 3, 4, 5])}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(numpy_data, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert np.array_equal(loaded_data["array_1d"], numpy_data["array_1d"])
    finally:
        os.unlink(temp_path)


def test_load_pickle_numpy_3d_array_shape_round_trips():
    # Arrange
    import numpy as np

    from scitex_io._load_modules._pickle import _load_pickle

    numpy_data = {"array_3d": np.ones((5, 5, 5))}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(numpy_data, f)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data["array_3d"].shape == (5, 5, 5)
    finally:
        os.unlink(temp_path)


@pytest.mark.parametrize("protocol", list(range(pickle.HIGHEST_PROTOCOL + 1)))
def test_load_pickle_round_trips_per_protocol(protocol):
    # Arrange
    from scitex_io._load_modules._pickle import _load_pickle

    test_data = {"protocol_test": True, "data": [1, 2, 3]}
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
        pickle.dump(test_data, f, protocol=protocol)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_pickle(temp_path)
        # Assert
        assert loaded_data == test_data
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
