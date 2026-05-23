#!/usr/bin/env python3
"""Real-coverage tests for ``scitex_io._load_modules._H5Explorer``.

Real ``h5py.File`` instances are written into ``tmp_path``. Where the
test needs to force an exception from ``h5py.File`` (lock / corruption /
unknown OSError branches), we use the ``attr_restore`` fixture from
conftest to swap out the module-level ``h5py.File`` and restore it on
teardown.
"""

from __future__ import annotations

import io
import pickle
import warnings
from contextlib import redirect_stdout

import h5py
import numpy as np
import pytest

from scitex_io._load_modules._H5Explorer import (
    H5Explorer,
    _delete_corrupted_entry,
    explore_h5,
    has_h5_key,
)


@pytest.fixture
def sample_h5(tmp_path):
    p = tmp_path / "sample.h5"
    with h5py.File(p, "w") as f:
        f.attrs["root_attr"] = "hello"
        g = f.create_group("group1")
        g.attrs["units"] = "Hz"
        g.create_dataset("ints", data=np.arange(10, dtype=np.int32))
        g.create_dataset("floats", data=np.linspace(0, 1, 5))
        sub = g.create_group("sub")
        sub.create_dataset("matrix", data=np.eye(3))
        sub.create_dataset("bytes_field", data=b"hello world")
        obj = {"a": 1, "b": [1, 2, 3]}
        sub.create_dataset("pickled", data=np.void(pickle.dumps(obj)))
        f.create_dataset("top_dataset", data=np.array([1.0, 2.0]), chunks=(2,))
    return str(p)


# ---------------------------------------------------------------------------
# __init__ / close
# ---------------------------------------------------------------------------


def test_h5explorer_init_records_filepath(sample_h5):
    """Constructor stores the supplied filepath."""
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Assert
    assert exp.filepath == sample_h5
    exp.close()


def test_h5explorer_init_defaults_mode_to_read(sample_h5):
    """Default ``mode`` is ``'r'``."""
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Assert
    assert exp.mode == "r"
    exp.close()


def test_h5explorer_init_opens_underlying_file(sample_h5):
    """``exp.file`` is a live h5py handle after construction."""
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Assert
    assert exp.file is not None
    exp.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_h5explorer_context_manager_yields_open_file(sample_h5):
    """Inside the ``with`` block the underlying file is open."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        live = exp.file is not None
    # Assert
    assert live


def test_h5explorer_context_manager_exposes_root_keys(sample_h5):
    """Inside the ``with`` block, ``keys()`` reports the root groups."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        root = exp.keys()
    # Assert
    assert "group1" in root


# ---------------------------------------------------------------------------
# keys()
# ---------------------------------------------------------------------------


def test_h5explorer_keys_root_lists_group1(sample_h5):
    """``keys('/')`` lists root groups."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        root_keys = exp.keys("/")
    # Assert
    assert "group1" in root_keys


def test_h5explorer_keys_root_lists_top_dataset(sample_h5):
    """``keys('/')`` lists root datasets."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        root_keys = exp.keys("/")
    # Assert
    assert "top_dataset" in root_keys


def test_h5explorer_keys_group_lists_children(sample_h5):
    """``keys('/group1')`` lists the group's immediate children."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        sub_keys = exp.keys("/group1")
    # Assert
    assert {"ints", "sub"}.issubset(sub_keys)


def test_h5explorer_keys_dataset_returns_empty_list(sample_h5):
    """Calling ``keys()`` on a dataset path returns ``[]``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        result = exp.keys("/group1/ints")
    # Assert
    assert result == []


# ---------------------------------------------------------------------------
# show() / explore() printing
# ---------------------------------------------------------------------------


def test_h5explorer_show_prints_dataset_name(sample_h5):
    """``show()`` includes a dataset's name in stdout."""
    # Arrange
    buf = io.StringIO()
    # Act
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show()
    # Assert
    assert "ints" in buf.getvalue()


def test_h5explorer_show_prints_top_dataset_name(sample_h5):
    """``show()`` includes top-level dataset names in stdout."""
    # Arrange
    buf = io.StringIO()
    # Act
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show()
    # Assert
    assert "top_dataset" in buf.getvalue()


def test_h5explorer_show_at_path_prints_group_children(sample_h5):
    """``show('/group1')`` prints that group's children."""
    # Arrange
    buf = io.StringIO()
    # Act
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show("/group1")
    # Assert
    assert "ints" in buf.getvalue()


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------


def test_h5explorer_load_dataset_returns_ndarray(sample_h5):
    """Loading a dataset yields a numpy array."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        ints = exp.load("/group1/ints")
    # Assert
    assert isinstance(ints, np.ndarray)


def test_h5explorer_load_dataset_returns_expected_values(sample_h5):
    """Loaded dataset matches what was written."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        ints = exp.load("/group1/ints")
    # Assert
    assert list(ints) == list(range(10))


def test_h5explorer_load_decodes_bytes_to_str(sample_h5):
    """A bytes dataset is auto-decoded to a Python string."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        s = exp.load("/group1/sub/bytes_field")
    # Assert
    assert s == "hello world"


def test_h5explorer_load_unpickles_void_data(sample_h5):
    """A pickled-payload dataset is unpickled on load."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        obj = exp.load("/group1/sub/pickled")
    # Assert
    assert obj == {"a": 1, "b": [1, 2, 3]}


def test_h5explorer_load_group_includes_children_keys(sample_h5):
    """Loading a group returns a dict containing the children keys."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        grp = exp.load("/group1")
    # Assert
    assert {"ints", "sub"}.issubset(grp.keys())


def test_h5explorer_load_group_includes_attrs_with_underscore_prefix(sample_h5):
    """Group attributes appear under ``_attr_<name>`` keys."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        grp = exp.load("/group1")
    # Assert
    assert grp["_attr_units"] == "Hz"


# ---------------------------------------------------------------------------
# get() alias
# ---------------------------------------------------------------------------


def test_h5explorer_get_is_alias_for_load(sample_h5):
    """``get(path)`` returns the same array as ``load(path)``."""
    # Arrange
    with H5Explorer(sample_h5) as exp:
        a = exp.load("/group1/ints")
        b = exp.get("/group1/ints")
    # Act
    same = np.array_equal(a, b)
    # Assert
    assert same


# ---------------------------------------------------------------------------
# get_info()
# ---------------------------------------------------------------------------


def test_h5explorer_get_info_dataset_type(sample_h5):
    """``get_info`` on a dataset reports type ``Dataset``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/group1/ints")
    # Assert
    assert info["type"] == "Dataset"


def test_h5explorer_get_info_dataset_shape(sample_h5):
    """``get_info`` on a dataset reports its shape."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/group1/ints")
    # Assert
    assert info["shape"] == (10,)


def test_h5explorer_get_info_dataset_includes_dtype(sample_h5):
    """``get_info`` on a dataset includes the ``dtype`` field."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/group1/ints")
    # Assert
    assert "dtype" in info


def test_h5explorer_get_info_group_type(sample_h5):
    """``get_info`` on a group reports type ``Group``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/group1")
    # Assert
    assert info["type"] == "Group"


def test_h5explorer_get_info_group_lists_attributes(sample_h5):
    """``get_info`` on a group lists its attributes."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/group1")
    # Assert
    assert "units" in info["attributes"]


def test_h5explorer_get_info_root_type(sample_h5):
    """``get_info('/')`` reports type ``File``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/")
    # Assert
    assert info["type"] == "File"


def test_h5explorer_get_info_root_lists_attributes(sample_h5):
    """``get_info('/')`` lists root attributes."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        info = exp.get_info("/")
    # Assert
    assert "root_attr" in info["attributes"]


# ---------------------------------------------------------------------------
# find()
# ---------------------------------------------------------------------------


def test_h5explorer_find_locates_matching_name(sample_h5):
    """``find('matrix')`` finds the matching dataset path."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        matches = exp.find("matrix")
    # Assert
    assert any("matrix" in m for m in matches)


def test_h5explorer_find_is_case_insensitive(sample_h5):
    """``find('INTS')`` matches ``ints`` (case-insensitive)."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        matches = exp.find("INTS")
    # Assert
    assert any("ints" in m for m in matches)


# ---------------------------------------------------------------------------
# get_shape / get_dtype
# ---------------------------------------------------------------------------


def test_h5explorer_get_shape_returns_dataset_shape(sample_h5):
    """``get_shape`` on a dataset returns its shape tuple."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        shape = exp.get_shape("/group1/ints")
    # Assert
    assert shape == (10,)


def test_h5explorer_get_dtype_returns_dataset_dtype(sample_h5):
    """``get_dtype`` on a dataset returns its dtype."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        dtype = exp.get_dtype("/group1/ints")
    # Assert
    assert dtype == np.int32


def test_h5explorer_get_shape_returns_none_for_group(sample_h5):
    """``get_shape`` on a group returns ``None``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        shape = exp.get_shape("/group1")
    # Assert
    assert shape is None


def test_h5explorer_get_dtype_returns_none_for_group(sample_h5):
    """``get_dtype`` on a group returns ``None``."""
    # Arrange
    # Act
    with H5Explorer(sample_h5) as exp:
        dtype = exp.get_dtype("/group1")
    # Assert
    assert dtype is None


# ---------------------------------------------------------------------------
# explore_h5 convenience
# ---------------------------------------------------------------------------


def test_explore_h5_prints_top_group(sample_h5):
    """``explore_h5`` prints the file's top-level groups."""
    # Arrange
    buf = io.StringIO()
    # Act
    with redirect_stdout(buf):
        explore_h5(sample_h5)
    # Assert
    assert "group1" in buf.getvalue()


def test_explore_h5_warns_on_missing_file(tmp_path):
    """``explore_h5`` on a missing file emits a warning."""
    # Arrange
    # Act
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        explore_h5(str(tmp_path / "doesnotexist.h5"))
    # Assert
    assert any("does not exist" in str(x.message) for x in w)


# ---------------------------------------------------------------------------
# has_h5_key — happy paths
# ---------------------------------------------------------------------------


def test_has_h5_key_returns_true_for_existing_group(sample_h5):
    """``has_h5_key`` is True for an existing top-level group."""
    # Arrange
    # Act
    result = has_h5_key(sample_h5, "group1")
    # Assert
    assert result is True


def test_has_h5_key_returns_true_for_existing_nested_dataset(sample_h5):
    """``has_h5_key`` is True for an existing nested dataset."""
    # Arrange
    # Act
    result = has_h5_key(sample_h5, "group1/ints")
    # Assert
    assert result is True


def test_has_h5_key_returns_false_for_missing_key(sample_h5):
    """``has_h5_key`` is False when the leaf key is missing."""
    # Arrange
    # Act
    result = has_h5_key(sample_h5, "group1/nope")
    # Assert
    assert result is False


def test_has_h5_key_returns_true_for_leading_slash_path(sample_h5):
    """A leading slash in the key is tolerated."""
    # Arrange
    # Act
    result = has_h5_key(sample_h5, "/group1/sub/matrix")
    # Assert
    assert result is True


def test_has_h5_key_returns_false_for_missing_file(tmp_path):
    """``has_h5_key`` is False when the file itself does not exist."""
    # Arrange
    # Act
    result = has_h5_key(str(tmp_path / "nofile.h5"), "x")
    # Assert
    assert result is False


def test_has_h5_key_returns_false_for_corrupted_file(tmp_path):
    """A corrupted file → ``has_h5_key`` returns False (does not raise)."""
    # Arrange
    p = tmp_path / "broken.h5"
    p.write_bytes(b"not an hdf5 file")
    # Act
    result = has_h5_key(str(p), "some/key", action_on_corrupted="delete")
    # Assert
    assert result is False


def test_has_h5_key_corruption_ignore_returns_false(tmp_path):
    """``action_on_corrupted='ignore'`` still returns False on corruption."""
    # Arrange
    p = tmp_path / "broken.h5"
    p.write_bytes(b"\x00\x01\x02 not hdf5 truncated file")
    # Act
    result = has_h5_key(str(p), "k", action_on_corrupted="ignore")
    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# has_h5_key — lock / OSError branches via attr_restore
# ---------------------------------------------------------------------------


def test_has_h5_key_lock_indicator_returns_false_after_retries(tmp_path, attr_restore):
    """A persistent ``unable to lock file`` OSError → False."""
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "lock.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1])

    def fake_file(path, mode):
        raise OSError("unable to lock file")

    attr_restore.set(mod.h5py, "File", fake_file)
    # Act
    result = has_h5_key(str(p), "present", max_retries=3)
    # Assert
    assert result is False


def test_has_h5_key_lock_indicator_attempts_max_retries(tmp_path, attr_restore):
    """A persistent lock error → exactly ``max_retries`` attempts."""
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "lock.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1])
    calls = {"n": 0}

    def fake_file(path, mode):
        calls["n"] += 1
        raise OSError("unable to lock file")

    attr_restore.set(mod.h5py, "File", fake_file)
    # Act
    has_h5_key(str(p), "present", max_retries=3)
    # Assert
    assert calls["n"] == 3


def test_has_h5_key_unknown_oserror_reraises(tmp_path, attr_restore):
    """An OSError that matches neither lock nor corruption is re-raised."""
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("k", data=[1])

    def fake_file(path, mode):
        raise OSError("some completely different error")

    attr_restore.set(mod.h5py, "File", fake_file)
    # Act
    ctx = pytest.raises(OSError, match="completely different")
    # Assert
    with ctx:
        has_h5_key(str(p), "k")


def test_has_h5_key_keyerror_returns_false(tmp_path, attr_restore):
    """A ``KeyError`` from ``h5py.File`` is swallowed and returns False."""
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("k", data=[1])

    def fake_file(path, mode):
        raise KeyError("missing key")

    attr_restore.set(mod.h5py, "File", fake_file)
    # Act
    result = has_h5_key(str(p), "anything")
    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# _delete_corrupted_entry
# ---------------------------------------------------------------------------


def test_delete_corrupted_entry_returns_false_for_missing_key(tmp_path):
    """Missing-key path → ``_delete_corrupted_entry`` returns False."""
    # Arrange
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1, 2, 3])
    # Act
    result = _delete_corrupted_entry(str(p), "missing_key")
    # Assert
    assert result is False


def test_delete_corrupted_entry_returns_true_for_present_key(tmp_path):
    """Existing-key path → ``_delete_corrupted_entry`` returns True."""
    # Arrange
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1, 2, 3])
    # Act
    result = _delete_corrupted_entry(str(p), "present")
    # Assert
    assert result is True
