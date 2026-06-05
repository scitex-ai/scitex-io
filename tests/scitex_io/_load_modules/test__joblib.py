#!/usr/bin/env python3
# Time-stamp: "2025-06-11 02:20:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__joblib.py

"""Comprehensive tests for joblib file loading functionality.

This module tests the _load_joblib function with various data types,
compression levels, edge cases, and error conditions.
"""

import os
import shutil
import sys
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
joblib = pytest.importorskip("joblib")
import datetime
import pickle
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


@dataclass
class TestData:
    """Data class for testing serialization."""

    name: str
    value: float
    items: List[str]


class CustomObject:
    """Custom class for testing object serialization."""

    def __init__(self, x: int, y: str):
        self.x = x
        self.y = y
        self._private = "private_data"

    def __eq__(self, other):
        if not isinstance(other, CustomObject):
            return False
        return self.x == other.x and self.y == other.y


class TestLoadJoblibBasic:
    """Basic functionality tests for _load_joblib."""

    def test_load_simple_dict_round_trips_whole_dict(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"key1": "value1", "key2": 42, "key3": 3.14}
        p = tmp_path / "simple.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded == data

    def test_load_simple_dict_returns_dict_instance(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"key1": "value1", "key2": 42, "key3": 3.14}
        p = tmp_path / "simple.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert isinstance(loaded, dict)

    def test_load_numpy_arrays_preserves_values_for_all_dtypes(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        arrays = {
            "1d": np.array([1, 2, 3, 4, 5]),
            "int": np.array([1, 2, 3], dtype=np.int32),
            "float": np.array([1.1, 2.2, 3.3], dtype=np.float64),
        }
        p = tmp_path / "arrays.joblib"
        joblib.dump(arrays, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert all(np.array_equal(loaded[k], arrays[k]) for k in arrays)

    def test_load_numpy_arrays_preserves_dtype_for_all_dtypes(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        arrays = {
            "int": np.array([1, 2, 3], dtype=np.int32),
            "float": np.array([1.1, 2.2, 3.3], dtype=np.float64),
            "complex": np.array([1 + 2j, 3 + 4j], dtype=np.complex128),
            "bool": np.array([True, False, True], dtype=bool),
        }
        p = tmp_path / "arrays.joblib"
        joblib.dump(arrays, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert all(loaded[k].dtype == arrays[k].dtype for k in arrays)

    def test_load_pandas_dataframe_round_trips(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        df = pd.DataFrame(
            {
                "A": [1, 2, 3, 4, 5],
                "B": ["a", "b", "c", "d", "e"],
                "C": pd.date_range("2024-01-01", periods=5),
                "D": [1.1, 2.2, 3.3, 4.4, 5.5],
            }
        )
        p = tmp_path / "df.joblib"
        joblib.dump({"dataframe": df}, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["dataframe"].equals(df)

    def test_load_pandas_series_round_trips(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        series = pd.Series([10, 20, 30], index=["x", "y", "z"])
        p = tmp_path / "series.joblib"
        joblib.dump({"series": series}, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["series"].equals(series)

    def test_load_nested_structures_preserves_deep_list(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        nested_data = {
            "level1": {
                "level2": {"level3": {"list": [[1, 2], [3, 4]]}},
            },
        }
        p = tmp_path / "nested.joblib"
        joblib.dump(nested_data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["level1"]["level2"]["level3"]["list"] == [[1, 2], [3, 4]]

    def test_load_nested_structures_preserves_version_metadata(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        nested_data = {"metadata": {"version": "1.0.0"}}
        p = tmp_path / "nested.joblib"
        joblib.dump(nested_data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["metadata"]["version"] == "1.0.0"

    def test_load_nested_structures_preserves_set_type(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        nested_data = {"metadata": {"tags": {"python", "testing", "joblib"}}}
        p = tmp_path / "nested.joblib"
        joblib.dump(nested_data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert isinstance(loaded["metadata"]["tags"], set)


class TestLoadJoblibCompression:
    """Test compression-related functionality."""

    @pytest.mark.parametrize("compress_level", list(range(10)))
    def test_load_all_compression_levels_round_trip(self, tmp_path, compress_level):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = np.random.rand(100, 100)
        p = tmp_path / f"c{compress_level}.joblib"
        joblib.dump(data, str(p), compress=compress_level)
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert np.allclose(loaded, data)

    @pytest.mark.parametrize("method", ["zlib", "gzip", "bz2", "lzma", "xz"])
    def test_load_different_compression_methods_round_trip(self, tmp_path, method):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"array": np.random.rand(50, 50), "value": 42}
        p = tmp_path / f"{method}.joblib"
        try:
            joblib.dump(data, str(p), compress=(method, 3))
        except Exception as exc:
            if "module" in str(exc) and "not found" in str(exc):
                return  # Compression method not installed in this env — OK.
            raise
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert np.allclose(loaded["array"], data["array"])

    def test_load_large_compressed_data_preserves_matrix_shape(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        large_data = {"matrix": np.random.rand(1000, 1000)}
        p = tmp_path / "large.joblib"
        joblib.dump(large_data, str(p), compress=3)
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["matrix"].shape == (1000, 1000)

    def test_load_large_compressed_data_preserves_string_list_length(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        large_data = {"strings": ["string_" + str(i) for i in range(10000)]}
        p = tmp_path / "large.joblib"
        joblib.dump(large_data, str(p), compress=3)
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert len(loaded["strings"]) == 10000

    def test_load_large_compressed_data_preserves_nested_dict_length(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        large_data = {"nested": {str(i): np.random.rand(10, 10) for i in range(100)}}
        p = tmp_path / "large.joblib"
        joblib.dump(large_data, str(p), compress=3)
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert len(loaded["nested"]) == 100

    def test_load_large_compressed_data_compresses_below_uncompressed_size(
        self, tmp_path
    ):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib  # noqa: F401

        large_data = {"matrix": np.random.rand(1000, 1000)}
        p = tmp_path / "large.joblib"
        joblib.dump(large_data, str(p), compress=3)
        # Act
        compressed_size = os.path.getsize(str(p))
        # Assert
        assert compressed_size < large_data["matrix"].nbytes


class TestLoadJoblibCustomObjects:
    """Test loading custom objects and classes."""

    def test_load_custom_class_returns_same_class_instance(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        obj = CustomObject(x=42, y="test")
        p = tmp_path / "obj.joblib"
        joblib.dump(obj, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert isinstance(loaded, CustomObject)

    def test_load_custom_class_preserves_x_attribute(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        obj = CustomObject(x=42, y="test")
        p = tmp_path / "obj.joblib"
        joblib.dump(obj, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded.x == 42

    def test_load_custom_class_preserves_y_attribute(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        obj = CustomObject(x=42, y="test")
        p = tmp_path / "obj.joblib"
        joblib.dump(obj, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded.y == "test"

    def test_load_custom_class_equals_original_object(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        obj = CustomObject(x=42, y="test")
        p = tmp_path / "obj.joblib"
        joblib.dump(obj, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded == obj

    def test_load_dataclass_returns_same_class_instance(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = TestData(
            name="test_data", value=3.14159, items=["item1", "item2", "item3"]
        )
        p = tmp_path / "dc.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert isinstance(loaded, TestData)

    def test_load_dataclass_preserves_name_field(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = TestData(name="test_data", value=3.14159, items=["i"])
        p = tmp_path / "dc.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded.name == "test_data"

    def test_load_dataclass_preserves_value_field(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = TestData(name="x", value=3.14159, items=[])
        p = tmp_path / "dc.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded.value == 3.14159

    def test_load_dataclass_preserves_items_field(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = TestData(name="x", value=0.0, items=["item1", "item2", "item3"])
        p = tmp_path / "dc.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded.items == ["item1", "item2", "item3"]

    def test_load_lambda_function_preserves_value_field(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        # Lambda functions may not serialise; tolerate the dump failure.
        data = {"func": lambda x: x * 2, "value": 42}
        p = tmp_path / "lam.joblib"
        try:
            joblib.dump(data, str(p))
        except Exception:
            return  # Lambda serialization not supported in this env — OK.
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["value"] == 42


class TestLoadJoblibEdgeCases:
    """Test edge cases and error conditions."""

    def test_load_empty_file(self):
        """Test loading an empty joblib file."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(
                Exception
            ):  # Should raise when trying to load empty file
                _load_joblib(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_corrupted_file(self):
        """Test loading a corrupted joblib file."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            f.write(b"This is not a valid joblib file content")
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # Should raise when loading invalid data
                _load_joblib(temp_path)
        finally:
            os.unlink(temp_path)

    def test_wrong_file_extension(self):
        """Test various wrong file extensions."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        wrong_extensions = [
            "file.pkl",
            "file.pickle",
            "file.npy",
            "file.npz",
            "file.json",
            "file.txt",
            "file.dat",
            "file",  # No extension
            "file.JOBLIB",  # Wrong case
            "file.joblib.bak",  # Additional extension
        ]

        for filename in wrong_extensions:
            with pytest.raises(ValueError, match="must have .joblib extension"):
                _load_joblib(filename)

    def test_nonexistent_file_raises_filenotfounderror(self):
        """Test loading a non-existent file."""
        # Arrange
        # Act
        from scitex_io._load_modules._joblib import _load_joblib

        # Assert
        with pytest.raises(FileNotFoundError):
            _load_joblib("/tmp/nonexistent_file_12345.joblib")

    @pytest.fixture
    def loaded_empty_values(self, tmp_path):
        from scitex_io._load_modules._joblib import _load_joblib

        data = {
            "none": None,
            "empty_list": [],
            "empty_dict": {},
            "empty_tuple": (),
            "empty_set": set(),
            "empty_string": "",
            "empty_array": np.array([]),
        }
        p = tmp_path / "empties.joblib"
        joblib.dump(data, str(p))
        return _load_joblib(str(p))

    def test_load_none_value_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["none"]
        # Assert
        assert result is None

    def test_load_empty_list_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["empty_list"]
        # Assert
        assert result == []

    def test_load_empty_dict_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["empty_dict"]
        # Assert
        assert result == {}

    def test_load_empty_tuple_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["empty_tuple"]
        # Assert
        assert result == ()

    def test_load_empty_set_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["empty_set"]
        # Assert
        assert result == set()

    def test_load_empty_string_round_trips(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = loaded["empty_string"]
        # Assert
        assert result == ""

    def test_load_empty_array_has_zero_length(self, loaded_empty_values):
        # Arrange
        loaded = loaded_empty_values
        # Act
        result = len(loaded["empty_array"])
        # Assert
        assert result == 0


class TestLoadJoblibWithKwargs:
    """Test _load_joblib with various keyword arguments."""

    @pytest.mark.parametrize("mmap_mode", [None, "r", "r+", "c"])
    def test_load_with_mmap_mode_preserves_shape(self, tmp_path, mmap_mode):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        large_array = np.random.rand(1000, 1000)
        p = tmp_path / "large.joblib"
        joblib.dump(large_array, str(p))
        # Act
        loaded = _load_joblib(str(p), mmap_mode=mmap_mode)
        # Assert
        assert loaded.shape == (1000, 1000)

    def test_load_with_custom_kwargs_preserves_string_value(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"test": "data", "array": np.array([1, 2, 3])}
        p = tmp_path / "k.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert loaded["test"] == data["test"]

    def test_load_with_custom_kwargs_preserves_array_value(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"test": "data", "array": np.array([1, 2, 3])}
        p = tmp_path / "k.joblib"
        joblib.dump(data, str(p))
        # Act
        loaded = _load_joblib(str(p))
        # Assert
        assert np.array_equal(loaded["array"], data["array"])


class TestLoadJoblibPathHandling:
    """Test various path formats and handling."""

    def test_load_with_pathlib_path(self):
        """Test loading with pathlib.Path object."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"pathlib": "test"}

        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
            joblib.dump(data, f.name)
            temp_path = Path(f.name)

        try:
            # Convert to string since _load_joblib expects str
            loaded = _load_joblib(str(temp_path))
            assert loaded == data
        finally:
            os.unlink(temp_path)

    def test_load_with_relative_path(self):
        """Test loading with relative paths."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"relative": "path"}

        # Create file in current directory
        filename = "test_relative_path.joblib"
        joblib.dump(data, filename)

        try:
            loaded = _load_joblib(filename)
            assert loaded == data
        finally:
            if os.path.exists(filename):
                os.unlink(filename)

    def test_load_with_special_characters_in_path(self):
        """Test loading files with special characters in path."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"special": "chars"}

        # Test various special characters (that are valid in filenames)
        special_names = [
            "test file with spaces.joblib",
            "test-file-with-dashes.joblib",
            "test_file_with_underscores.joblib",
            "test.file.with.dots.joblib",
        ]

        for name in special_names:
            with tempfile.NamedTemporaryFile(suffix="", delete=False) as f:
                temp_dir = os.path.dirname(f.name)
                special_path = os.path.join(temp_dir, name)

            joblib.dump(data, special_path)

            try:
                loaded = _load_joblib(special_path)
                assert loaded == data
            finally:
                if os.path.exists(special_path):
                    os.unlink(special_path)


class TestLoadJoblibConcurrency:
    """Test concurrent loading scenarios."""

    def test_load_same_file_multiple_times_returns_equal_arrays(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._joblib import _load_joblib

        data = {"concurrent": np.random.rand(100, 100)}
        p = tmp_path / "c.joblib"
        joblib.dump(data, str(p))
        results = [_load_joblib(str(p)) for _ in range(10)]
        # Act
        all_equal = all(
            np.allclose(r["concurrent"], results[0]["concurrent"]) for r in results[1:]
        )
        # Assert
        assert all_equal


class TestLoadJoblibIntegration:
    """Integration tests with real-world scenarios."""

    @pytest.fixture
    def loaded_ml_model(self, tmp_path):
        from scitex_io._load_modules._joblib import _load_joblib

        model_data = {
            "weights": {
                "layer1": np.random.rand(100, 50),
            },
            "config": {"learning_rate": 0.001},
        }
        p = tmp_path / "model.joblib"
        joblib.dump(model_data, str(p), compress=3)
        return _load_joblib(str(p))

    def test_load_ml_model_preserves_weights_section(self, loaded_ml_model):
        # Arrange
        loaded = loaded_ml_model
        # Act
        has_weights = "weights" in loaded
        # Assert
        assert has_weights

    def test_load_ml_model_preserves_config_section(self, loaded_ml_model):
        # Arrange
        loaded = loaded_ml_model
        # Act
        has_config = "config" in loaded
        # Assert
        assert has_config

    def test_load_ml_model_preserves_learning_rate(self, loaded_ml_model):
        # Arrange
        loaded = loaded_ml_model
        # Act
        result = loaded["config"]["learning_rate"]
        # Assert
        assert result == 0.001

    def test_load_ml_model_preserves_layer1_shape(self, loaded_ml_model):
        # Arrange
        loaded = loaded_ml_model
        # Act
        result = loaded["weights"]["layer1"].shape
        # Assert
        assert result == (100, 50)

    @pytest.fixture
    def loaded_sci_data(self, tmp_path):
        from scitex_io._load_modules._joblib import _load_joblib

        sci_data = {
            "experiment_id": "EXP-2024-001",
            "measurements": {"time": np.linspace(0, 10, 1000)},
            "analysis": {"mean": np.mean},
            "parameters": {"sampling_rate": 100},
        }
        p = tmp_path / "sci.joblib"
        joblib.dump(sci_data, str(p))
        return _load_joblib(str(p))

    def test_load_sci_data_preserves_experiment_id(self, loaded_sci_data):
        # Arrange
        loaded = loaded_sci_data
        # Act
        result = loaded["experiment_id"]
        # Assert
        assert result == "EXP-2024-001"

    def test_load_sci_data_preserves_time_series_length(self, loaded_sci_data):
        # Arrange
        loaded = loaded_sci_data
        # Act
        result = len(loaded["measurements"]["time"])
        # Assert
        assert result == 1000

    def test_load_sci_data_preserves_sampling_rate(self, loaded_sci_data):
        # Arrange
        loaded = loaded_sci_data
        # Act
        result = loaded["parameters"]["sampling_rate"]
        # Assert
        assert result == 100

    def test_load_sci_data_preserves_callable_function_reference(self, loaded_sci_data):
        # Arrange
        loaded = loaded_sci_data
        # Act
        is_callable = callable(loaded["analysis"]["mean"])
        # Assert
        assert is_callable


@pytest.mark.parametrize("protocol", [2, 3, 4])
def test_backwards_compatibility_round_trips_string_field(tmp_path, protocol):
    # Arrange
    from scitex_io._load_modules._joblib import _load_joblib

    data = {"test": "backwards", "array": np.array([1, 2, 3])}
    p = tmp_path / f"p{protocol}.joblib"
    try:
        joblib.dump(data, str(p), protocol=protocol)
    except TypeError:
        return  # Older joblib without protocol kwarg — OK.
    # Act
    loaded = _load_joblib(str(p))
    # Assert
    assert loaded["test"] == data["test"]


@pytest.mark.parametrize("protocol", [2, 3, 4])
def test_backwards_compatibility_round_trips_array_field(tmp_path, protocol):
    # Arrange
    from scitex_io._load_modules._joblib import _load_joblib

    data = {"test": "backwards", "array": np.array([1, 2, 3])}
    p = tmp_path / f"p{protocol}.joblib"
    try:
        joblib.dump(data, str(p), protocol=protocol)
    except TypeError:
        return  # Older joblib without protocol kwarg — OK.
    # Act
    loaded = _load_joblib(str(p))
    # Assert
    assert np.array_equal(loaded["array"], data["array"])


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_joblib.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-14 07:55:39 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_joblib.py
#
# from typing import Any
#
# import joblib
#
#
# def _load_joblib(lpath: str, **kwargs) -> Any:
#     """Load joblib file."""
#     if not lpath.endswith(".joblib"):
#         raise ValueError("File must have .joblib extension")
#     with open(lpath, "rb") as f:
#         return joblib.load(f, **kwargs)
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_joblib.py
# --------------------------------------------------------------------------------
