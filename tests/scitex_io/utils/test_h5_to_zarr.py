"""Tests for scitex_io.utils.h5_to_zarr public migration API.

from __future__ import annotations
Exercises real h5py -> zarr round-trips against real files in tmp_path.
"""

import os
from pathlib import Path

import h5py
import numpy as np
import pytest

zarr = pytest.importorskip("zarr", reason="zarr not installed")
try:
    from zarr.codecs import GzipCodec  # noqa: F401  -- zarr v3 marker
except Exception:  # noqa: BLE001
    pytest.skip(
        "zarr v3 required (zarr.codecs.GzipCodec missing)",
        allow_module_level=True,
    )

from scitex_io.utils.h5_to_zarr import (
    _migrate_sequential,
    migrate_h5_to_zarr,
    migrate_h5_to_zarr_batch,
)


def _build_h5(path: Path):
    with h5py.File(path, "w") as f:
        f.attrs["title"] = "demo"
        f.create_dataset("flat", data=np.arange(24).reshape(4, 6), dtype="int32")
        g = f.create_group("group_a")
        g.attrs["k"] = 1
        g.create_dataset("nested", data=np.linspace(0.0, 1.0, 10))
        g.create_dataset("zero", shape=(0,), dtype="float64")
        h = g.create_group("sub")
        h.create_dataset("deep", data=np.array([[1, 2], [3, 4]], dtype="int64"))
    return path


def _assert_roundtrip(h5_path: Path, zarr_path: Path):
    store = zarr.open(str(zarr_path), mode="r")
    with h5py.File(h5_path, "r") as f:
        # root attrs
        assert store.attrs["title"] == f.attrs["title"]
        # flat dataset
        np.testing.assert_array_equal(store["flat"][:], f["flat"][:])
        assert store["flat"].dtype == f["flat"].dtype
        # nested
        np.testing.assert_allclose(store["group_a/nested"][:], f["group_a/nested"][:])
        assert store["group_a"].attrs["k"] == 1
        # deep
        np.testing.assert_array_equal(
            store["group_a/sub/deep"][:], f["group_a/sub/deep"][:]
        )


def test_migrate_h5_to_zarr_basic(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "src.h5")
    # Act
    # Act
    out = migrate_h5_to_zarr(
        h5_path, zarr_path=tmp_path / "dst.zarr", show_progress=True
    )
    # Assert
    # Assert
    assert os.path.isdir(out)
    _assert_roundtrip(h5_path, Path(out))


def test_migrate_h5_to_zarr_default_zarr_path_out_endswith_zarr(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "auto.h5")
    # Act
    out = migrate_h5_to_zarr(h5_path, show_progress=False)
    # Act
    # Assert
    # Assert
    assert out.endswith(".zarr")


def test_migrate_h5_to_zarr_default_zarr_path_path_out_exists(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "auto.h5")
    # Act
    out = migrate_h5_to_zarr(h5_path, show_progress=False)
    # Act
    # Assert
    # Assert
    assert Path(out).exists()




def test_migrate_h5_to_zarr_missing_file_raises(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    missing = tmp_path / "nope.h5"
    # Assert
    # Assert
    with pytest.raises(Exception):
        migrate_h5_to_zarr(missing, zarr_path=tmp_path / "x.zarr")


def test_migrate_h5_to_zarr_existing_no_overwrite_raises(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "src.h5")
    zp = tmp_path / "out.zarr"
    # Act
    # Act
    migrate_h5_to_zarr(h5_path, zarr_path=zp, show_progress=False)
    # Assert
    # Assert
    with pytest.raises(Exception):
        migrate_h5_to_zarr(h5_path, zarr_path=zp, show_progress=False, overwrite=False)


def test_migrate_h5_to_zarr_overwrite(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "src.h5")
    zp = tmp_path / "out.zarr"
    migrate_h5_to_zarr(h5_path, zarr_path=zp, show_progress=False)
    # Act
    # Act
    out = migrate_h5_to_zarr(h5_path, zarr_path=zp, show_progress=False, overwrite=True)
    # Assert
    # Assert
    assert Path(out).exists()


def test_migrate_h5_to_zarr_corrupted_file(tmp_path):
    """Force the OSError branch by writing a junk HDF5 file."""
    # Arrange
    bad = tmp_path / "bad.h5"
    # Act
    bad.write_bytes(b"not-an-hdf5-file")
    # Assert
    with pytest.raises(Exception):
        migrate_h5_to_zarr(bad, zarr_path=tmp_path / "out.zarr", show_progress=False)


def test_migrate_h5_to_zarr_no_validate(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "v.h5")
    # Act
    # Act
    out = migrate_h5_to_zarr(
        h5_path,
        zarr_path=tmp_path / "v.zarr",
        show_progress=False,
        validate=False,
    )
    # Assert
    # Assert
    assert Path(out).exists()


def test_migrate_h5_to_zarr_compressor_none(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "nc.h5")
    # Act
    # Act
    out = migrate_h5_to_zarr(
        h5_path,
        zarr_path=tmp_path / "nc.zarr",
        compressor=None,
        show_progress=False,
    )
    # Assert
    # Assert
    assert Path(out).exists()


def test_migrate_h5_to_zarr_batch_sequential_len_results_is_2(tmp_path):
    # Arrange
    # Arrange
    h5_paths = []
    for i in range(2):
        p = _build_h5(tmp_path / f"a{i}.h5")
        h5_paths.append(p)
    out_dir = tmp_path / "out"
    # Act
    results = migrate_h5_to_zarr_batch(
        h5_paths, output_dir=out_dir, parallel=False, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert len(results) == 2


def test_migrate_h5_to_zarr_batch_sequential_all_path_r_exists_for_r_in_results(tmp_path):
    # Arrange
    # Arrange
    h5_paths = []
    for i in range(2):
        p = _build_h5(tmp_path / f"a{i}.h5")
        h5_paths.append(p)
    out_dir = tmp_path / "out"
    # Act
    results = migrate_h5_to_zarr_batch(
        h5_paths, output_dir=out_dir, parallel=False, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert all(Path(r).exists() for r in results)




def test_migrate_h5_to_zarr_batch_default_output_len_results_is_1(tmp_path):
    # Arrange
    # Arrange
    p = _build_h5(tmp_path / "b0.h5")
    # Act
    results = migrate_h5_to_zarr_batch([p], output_dir=None, parallel=False)
    # Act
    # Assert
    # Assert
    assert len(results) == 1


def test_migrate_h5_to_zarr_batch_default_output_path_results_0_exists(tmp_path):
    # Arrange
    # Arrange
    p = _build_h5(tmp_path / "b0.h5")
    # Act
    results = migrate_h5_to_zarr_batch([p], output_dir=None, parallel=False)
    # Act
    # Assert
    # Assert
    assert Path(results[0]).exists()




def test_migrate_h5_to_zarr_batch_error_swallowed(tmp_path):
    """One bad path should not break the batch; it should be reported and skipped."""
    # Arrange
    good = _build_h5(tmp_path / "g.h5")
    bad = tmp_path / "missing.h5"
    out_dir = tmp_path / "bout"
    # Act
    results = migrate_h5_to_zarr_batch(
        [bad, good], output_dir=out_dir, parallel=False, overwrite=True
    )
    # Good one should appear; bad one is reported but skipped.
    # Assert
    assert any(str(out_dir) in str(r) for r in results)


def test__migrate_sequential_direct_len_out_is_1(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "s.h5")
    zp = tmp_path / "s.zarr"
    # Act
    out = _migrate_sequential(
        [h5_path], [zp], compressor=None, chunks=True, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert len(out) == 1


def test__migrate_sequential_direct_path_out_0_exists(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "s.h5")
    zp = tmp_path / "s.zarr"
    # Act
    out = _migrate_sequential(
        [h5_path], [zp], compressor=None, chunks=True, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert Path(out[0]).exists()




def test_migrate_h5_to_zarr_batch_parallel_len_results_is_2(tmp_path):
    # Arrange
    # Arrange
    h5_paths = [_build_h5(tmp_path / f"p{i}.h5") for i in range(2)]
    out_dir = tmp_path / "pout"
    # Act
    results = migrate_h5_to_zarr_batch(
        h5_paths, output_dir=out_dir, parallel=True, n_workers=1, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert len(results) == 2


def test_migrate_h5_to_zarr_batch_parallel_all_path_r_exists_for_r_in_results(tmp_path):
    # Arrange
    # Arrange
    h5_paths = [_build_h5(tmp_path / f"p{i}.h5") for i in range(2)]
    out_dir = tmp_path / "pout"
    # Act
    results = migrate_h5_to_zarr_batch(
        h5_paths, output_dir=out_dir, parallel=True, n_workers=1, overwrite=True
    )
    # Act
    # Assert
    # Assert
    assert all(Path(r).exists() for r in results)




def test_migrate_h5_to_zarr_batch_parallel_default_workers(tmp_path):
    """Trigger the n_workers=None default-branch (parallel)."""
    # Arrange
    h5_paths = [_build_h5(tmp_path / f"q{i}.h5") for i in range(2)]
    out_dir = tmp_path / "qout"
    # Act
    results = migrate_h5_to_zarr_batch(
        h5_paths, output_dir=out_dir, parallel=True, overwrite=True
    )
    # Assert
    assert len(results) == 2


def test_migrate_h5_to_zarr_chunks_tuple(tmp_path):
    """chunks tuple is passed through to migrate_dataset for a single-dataset file."""
    # Use a single-dataset H5 file so the tuple shape matches.
    # Arrange
    h5p = tmp_path / "ct.h5"
    with h5py.File(h5p, "w") as f:
        f.create_dataset("flat", data=np.arange(24).reshape(4, 6), dtype="int32")
    # Act
    out = migrate_h5_to_zarr(
        h5p,
        zarr_path=tmp_path / "ct.zarr",
        chunks=(2, 3),
        show_progress=False,
    )
    # Assert
    assert Path(out).exists()


def test_migrate_h5_to_zarr_chunks_false(tmp_path):
    # Arrange
    # Arrange
    h5_path = _build_h5(tmp_path / "cf.h5")
    # Act
    # Act
    out = migrate_h5_to_zarr(
        h5_path,
        zarr_path=tmp_path / "cf.zarr",
        chunks=False,
        show_progress=False,
    )
    # Assert
    # Assert
    assert Path(out).exists()
