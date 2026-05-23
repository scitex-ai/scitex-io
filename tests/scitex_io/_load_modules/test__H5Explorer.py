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


def test_init_and_close_exp_filepath_equals_sample_h5(sample_h5):
    # Arrange
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Act
    # Assert
    # Assert
    assert exp.filepath == sample_h5


def test_init_and_close_exp_mode_equals_r(sample_h5):
    # Arrange
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Act
    # Assert
    # Assert
    assert exp.mode == "r"


def test_init_and_close_exp_file_is_not_none(sample_h5):
    # Arrange
    # Arrange
    # Act
    exp = H5Explorer(sample_h5)
    # Act
    # Assert
    # Assert
    assert exp.file is not None




def test_context_manager_smoke_case(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with H5Explorer(sample_h5) as exp:
        assert exp.file is not None
        assert "group1" in exp.keys()


def test_keys_root_and_group(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with H5Explorer(sample_h5) as exp:
        root_keys = exp.keys("/")
        assert "group1" in root_keys
        assert "top_dataset" in root_keys
        sub_keys = exp.keys("/group1")
        assert "ints" in sub_keys and "sub" in sub_keys
        # keys on dataset returns []
        assert exp.keys("/group1/ints") == []


def test_show_and_explore_ints_in_out(sample_h5):
    # Arrange
    # Arrange
    buf = io.StringIO()
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show()
        exp.explore()
        exp.show(max_depth=1)
        exp.show("/group1")
    # Act
    out = buf.getvalue()
    # Act
    # Assert
    # Assert
    assert "ints" in out


def test_show_and_explore_top_dataset_in_out(sample_h5):
    # Arrange
    # Arrange
    buf = io.StringIO()
    with redirect_stdout(buf), H5Explorer(sample_h5) as exp:
        exp.show()
        exp.explore()
        exp.show(max_depth=1)
        exp.show("/group1")
    # Act
    out = buf.getvalue()
    # Act
    # Assert
    # Assert
    assert "top_dataset" in out




def test_load_dataset_and_group(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
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


def test_get_alias_smoke_case(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with H5Explorer(sample_h5) as exp:
        a = exp.load("/group1/ints")
        b = exp.get("/group1/ints")
        np.testing.assert_array_equal(a, b)


def test_get_info_dataset_group_root(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
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


def test_find_smoke_case(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with H5Explorer(sample_h5) as exp:
        matches = exp.find("matrix")
        assert any("matrix" in m for m in matches)
        matches2 = exp.find("INTS")  # case-insensitive
        assert any("ints" in m for m in matches2)


def test_get_shape_and_dtype(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with H5Explorer(sample_h5) as exp:
        assert exp.get_shape("/group1/ints") == (10,)
        assert exp.get_dtype("/group1/ints") == np.int32
        # Group → None
        assert exp.get_shape("/group1") is None
        assert exp.get_dtype("/group1") is None


def test_explore_h5_convenience(sample_h5, tmp_path):
    # Arrange
    # Arrange
    buf = io.StringIO()
    # Act
    # Act
    with redirect_stdout(buf):
        explore_h5(sample_h5)
    # Assert
    # Assert
    assert "group1" in buf.getvalue()
    # non-existent → warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        explore_h5(str(tmp_path / "doesnotexist.h5"))
        assert any("does not exist" in str(x.message) for x in w)


def test_has_h5_key_basic_has_h5_key_sample_h5_group1_is_true(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert has_h5_key(sample_h5, "group1") is True


def test_has_h5_key_basic_has_h5_key_sample_h5_group1_ints_is_true(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert has_h5_key(sample_h5, "group1/ints") is True


def test_has_h5_key_basic_has_h5_key_sample_h5_group1_nope_is_false(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert has_h5_key(sample_h5, "group1/nope") is False


def test_has_h5_key_basic_has_h5_key_sample_h5_group1_sub_matrix_is_true(sample_h5):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert has_h5_key(sample_h5, "/group1/sub/matrix") is True




def test_has_h5_key_missing_file(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert has_h5_key(str(tmp_path / "nofile.h5"), "x") is False


def test_has_h5_key_corrupted(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "broken.h5"
    p.write_bytes(b"not an hdf5 file")
    # corruption indicator path; action_on_corrupted="delete" attempts delete fn
    # Act
    # Act
    out = has_h5_key(str(p), "some/key", action_on_corrupted="delete")
    # Assert
    # Assert
    assert out is False


def test_has_h5_key_lock_indicator_retries_out_is_false(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "lock.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1])
    calls = {"n": 0}
    real_file = h5py.File
    def fake_file(path, mode):
        calls["n"] += 1
        raise OSError("unable to lock file")
    monkeypatch.setattr(mod.h5py, "File", fake_file)
    # Act
    out = has_h5_key(str(p), "present", max_retries=3)
    # Act
    # Assert
    # Assert
    assert out is False


def test_has_h5_key_lock_indicator_retries_calls_n_3(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod
    p = tmp_path / "lock.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1])
    calls = {"n": 0}
    real_file = h5py.File
    def fake_file(path, mode):
        calls["n"] += 1
        raise OSError("unable to lock file")
    monkeypatch.setattr(mod.h5py, "File", fake_file)
    # Act
    out = has_h5_key(str(p), "present", max_retries=3)
    # Act
    # Assert
    # Assert
    assert calls["n"] == 3




def test_has_h5_key_unknown_oserror_reraises(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod

    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("k", data=[1])

    def fake_file(path, mode):
        raise OSError("some completely different error")

    # Act
    # Act
    monkeypatch.setattr(mod.h5py, "File", fake_file)
    # Assert
    # Assert
    with pytest.raises(OSError, match="completely different"):
        has_h5_key(str(p), "k")


def test_has_h5_key_corruption_action_raise(tmp_path):
    """corruption indicator with action_on_corrupted != 'delete' → returns False without delete."""
    # Arrange
    p = tmp_path / "broken.h5"
    p.write_bytes(b"\x00\x01\x02 not hdf5 truncated file")
    # Act
    out = has_h5_key(str(p), "k", action_on_corrupted="ignore")
    # Assert
    assert out is False


def test_has_h5_key_keyerror_path(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    import scitex_io._load_modules._H5Explorer as mod

    p = tmp_path / "x.h5"
    with h5py.File(p, "w") as f:
        f.create_dataset("k", data=[1])

    def fake_file(path, mode):
        raise KeyError("missing key")

    # Act
    # Act
    monkeypatch.setattr(mod.h5py, "File", fake_file)
    # Assert
    # Assert
    assert has_h5_key(str(p), "anything") is False


def test_delete_corrupted_entry_swallows_errors_delete_corrupted_entry_str_p_missing_key_is_false(tmp_path):
    # Real file, missing key → returns False (no exception)
    # Arrange
    # Arrange
    p = tmp_path / "x.h5"
    # Act
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1, 2, 3])
    # Act
    # Assert
    # Assert
    assert _delete_corrupted_entry(str(p), "missing_key") is False


def test_delete_corrupted_entry_swallows_errors_delete_corrupted_entry_str_p_present_is_true(tmp_path):
    # Real file, missing key → returns False (no exception)
    # Arrange
    # Arrange
    p = tmp_path / "x.h5"
    # Act
    with h5py.File(p, "w") as f:
        f.create_dataset("present", data=[1, 2, 3])
    # Act
    # Assert
    # Assert
    assert _delete_corrupted_entry(str(p), "present") is True


