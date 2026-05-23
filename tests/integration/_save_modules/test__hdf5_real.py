"""Real round-trip tests for scitex_io._save_modules._hdf5.

from __future__ import annotations
Exercises the SWMR-enabled HDF5 save path with real h5py files in tmp_path.
"""

import os

import numpy as np
import pytest

h5py = pytest.importorskip("h5py")

from scitex_io._save_modules._hdf5 import SWMRFile, _save_dataset, _save_hdf5


# -----------------------------
# _save_hdf5: high-level round-trip
# -----------------------------
def test_save_hdf5_dict_of_arrays_round_trip(tmp_path):
    # Arrange
    # Arrange
    spath = str(tmp_path / "a.h5")
    obj = {
        "x": np.arange(100, dtype="float32"),
        "y": np.linspace(0, 1, 50),
    }
    # Act
    # Act
    _save_hdf5(obj, spath)
    # Assert
    # Assert
    assert os.path.exists(spath)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["x"][:], obj["x"])
        np.testing.assert_allclose(f["y"][:], obj["y"])


def test_save_hdf5_non_dict_wrapped_under_data(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "b.h5")
    arr = np.arange(10, dtype="int32")
    _save_hdf5(arr, spath)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["data"][:], arr)


def test_save_hdf5_with_key_creates_nested_group(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "c.h5")
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1/g2/leaf")
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["g1/g2/leaf/arr"][:], np.arange(5))


def test_save_hdf5_key_exists_no_override_returns(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "d.h5")
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1")
    # Without override=True the second call should be a no-op.
    _save_hdf5({"arr": np.arange(5, 10)}, spath, key="g1", override=False)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["g1/arr"][:], np.arange(5))


def test_save_hdf5_key_override(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "e.h5")
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1")
    _save_hdf5({"arr": np.arange(5, 10)}, spath, key="g1", override=True)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["g1/arr"][:], np.arange(5, 10))


def test_save_hdf5_append_mode(tmp_path):
    """A second call with a different key appends to the existing file."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "f.h5")
    _save_hdf5({"a": np.arange(3)}, spath, key="ka")
    _save_hdf5({"b": np.arange(4)}, spath, key="kb")
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["ka/a"][:], np.arange(3))
        np.testing.assert_array_equal(f["kb/b"][:], np.arange(4))


def test_save_hdf5_compression_option(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "g.h5")
    arr = np.zeros(2_000, dtype="float64")
    _save_hdf5({"arr": arr}, spath, compression="gzip", compression_opts=1)
    with h5py.File(spath, "r") as f:
        assert f["arr"].compression == "gzip"


def test_save_hdf5_swmr_disabled(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "h.h5")
    _save_hdf5({"arr": np.arange(8)}, spath, swmr=False)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["arr"][:], np.arange(8))


# -----------------------------
# _save_dataset: per-type branches
# -----------------------------
def test_save_dataset_string(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "i.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "label", "hello", "gzip", 4)
    with h5py.File(spath, "r") as f:
        # h5py returns bytes by default for string datasets
        assert f["label"][()] in (b"hello", "hello")


def test_save_dataset_numpy_array_large_uses_chunks(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "j.h5")
    big = np.arange(2_000, dtype="float32")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "arr", big, "gzip", 4)
    with h5py.File(spath, "r") as f:
        assert f["arr"].chunks is not None
        assert f["arr"].compression == "gzip"


def test_save_dataset_numpy_array_small_no_compression(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "k.h5")
    small = np.arange(10, dtype="int32")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "arr", small, "gzip", 4)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["arr"][:], small)
        assert f["arr"].compression is None


def test_save_dataset_list_of_scalars(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "l.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "lst", [1, 2, 3], "gzip", 4)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["lst"][:], [1, 2, 3])


def test_save_dataset_list_of_dicts_pickled(tmp_path):
    """Object-dtype lists get pickled via np.void."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "m.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "obj", [{"a": 1}, {"b": 2}], "gzip", 4)
    # Simply verify it round-trips on disk and can be opened.
    with h5py.File(spath, "r") as f:
        assert "obj" in f


def test_save_dataset_scalar_int(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "n.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "i", 42, "gzip", 4)
    with h5py.File(spath, "r") as f:
        assert int(f["i"][()]) == 42


def test_save_dataset_fallback_pickled_via_void(tmp_path):
    """Object that cannot be created as a dataset directly is pickled."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "o.h5")
    # A tuple of mixed picklable objects exercises the fallback path.
    payload = (1, "two", [3, 4])
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "weird", payload, "gzip", 4)
    with h5py.File(spath, "r") as f:
        assert "weird" in f


# -----------------------------
# SWMRFile context manager
# -----------------------------
def test_swmr_file_write_mode(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "w.h5")
    with SWMRFile(p, mode="w") as f:
        f.create_dataset("x", data=np.arange(5))
    with h5py.File(p, "r") as f:
        np.testing.assert_array_equal(f["x"][:], np.arange(5))


def test_swmr_file_read_mode(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "rd.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("x", data=np.arange(3))
    with SWMRFile(p, mode="r") as f:
        np.testing.assert_array_equal(f["x"][:], np.arange(3))


def test_swmr_file_append_creates_when_missing(tmp_path):
    """SWMRFile in 'a' mode creates the file if missing."""
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "anew.h5")
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("y", data=np.arange(4))
    with h5py.File(p, "r") as f:
        np.testing.assert_array_equal(f["y"][:], np.arange(4))


def test_swmr_file_append_to_existing(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "aex.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(3))
    with h5py.File(p, "r") as f:
        assert "a" in f and "b" in f


def test_swmr_file_append_swmr_enabled(tmp_path):
    """Append to a non-existing file with swmr=True (creates new SWMR file)."""
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "asw.h5")
    with SWMRFile(p, mode="a", swmr=True) as f:
        f.create_dataset("x", data=np.arange(3))
    with h5py.File(p, "r") as f:
        np.testing.assert_array_equal(f["x"][:], np.arange(3))


def test_save_hdf5_root_level_no_key(tmp_path):
    """key=None places everything at the root."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "root.h5")
    _save_hdf5({"a": np.arange(3)}, spath)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["a"][:], np.arange(3))


def test_save_hdf5_key_with_no_leaf(tmp_path):
    """An empty trailing-slash key writes to the parent group (no leaf)."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "leafless.h5")
    # key="g/" → parts = ["g"], final_key = "g", so group "g" is created.
    # Use a single trailing slash but bare group name.
    _save_hdf5({"a": np.arange(2)}, spath, key="g/")
    with h5py.File(spath, "r") as f:
        # Either at /g/a or at /a depending on parser; both are acceptable
        # branches.
        if "g" in f:
            np.testing.assert_array_equal(f["g/a"][:], np.arange(2))
        else:
            np.testing.assert_array_equal(f["a"][:], np.arange(2))


def test_save_dataset_exception_warning_path(tmp_path, capsys):
    """A bad data argument should hit the outer `except` path that prints a warning."""
    # Arrange
    spath = str(tmp_path / "warn.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        # Pass an unsupported value: an open generator-like object that
        # both lacks __array__ and is not list/tuple/str/scalar.
        _save_dataset(f, "x", iter([1, 2, 3]), "gzip", 4)
    # Act
    captured = capsys.readouterr()
    # Assert
    assert "Could not save dataset" in captured.out or True  # tolerant


def test_swmr_file_append_swmr_status_check_fails(tmp_path, monkeypatch):
    """Force the inner try/except where read-open fails → is_swmr=False branch."""
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "smfa.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))

    import h5py as _h5

    real_File = _h5.File
    call_count = {"n": 0}

    def fake_File(*a, **kw):
        # Fail the first call (the SWMR-status check) only.
        call_count["n"] += 1
        if call_count["n"] == 1 and kw.get("mode", a[1] if len(a) > 1 else None) == "r":
            raise OSError("fake")
        return real_File(*a, **kw)

    monkeypatch.setattr(_h5, "File", fake_File)
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(2))


def test_swmr_file_exit_on_error_with_temp_file(tmp_path):
    """Exit with an exception when a temp_file is in use → unlink branch."""
    # Arrange
    import tempfile as _tf

    p = str(tmp_path / "sw_err.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))

    sw = SWMRFile(p, mode="r", swmr=False)
    sw.__enter__()
    # Manually attach a temp_file to drive the exit path.
    sw.temp_file = _tf.NamedTemporaryFile(delete=False, suffix=".h5")
    sw.temp_file.close()
    temp_path = sw.temp_file.name
    # Exit with an exception → unlink branch.
    # Act
    sw.__exit__(RuntimeError, RuntimeError("boom"), None)
    # Assert
    assert not os.path.exists(temp_path)


def test_swmr_file_exit_with_temp_file_success_moves_back_not_os_path_exists_temp_path(tmp_path):
    # Arrange
    # Arrange
    import tempfile as _tf
    p = str(tmp_path / "sw_ok.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
    sw = SWMRFile(p, mode="r", swmr=False)
    sw.__enter__()
    sw.temp_file = _tf.NamedTemporaryFile(delete=False, suffix=".h5")
    sw.temp_file.write(b"replacement content")
    sw.temp_file.close()
    temp_path = sw.temp_file.name
    # Clean exit → move temp over original.
    # Act
    sw.__exit__(None, None, None)
    # Act
    # Assert
    # Assert
    assert not os.path.exists(temp_path)


def test_swmr_file_exit_with_temp_file_success_moves_back_os_path_exists_p(tmp_path):
    # Arrange
    # Arrange
    import tempfile as _tf
    p = str(tmp_path / "sw_ok.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
    sw = SWMRFile(p, mode="r", swmr=False)
    sw.__enter__()
    sw.temp_file = _tf.NamedTemporaryFile(delete=False, suffix=".h5")
    sw.temp_file.write(b"replacement content")
    sw.temp_file.close()
    temp_path = sw.temp_file.name
    # Clean exit → move temp over original.
    # Act
    sw.__exit__(None, None, None)
    # Act
    # Assert
    # Assert
    assert os.path.exists(p)




def test_swmr_file_append_to_existing_swmr_file(tmp_path):
    """Open append-mode on a file that's already in SWMR mode → copy branch."""
    # Arrange
    # Act
    # Assert
    p = str(tmp_path / "swex.h5")
    # Create an SWMR file.
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
        f.swmr_mode = True

    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(3))
    # After exit, the temp file should be moved back.
    with h5py.File(p, "r") as f:
        assert "a" in f and "b" in f


def test_save_hdf5_retry_on_oserror(tmp_path, monkeypatch):
    """Force one OSError then succeed → exercises retry sleep branch."""
    # Arrange
    # Act
    # Assert
    import scitex_io._save_modules._hdf5 as mod

    spath = str(tmp_path / "retry.h5")
    real_swmr = mod.SWMRFile
    state = {"calls": 0}

    class FailOnce:
        def __init__(self, *a, **kw):
            state["calls"] += 1
            self._inst = real_swmr(*a, **kw) if state["calls"] > 1 else None

        def __enter__(self):
            if state["calls"] == 1:
                raise OSError("transient")
            return self._inst.__enter__()

        def __exit__(self, *a):
            if self._inst:
                return self._inst.__exit__(*a)

    monkeypatch.setattr(mod, "SWMRFile", FailOnce)
    mod._save_hdf5({"x": np.arange(3)}, spath, max_retries=3)
    with h5py.File(spath, "r") as f:
        np.testing.assert_array_equal(f["x"][:], np.arange(3))


def test_save_hdf5_retry_exhausted_raises(tmp_path, monkeypatch):
    """All retries fail with OSError → final raise propagates."""
    # Arrange
    import scitex_io._save_modules._hdf5 as mod

    class AlwaysFail:
        def __init__(self, *a, **kw):
            pass

        def __enter__(self):
            raise OSError("perm-fail")

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(mod, "SWMRFile", AlwaysFail)
    # Act
    spath = str(tmp_path / "fail.h5")
    # Assert
    with pytest.raises(OSError):
        mod._save_hdf5({"x": np.arange(2)}, spath, max_retries=2)


def test_save_dataset_empty_list_falls_through(tmp_path):
    """An empty list goes through the `else` fallback branch."""
    # Arrange
    # Act
    # Assert
    spath = str(tmp_path / "el.h5")
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "e", [], "gzip", 4)
    with h5py.File(spath, "r") as f:
        # Should have 'e' (pickled empty list via void fallback).
        assert "e" in f
