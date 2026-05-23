#!/usr/bin/env python3
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__hdf5.py

"""Real-collaborator tests for ``_load_hdf5``.

All tests write a real HDF5 file under ``tmp_path`` and assert on the
loaded structure. Each test asserts exactly one behaviour.
"""

from __future__ import annotations

import pickle

import h5py
import numpy as np
import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


# ---------------------------------------------------------------------------
# Basic loading
# ---------------------------------------------------------------------------


@pytest.fixture
def basic_hdf5(tmp_path):
    path = tmp_path / "basic.hdf5"
    data = {"array": np.random.rand(10, 20), "scalar": 42}
    with h5py.File(path, "w") as hf:
        hf.create_dataset("array", data=data["array"])
        hf.create_dataset("scalar", data=data["scalar"])
    return path, data


def test_load_hdf5_basic_contains_array_key(basic_hdf5):
    """Loaded dict contains the ``array`` key."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = basic_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert "array" in loaded


def test_load_hdf5_basic_contains_scalar_key(basic_hdf5):
    """Loaded dict contains the ``scalar`` key."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = basic_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert "scalar" in loaded


def test_load_hdf5_basic_array_values_match(basic_hdf5):
    """Loaded array matches what was written."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, data = basic_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert np.allclose(loaded["array"], data["array"])


def test_load_hdf5_basic_scalar_value_matches(basic_hdf5):
    """Loaded scalar matches what was written."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = basic_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["scalar"] == 42


# ---------------------------------------------------------------------------
# Non-HDF5 file -> error
# ---------------------------------------------------------------------------


def test_load_hdf5_non_hdf5_file_raises(tmp_path):
    """Opening a non-HDF5 file raises an OS/IO/Value error."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path = tmp_path / "not_hdf5.txt"
    path.write_bytes(b"This is not an HDF5 file")
    # Act
    ctx = pytest.raises((OSError, IOError, ValueError))
    # Assert
    with ctx:
        _load_hdf5(str(path), max_retries=1)


# ---------------------------------------------------------------------------
# Nested group structures
# ---------------------------------------------------------------------------


@pytest.fixture
def nested_hdf5(tmp_path):
    path = tmp_path / "nested.h5"
    with h5py.File(path, "w") as hf:
        grp1 = hf.create_group("experiment")
        grp2 = grp1.create_group("trial_1")
        grp3 = grp1.create_group("trial_2")
        hf.create_dataset("metadata", data=np.array([1, 2, 3]))
        grp1.create_dataset(
            "conditions", data=np.array(["A", "B", "C"], dtype="S1")
        )
        grp2.create_dataset("data", data=np.ones((5, 5)))
        grp3.create_dataset("data", data=np.zeros((3, 3)))
    return path


def test_load_hdf5_nested_top_level_metadata(nested_hdf5):
    """Top-level ``metadata`` survives the load."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(nested_hdf5))
    # Assert
    assert "metadata" in loaded


def test_load_hdf5_nested_experiment_group(nested_hdf5):
    """Top-level group ``experiment`` is present."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(nested_hdf5))
    # Assert
    assert "experiment" in loaded


def test_load_hdf5_nested_experiment_is_dict(nested_hdf5):
    """A group is loaded as a dict."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(nested_hdf5))
    # Assert
    assert isinstance(loaded["experiment"], dict)


def test_load_hdf5_nested_trial_data_values_match(nested_hdf5):
    """Inner dataset values survive the round-trip."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(nested_hdf5))
    # Assert
    assert np.array_equal(loaded["experiment"]["trial_1"]["data"], np.ones((5, 5)))


# ---------------------------------------------------------------------------
# Numpy dtypes
# ---------------------------------------------------------------------------


@pytest.fixture
def dtypes_hdf5(tmp_path):
    test_data = {
        "int8": np.int8(42),
        "int64": np.int64(10000000000),
        "float32": np.float32(3.14159),
        "float64": np.float64(2.71828),
        "bool_true": np.bool_(True),
        "bool_false": np.bool_(False),
        "array_int": np.array([1, 2, 3, 4, 5], dtype=np.int32),
        "array_float": np.array([1.1, 2.2, 3.3], dtype=np.float64),
        "multidim_array": np.random.rand(3, 4, 5).astype(np.float32),
    }
    path = tmp_path / "dtypes.hdf5"
    with h5py.File(path, "w") as hf:
        for key, value in test_data.items():
            hf.create_dataset(key, data=value)
    return path, test_data


def test_load_hdf5_dtype_int8_value(dtypes_hdf5):
    """``int8`` scalar value round-trips."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["int8"] == 42


def test_load_hdf5_dtype_int64_value(dtypes_hdf5):
    """``int64`` scalar value round-trips."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["int64"] == 10000000000


def test_load_hdf5_dtype_float32_within_tolerance(dtypes_hdf5):
    """``float32`` scalar is within numerical tolerance."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert abs(loaded["float32"] - 3.14159) < 1e-5


def test_load_hdf5_dtype_bool_true_is_true(dtypes_hdf5):
    """``bool_true`` round-trips to True."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert bool(loaded["bool_true"]) is True


def test_load_hdf5_dtype_bool_false_is_false(dtypes_hdf5):
    """``bool_false`` round-trips to False."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert bool(loaded["bool_false"]) is False


def test_load_hdf5_dtype_array_int_values_match(dtypes_hdf5):
    """Integer arrays round-trip element-wise."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert np.array_equal(loaded["array_int"], [1, 2, 3, 4, 5])


def test_load_hdf5_dtype_multidim_array_shape_preserved(dtypes_hdf5):
    """Multidimensional arrays preserve their shape."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _ = dtypes_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["multidim_array"].shape == (3, 4, 5)


# ---------------------------------------------------------------------------
# Strings / bytes / unicode
# ---------------------------------------------------------------------------


@pytest.fixture
def strings_hdf5(tmp_path):
    string_data = "Hello, HDF5 World!"
    bytes_data = string_data.encode("utf-8")
    unicode_string = "Greek alpha"
    path = tmp_path / "strings.hdf5"
    with h5py.File(path, "w") as hf:
        hf.create_dataset("bytes_to_string", data=bytes_data)
        hf.create_dataset("unicode_string", data=unicode_string)
        string_array = np.array(["apple", "banana", "cherry"], dtype="S10")
        hf.create_dataset("string_array", data=string_array)
        vlen_string = h5py.special_dtype(vlen=str)
        hf.create_dataset(
            "vlen_string",
            data=["variable", "length", "strings"],
            dtype=vlen_string,
        )
    return path, string_data, unicode_string


def test_load_hdf5_bytes_dataset_decodes_to_str(strings_hdf5):
    """A bytes-typed dataset is decoded to ``str``."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, _ = strings_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert isinstance(loaded["bytes_to_string"], str)


def test_load_hdf5_bytes_dataset_value_matches(strings_hdf5):
    """Decoded bytes match the original text."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, string_data, _ = strings_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["bytes_to_string"] == string_data


def test_load_hdf5_unicode_string_preserved(strings_hdf5):
    """Unicode strings round-trip unchanged."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, unicode_string = strings_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["unicode_string"] == unicode_string


def test_load_hdf5_string_array_present(strings_hdf5):
    """The fixed-width string array key is present."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, _ = strings_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert "string_array" in loaded


def test_load_hdf5_vlen_string_present(strings_hdf5):
    """The variable-length string array key is present."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, _ = strings_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert "vlen_string" in loaded


# ---------------------------------------------------------------------------
# Pickled objects
# ---------------------------------------------------------------------------


@pytest.fixture
def pickled_hdf5(tmp_path):
    objs = {
        "list": [1, 2, 3, "hello", [4, 5]],
        "dict": {"key1": "value1", "key2": 42, "nested": {"a": 1}},
        "set": {1, 2, 3, 4, 5},
        "tuple": (1, "two", 3.0, [4, 5]),
    }
    path = tmp_path / "pickled.hdf5"
    with h5py.File(path, "w") as hf:
        for key, obj in objs.items():
            hf.create_dataset(f"pickled_{key}", data=np.void(pickle.dumps(obj)))
    return path, objs


@pytest.mark.parametrize("key", ["list", "dict", "set", "tuple"])
def test_load_hdf5_unpickles_void_dataset(pickled_hdf5, key):
    """A void-typed pickle payload is unpickled on load."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, objs = pickled_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded[f"pickled_{key}"] == objs[key]


# ---------------------------------------------------------------------------
# Large datasets
# ---------------------------------------------------------------------------


@pytest.fixture
def large_hdf5(tmp_path):
    large_1d = np.random.rand(100_000)
    large_2d = np.random.rand(500, 500)
    path = tmp_path / "large.hdf5"
    with h5py.File(path, "w") as hf:
        hf.create_dataset("large_1d", data=large_1d, compression="gzip")
        hf.create_dataset("large_2d", data=large_2d, compression="lzf")
        hf.create_dataset("chunked", data=np.ones((500, 500)), chunks=True)
    return path, large_1d, large_2d


def test_load_hdf5_large_1d_shape_preserved(large_hdf5):
    """A 1-D compressed array preserves its shape."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, large_1d, _ = large_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["large_1d"].shape == large_1d.shape


def test_load_hdf5_large_2d_shape_preserved(large_hdf5):
    """A 2-D compressed array preserves its shape."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, large_2d = large_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert loaded["large_2d"].shape == large_2d.shape


def test_load_hdf5_chunked_dataset_values_match(large_hdf5):
    """A chunked dataset round-trips element-wise."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, _, _ = large_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert np.array_equal(loaded["chunked"], np.ones((500, 500)))


def test_load_hdf5_large_1d_sample_values_match(large_hdf5):
    """Sampling the first 100 elements matches the original."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path, large_1d, _ = large_hdf5
    # Act
    loaded = _load_hdf5(str(path))
    # Assert
    assert np.array_equal(loaded["large_1d"][:100], large_1d[:100])


# ---------------------------------------------------------------------------
# Attributes / metadata smoke
# ---------------------------------------------------------------------------


@pytest.fixture
def attrs_hdf5(tmp_path):
    path = tmp_path / "attrs.hdf5"
    with h5py.File(path, "w") as hf:
        ds = hf.create_dataset("data", data=np.random.rand(10, 10))
        ds.attrs["units"] = "volts"
        grp = hf.create_group("experiment")
        grp.attrs["date"] = "2023-01-01"
        grp.create_dataset("results", data=[1, 2, 3, 4, 5])
        hf.attrs["version"] = "1.0"
    return path


def test_load_hdf5_attrs_root_dataset_present(attrs_hdf5):
    """A dataset alongside attributes still loads."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(attrs_hdf5))
    # Assert
    assert "data" in loaded


def test_load_hdf5_attrs_nested_group_present(attrs_hdf5):
    """A group with attributes still loads its children."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(attrs_hdf5))
    # Assert
    assert "results" in loaded["experiment"]


# ---------------------------------------------------------------------------
# Empty groups / datasets
# ---------------------------------------------------------------------------


@pytest.fixture
def empty_hdf5(tmp_path):
    path = tmp_path / "empty.hdf5"
    with h5py.File(path, "w") as hf:
        hf.create_group("empty_group")
        grp = hf.create_group("group_with_empty")
        grp.create_dataset("empty_array", data=np.array([]))
        grp.create_dataset("empty_2d", shape=(0, 5))
        hf.create_dataset("normal_data", data=[1, 2, 3])
    return path


def test_load_hdf5_empty_group_loads_as_empty_dict(empty_hdf5):
    """An empty group loads as an empty dict."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(empty_hdf5))
    # Assert
    assert loaded["empty_group"] == {}


def test_load_hdf5_empty_array_has_zero_size(empty_hdf5):
    """A zero-length array has size 0."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(empty_hdf5))
    # Assert
    assert loaded["group_with_empty"]["empty_array"].size == 0


def test_load_hdf5_empty_2d_preserves_shape(empty_hdf5):
    """A (0, 5) dataset preserves its shape."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(empty_hdf5))
    # Assert
    assert loaded["group_with_empty"]["empty_2d"].shape == (0, 5)


def test_load_hdf5_empty_sibling_normal_data_present(empty_hdf5):
    """Non-empty siblings of empty datasets still load."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(empty_hdf5))
    # Assert
    assert np.array_equal(loaded["normal_data"], [1, 2, 3])


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------


def test_load_hdf5_missing_file_raises(tmp_path):
    """Opening a non-existent file raises."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    ctx = pytest.raises((FileNotFoundError, OSError, IOError))
    # Assert
    with ctx:
        _load_hdf5(str(tmp_path / "nonexistent.hdf5"), max_retries=1)


def test_load_hdf5_corrupted_file_raises(tmp_path):
    """Opening a corrupted file raises."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path = tmp_path / "corrupted.hdf5"
    path.write_bytes(b"This is not a valid HDF5 file")
    # Act
    ctx = pytest.raises((OSError, IOError, ValueError))
    # Assert
    with ctx:
        _load_hdf5(str(path), max_retries=1)


# ---------------------------------------------------------------------------
# Edge cases (deep nesting, unicode, extreme values)
# ---------------------------------------------------------------------------


@pytest.fixture
def edge_hdf5(tmp_path):
    path = tmp_path / "edge.hdf5"
    with h5py.File(path, "w") as hf:
        deep_group = hf
        for i in range(5):
            deep_group = deep_group.create_group(f"level_{i}")
        deep_group.create_dataset("deep_data", data=[42])
        ug = hf.create_group("unicode_group")
        ug.create_dataset("ds", data=np.array([1, 2, 3]))
        hf.create_dataset("huge_number", data=np.float64(1e308))
        hf.create_dataset("tiny_number", data=np.float64(1e-308))
        hf.create_dataset("nan_value", data=np.nan)
        hf.create_dataset("inf_value", data=np.inf)
        hf.create_dataset("neg_inf_value", data=-np.inf)
    return path


def test_load_hdf5_deep_nesting_reaches_leaf(edge_hdf5):
    """5-level-deep nesting reaches the leaf dataset."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    loaded = _load_hdf5(str(edge_hdf5))
    cur = loaded
    for i in range(5):
        cur = cur[f"level_{i}"]
    # Act
    leaf_value = int(cur["deep_data"][0])
    # Assert
    assert leaf_value == 42


def test_load_hdf5_huge_number_value(edge_hdf5):
    """``1e308`` round-trips exactly."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(edge_hdf5))
    # Assert
    assert loaded["huge_number"] == 1e308


def test_load_hdf5_tiny_number_value(edge_hdf5):
    """``1e-308`` round-trips exactly."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(edge_hdf5))
    # Assert
    assert loaded["tiny_number"] == 1e-308


def test_load_hdf5_nan_value(edge_hdf5):
    """A NaN dataset round-trips as NaN."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(edge_hdf5))
    # Assert
    assert np.isnan(loaded["nan_value"])


def test_load_hdf5_inf_value(edge_hdf5):
    """A positive infinity round-trips as inf."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(edge_hdf5))
    # Assert
    assert np.isinf(loaded["inf_value"])


def test_load_hdf5_neg_inf_value_is_negative(edge_hdf5):
    """A negative infinity is preserved with its sign."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    # Act
    loaded = _load_hdf5(str(edge_hdf5))
    # Assert
    assert loaded["neg_inf_value"] < 0


# ---------------------------------------------------------------------------
# Integration with public dispatcher + kwargs forwarding
# ---------------------------------------------------------------------------


def test_scitex_io_load_dispatches_hdf5(tmp_path):
    """``scitex_io.load`` recognises ``.hdf5`` and returns the dict."""
    # Arrange
    import scitex_io
    path = tmp_path / "via_load.hdf5"
    with h5py.File(path, "w") as hf:
        hf.create_dataset("test_data", data=np.array([1, 2, 3, 4, 5]))
    # Act
    loaded = scitex_io.load(str(path))
    # Assert
    assert np.array_equal(loaded["test_data"], [1, 2, 3, 4, 5])


def test_load_hdf5_accepts_extra_kwargs(tmp_path):
    """``_load_hdf5`` tolerates unknown kwargs (forwarded silently)."""
    # Arrange
    from scitex_io._load_modules._hdf5 import _load_hdf5
    path = tmp_path / "kw.hdf5"
    with h5py.File(path, "w") as hf:
        hf.create_dataset("data", data=[1, 2, 3])
    # Act
    loaded = _load_hdf5(str(path), some_unused_kwarg=True, another_kwarg="test")
    # Assert
    assert np.array_equal(loaded["data"], [1, 2, 3])
