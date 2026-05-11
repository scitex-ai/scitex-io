#!/usr/bin/env python3
"""Real-coverage tests for scitex_io._load_modules._H5Explorer."""

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
        # Pickled object stored as np.void
        obj = {"a": 1, "b": [1, 2, 3]}
        sub.create_dataset("pickled", data=np.void(pickle.dumps(obj)))
        f.create_dataset("top_dataset", data=np.array([1.0, 2.0]), chunks=(2,))
    return str(p)


def test_init_and_close(sample_h5):
    exp = H5Explorer(sample_h5)
    assert exp.filepath == sample_h5
    assert exp.mode == "r"
    assert exp.file is not None
    exp.close()
    # close is idempotent if file already closed
    exp.close()


def test_context_manager(sample_h5):
    with H5Explorer(sample_h5) as exp:
        assert exp.file is not None
        assert "group1" in exp.keys()


def test_keys_root_and_group(sample_h5):
    with H5Explorer(sample_h5) as exp:
        root_keys = exp.keys("/")
        assert "group1" in root_keys
        assert "top_dataset" in root_keys
        sub_keys = exp.keys("/group1")
        assert "ints" in sub_keys and "sub" in sub_keys
        # keys on dataset returns []
        assert exp.keys("/group1/ints") == []


def test_show_and_explore(sample_h5):
    buf = io.StringIO()
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show()
        exp.explore()
        exp.show(max_depth=1)
        exp.show("/group1")
    out = buf.getvalue()
    assert "ints" in out
    assert "top_dataset" in out


def test_load_dataset_and_group(sample_h5):
    with H5Explorer(sample_h5) as exp:
        ints = exp.load("/group1/ints")
        assert isinstance(ints, np.ndarray)
        assert list(ints) == list(range(10))

        # bytes auto-decoded
        s = exp.load("/group1/sub/bytes_field")
        assert s == "hello world"

        # pickled object
        obj = exp.load("/group1/sub/pickled")
        assert obj == {"a": 1, "b": [1, 2, 3]}

        # group load → dict with attrs
        grp = exp.load("/group1")
        assert "ints" in grp and "sub" in grp
        assert grp["_attr_units"] == "Hz"


def test_get_alias(sample_h5):
    with H5Explorer(sample_h5) as exp:
        a = exp.load("/group1/ints")
        b = exp.get("/group1/ints")
        np.testing.assert_array_equal(a, b)


def test_get_info_dataset_group_root(sample_h5):
    with H5Explorer(sample_h5) as exp:
        info_d = exp.get_info("/group1/ints")
        assert info_d["type"] == "Dataset"
        assert info_d["shape"] == (10,)
        assert "dtype" in info_d and "size" in info_d

        info_g = exp.get_info("/group1")
        assert info_g["type"] == "Group"
        assert info_g["n_items"] >= 1
        assert "units" in info_g["attributes"]

        info_root = exp.get_info("/")
        assert info_root["type"] == "File"
        assert "root_attr" in info_root["attributes"]


def test_find(sample_h5):
    with H5Explorer(sample_h5) as exp:
        matches = exp.find("matrix")
        assert any("matrix" in m for m in matches)
        matches2 = exp.find("INTS")  # case-insensitive
        assert any("ints" in m for m in matches2)


def test_get_shape_and_dtype(sample_h5):
    with H5Explorer(sample_h5) as exp:
        assert exp.get_shape("/group1/ints") == (10,)
        assert exp.get_dtype("/group1/ints") == np.int32
        # Group → None
        assert exp.get_shape("/group1") is None
        assert exp.get_dtype("/group1") is None


def test_explore_h5_convenience(sample_h5, tmp_path):
    buf = io.StringIO()
    with redirect_stdout(buf):
        explore_h5(sample_h5)
    assert "group1" in buf.getvalue()
    # non-existent → warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        explore_h5(str(tmp_path / "doesnotexist.h5"))
        assert any("does not exist" in str(x.message) for x in w)


def test_has_h5_key_basic(sample_h5):
    assert has_h5_key(sample_h5, "group1") is True
    assert has_h5_key(sample_h5, "group1/ints") is True
    assert has_h5_key(sample_h5, "group1/nope") is False
    assert has_h5_key(sample_h5, "/group1/sub/matrix") is True


def test_has_h5_key_missing_file(tmp_path):
    assert has_h5_key(str(tmp_path / "nofile.h5"), "x") is False


def test_has_h5_key_corrupted(tmp_path):
    p = tmp_path / "broken.h5"
    p.write_bytes(b"not an hdf5 file")
    # corruption indicator path; action_on_corrupted="delete" attempts delete fn
    out = has_h5_key(str(p), "some/key", action_on_corrupted="delete")
    assert out is False


def test_delete_corrupted_entry_swallows_errors(tmp_path):
    # Real file, missing key → returns False (no exception)
    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1, 2, 3])
    assert _delete_corrupted_entry(str(p), "missing_key") is False
    # Existing key → returns True after delete
    assert _delete_corrupted_entry(str(p), "present") is True
