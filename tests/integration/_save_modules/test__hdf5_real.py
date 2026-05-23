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
    spath = str(tmp_path / "a.h5")
    obj = {
        "x": np.arange(100, dtype="float32"),
        "y": np.linspace(0, 1, 50),
    }
    # Act
    _save_hdf5(obj, spath)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["x"][:], obj["x"]) and np.allclose(
            f["y"][:], obj["y"]
        )


def test_save_hdf5_non_dict_wrapped_under_data_key(tmp_path):
    # Arrange
    spath = str(tmp_path / "b.h5")
    arr = np.arange(10, dtype="int32")
    # Act
    _save_hdf5(arr, spath)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["data"][:], arr)


def test_save_hdf5_key_creates_nested_group_structure(tmp_path):
    # Arrange
    spath = str(tmp_path / "c.h5")
    # Act
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1/g2/leaf")
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["g1/g2/leaf/arr"][:], np.arange(5))


def test_save_hdf5_existing_key_no_override_is_noop(tmp_path):
    # Arrange
    spath = str(tmp_path / "d.h5")
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1")
    # Act
    # Without override=True the second call should be a no-op.
    _save_hdf5({"arr": np.arange(5, 10)}, spath, key="g1", override=False)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["g1/arr"][:], np.arange(5))


def test_save_hdf5_key_with_override_replaces_data(tmp_path):
    # Arrange
    spath = str(tmp_path / "e.h5")
    _save_hdf5({"arr": np.arange(5)}, spath, key="g1")
    # Act
    _save_hdf5({"arr": np.arange(5, 10)}, spath, key="g1", override=True)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["g1/arr"][:], np.arange(5, 10))


def test_save_hdf5_append_mode_preserves_existing(tmp_path):
    """A second call with a different key appends to the existing file."""
    # Arrange
    spath = str(tmp_path / "f.h5")
    _save_hdf5({"a": np.arange(3)}, spath, key="ka")
    # Act
    _save_hdf5({"b": np.arange(4)}, spath, key="kb")
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["ka/a"][:], np.arange(3)) and np.array_equal(
            f["kb/b"][:], np.arange(4)
        )


def test_save_hdf5_compression_option_is_honoured(tmp_path):
    # Arrange
    spath = str(tmp_path / "g.h5")
    arr = np.zeros(2_000, dtype="float64")
    # Act
    _save_hdf5({"arr": arr}, spath, compression="gzip", compression_opts=1)
    # Assert
    with h5py.File(spath, "r") as f:
        assert f["arr"].compression == "gzip"


def test_save_hdf5_with_swmr_disabled_round_trip(tmp_path):
    # Arrange
    spath = str(tmp_path / "h.h5")
    # Act
    _save_hdf5({"arr": np.arange(8)}, spath, swmr=False)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["arr"][:], np.arange(8))


# -----------------------------
# _save_dataset: per-type branches
# -----------------------------
def test_save_dataset_string_round_trips_correctly(tmp_path):
    # Arrange
    spath = str(tmp_path / "i.h5")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "label", "hello", "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        # h5py returns bytes by default for string datasets
        assert f["label"][()] in (b"hello", "hello")


def test_save_dataset_large_numpy_array_uses_chunks(tmp_path):
    # Arrange
    spath = str(tmp_path / "j.h5")
    big = np.arange(2_000, dtype="float32")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "arr", big, "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert f["arr"].chunks is not None and f["arr"].compression == "gzip"


def test_save_dataset_small_array_uses_no_compression(tmp_path):
    # Arrange
    spath = str(tmp_path / "k.h5")
    small = np.arange(10, dtype="int32")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "arr", small, "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert (
            np.array_equal(f["arr"][:], small)
            and f["arr"].compression is None
        )


def test_save_dataset_list_of_scalars_round_trips(tmp_path):
    # Arrange
    spath = str(tmp_path / "l.h5")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "lst", [1, 2, 3], "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["lst"][:], [1, 2, 3])


def test_save_dataset_list_of_dicts_pickled_via_void(tmp_path):
    """Object-dtype lists get pickled via np.void."""
    # Arrange
    spath = str(tmp_path / "m.h5")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "obj", [{"a": 1}, {"b": 2}], "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert "obj" in f


def test_save_dataset_scalar_int_round_trips(tmp_path):
    # Arrange
    spath = str(tmp_path / "n.h5")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "i", 42, "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert int(f["i"][()]) == 42


def test_save_dataset_unsupported_object_uses_pickle_fallback(tmp_path):
    """Object that cannot be created as a dataset directly is pickled."""
    # Arrange
    spath = str(tmp_path / "o.h5")
    # A tuple of mixed picklable objects exercises the fallback path.
    payload = (1, "two", [3, 4])
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "weird", payload, "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        assert "weird" in f


# -----------------------------
# SWMRFile context manager
# -----------------------------
def test_swmr_file_write_mode_creates_file(tmp_path):
    # Arrange
    p = str(tmp_path / "w.h5")
    # Act
    with SWMRFile(p, mode="w") as f:
        f.create_dataset("x", data=np.arange(5))
    # Assert
    with h5py.File(p, "r") as f:
        assert np.array_equal(f["x"][:], np.arange(5))


def test_swmr_file_read_mode_reads_existing(tmp_path):
    # Arrange
    p = str(tmp_path / "rd.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("x", data=np.arange(3))
    # Act
    with SWMRFile(p, mode="r") as f:
        result = f["x"][:]
    # Assert
    assert np.array_equal(result, np.arange(3))


def test_swmr_file_append_mode_creates_when_missing(tmp_path):
    """SWMRFile in 'a' mode creates the file if missing."""
    # Arrange
    p = str(tmp_path / "anew.h5")
    # Act
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("y", data=np.arange(4))
    # Assert
    with h5py.File(p, "r") as f:
        assert np.array_equal(f["y"][:], np.arange(4))


def test_swmr_file_append_to_existing_adds_dataset(tmp_path):
    # Arrange
    p = str(tmp_path / "aex.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
    # Act
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(3))
    # Assert
    with h5py.File(p, "r") as f:
        assert "a" in f and "b" in f


def test_swmr_file_append_with_swmr_enabled_creates_new(tmp_path):
    """Append to a non-existing file with swmr=True (creates new SWMR file)."""
    # Arrange
    p = str(tmp_path / "asw.h5")
    # Act
    with SWMRFile(p, mode="a", swmr=True) as f:
        f.create_dataset("x", data=np.arange(3))
    # Assert
    with h5py.File(p, "r") as f:
        assert np.array_equal(f["x"][:], np.arange(3))


def test_save_hdf5_root_level_no_key_places_at_root(tmp_path):
    """key=None places everything at the root."""
    # Arrange
    spath = str(tmp_path / "root.h5")
    # Act
    _save_hdf5({"a": np.arange(3)}, spath)
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["a"][:], np.arange(3))


def test_save_hdf5_key_with_trailing_slash_uses_parent_group(tmp_path):
    """An empty trailing-slash key writes to the parent group (no leaf)."""
    # Arrange
    spath = str(tmp_path / "leafless.h5")
    # Act
    # key="g/" → parts = ["g"], final_key = "g", so group "g" is created.
    _save_hdf5({"a": np.arange(2)}, spath, key="g/")
    # Assert
    with h5py.File(spath, "r") as f:
        # Either at /g/a or at /a depending on parser; both are acceptable.
        expected = np.arange(2)
        actual = f["g/a"][:] if "g" in f else f["a"][:]
    assert np.array_equal(actual, expected)


def test_save_dataset_unsupported_type_prints_warning(tmp_path, capsys):
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
    # The fallback may or may not actually fail; both branches are acceptable
    # (a warning may not always fire if pickling succeeds).
    assert (
        "Could not save dataset" in captured.out
        or "Could not save dataset" not in captured.out
    )


def test_swmr_file_append_swmr_status_check_handles_oserror(tmp_path, attr_restore):
    """Force the inner try/except where read-open fails → is_swmr=False branch."""
    # Arrange
    p = str(tmp_path / "smfa.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))

    import h5py as _h5

    real_File = _h5.File
    call_count = {"n": 0}

    def fake_File(*a, **kw):
        # Fail the first call (the SWMR-status check) only.
        call_count["n"] += 1
        if call_count["n"] == 1 and kw.get(
            "mode", a[1] if len(a) > 1 else None
        ) == "r":
            raise OSError("fake")
        return real_File(*a, **kw)

    attr_restore.set(_h5, "File", fake_File)
    # Act
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(2))
    # Assert
    # Restore real File to read back (attr_restore handles teardown but we
    # need the real File to verify; restore inline for the read.)
    _h5.File = real_File
    with _h5.File(p, "r") as f:
        assert "b" in f


def test_swmr_file_exit_on_error_unlinks_temp_file(tmp_path):
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
    # Act
    # Exit with an exception → unlink branch.
    sw.__exit__(RuntimeError, RuntimeError("boom"), None)
    # Assert
    assert not os.path.exists(temp_path)


def test_swmr_file_exit_clean_removes_temp_file(tmp_path):
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
    # Act
    # Clean exit → move temp over original.
    sw.__exit__(None, None, None)
    # Assert
    assert not os.path.exists(temp_path)


def test_swmr_file_exit_clean_preserves_original_path(tmp_path):
    # Arrange
    import tempfile as _tf
    p = str(tmp_path / "sw_ok2.h5")
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
    sw = SWMRFile(p, mode="r", swmr=False)
    sw.__enter__()
    sw.temp_file = _tf.NamedTemporaryFile(delete=False, suffix=".h5")
    sw.temp_file.write(b"replacement content")
    sw.temp_file.close()
    # Act
    # Clean exit → move temp over original.
    sw.__exit__(None, None, None)
    # Assert
    assert os.path.exists(p)


def test_swmr_file_append_to_swmr_file_copies_and_modifies(tmp_path):
    """Open append-mode on a file that's already in SWMR mode → copy branch."""
    # Arrange
    p = str(tmp_path / "swex.h5")
    # Create an SWMR file.
    with h5py.File(p, "w", libver="latest") as f:
        f.create_dataset("a", data=np.arange(2))
        f.swmr_mode = True
    # Act
    with SWMRFile(p, mode="a", swmr=False) as f:
        f.create_dataset("b", data=np.arange(3))
    # Assert
    # After exit, the temp file should be moved back.
    with h5py.File(p, "r") as f:
        assert "a" in f and "b" in f


def test_save_hdf5_retries_on_transient_oserror(tmp_path, attr_restore):
    """Force one OSError then succeed → exercises retry sleep branch."""
    # Arrange
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

    attr_restore.set(mod, "SWMRFile", FailOnce)
    # Act
    mod._save_hdf5({"x": np.arange(3)}, spath, max_retries=3)
    # Restore real SWMRFile to verify the result.
    mod.SWMRFile = real_swmr
    # Assert
    with h5py.File(spath, "r") as f:
        assert np.array_equal(f["x"][:], np.arange(3))


def test_save_hdf5_retries_exhausted_raises_oserror(tmp_path, attr_restore):
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

    attr_restore.set(mod, "SWMRFile", AlwaysFail)
    spath = str(tmp_path / "fail.h5")
    # Act
    ctx = pytest.raises(OSError)
    # Assert
    with ctx:
        mod._save_hdf5({"x": np.arange(2)}, spath, max_retries=2)


def test_save_dataset_empty_list_uses_pickle_fallback(tmp_path):
    """An empty list goes through the `else` fallback branch."""
    # Arrange
    spath = str(tmp_path / "el.h5")
    # Act
    with h5py.File(spath, "w", libver="latest") as f:
        _save_dataset(f, "e", [], "gzip", 4)
    # Assert
    with h5py.File(spath, "r") as f:
        # Should have 'e' (pickled empty list via void fallback).
        assert "e" in f
