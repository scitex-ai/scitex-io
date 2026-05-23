#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-file round-trip tests for scitex_io._save_modules._zarr.

from __future__ import annotations
The existing test__zarr.py is a placeholder. This file exercises the
full save path: directory store, zip store, key paths, compressors,
mixed-type dicts (str / scalar / array / object).
"""

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

from scitex_io._save_modules._zarr import _save_zarr


class TestSaveZarrDirectoryStore:
    def test_array_default_compressor(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.arange(100, dtype=np.float32).reshape(10, 10)
        out = str(tmp_path / "data.zarr")
        _save_zarr(arr, out)
        # Act
        # Act
        root = zarr.open(out, mode="r")
        # Assert
        # Assert
        assert "data" in root
        np.testing.assert_array_equal(root["data"][:], arr)

    def test_dict_top_level_int_root_scalar_42(self, tmp_path):
        # Arrange
        # Arrange
        d = {
            "arr": np.array([1, 2, 3, 4]),
            "scalar": 42,
            "name": "experiment-01",
            "flag": True,
        }
        out = str(tmp_path / "data.zarr")
        _save_zarr(d, out)
        root = zarr.open(out, mode="r")
        # Act
        np.testing.assert_array_equal(root["arr"][:], np.array([1, 2, 3, 4]))
        # Act
        # Assert
        # Assert
        assert int(root["scalar"][()]) == 42

    def test_dict_top_level_s_equals_experiment_01(self, tmp_path):
        # Arrange
        # Arrange
        d = {
            "arr": np.array([1, 2, 3, 4]),
            "scalar": 42,
            "name": "experiment-01",
            "flag": True,
        }
        out = str(tmp_path / "data.zarr")
        _save_zarr(d, out)
        root = zarr.open(out, mode="r")
        # Act
        np.testing.assert_array_equal(root["arr"][:], np.array([1, 2, 3, 4]))
        # Assert
        assert int(root["scalar"][()]) == 42
        # Strings get stored as numpy arrays — read back as bytes/str.
        s = root["name"][()]
        if isinstance(s, bytes):
            s = s.decode()
        # Act
        # Assert
        assert s == "experiment-01"

    def test_dict_top_level_bool_root_flag_is_true(self, tmp_path):
        # Arrange
        # Arrange
        d = {
            "arr": np.array([1, 2, 3, 4]),
            "scalar": 42,
            "name": "experiment-01",
            "flag": True,
        }
        out = str(tmp_path / "data.zarr")
        _save_zarr(d, out)
        root = zarr.open(out, mode="r")
        # Act
        np.testing.assert_array_equal(root["arr"][:], np.array([1, 2, 3, 4]))
        # Assert
        assert int(root["scalar"][()]) == 42
        # Strings get stored as numpy arrays — read back as bytes/str.
        s = root["name"][()]
        if isinstance(s, bytes):
            s = s.decode()
        # Act
        # Assert
        assert bool(root["flag"][()]) is True


    def test_key_creates_nested_group_session1_in_root(self, tmp_path):
        # Arrange
        # Arrange
        out = str(tmp_path / "data.zarr")
        _save_zarr(
            {"signal": np.arange(8)},
            out,
            key="session1/run3",
        )
        # Act
        root = zarr.open(out, mode="r")
        # Act
        # Assert
        # Assert
        assert "session1" in root

    def test_key_creates_nested_group_run3_in_root_session1(self, tmp_path):
        # Arrange
        # Arrange
        out = str(tmp_path / "data.zarr")
        _save_zarr(
            {"signal": np.arange(8)},
            out,
            key="session1/run3",
        )
        # Act
        root = zarr.open(out, mode="r")
        # Act
        # Assert
        # Assert
        assert "run3" in root["session1"]


    def test_key_overwrite_np_array_equal_root_group_a_x_np_arange_4_8(self, tmp_path):
        """Writing twice to the same key overrides cleanly."""
        # Arrange
        # Act
        # Assert
        out = str(tmp_path / "data.zarr")
        _save_zarr({"x": np.arange(4)}, out, key="group/a")
        _save_zarr({"x": np.arange(4, 8)}, out, key="group/a")
        root = zarr.open(out, mode="r")
        assert np.array_equal(root["group"]["a"]["x"][:], np.arange(4, 8))

    @pytest.mark.parametrize("comp", ["zstd", "lz4", "gzip"])
    def test_named_compressors_np_allclose_root_data_arr(self, tmp_path, comp):
        # Arrange
        # Act
        # Assert
        # Arrange
        arr = np.random.default_rng(0).normal(size=(50, 50)).astype(np.float32)
        out = str(tmp_path / f"data_{comp}.zarr")
        _save_zarr(arr, out, compressor=comp)
        # Act
        root = zarr.open(out, mode="r")
        # Assert
        assert np.allclose(root["data"][:], arr)

    def test_unknown_compressor_falls_back_to_zstd(self, tmp_path):
        """Implementation maps unknown names to zstd default."""
        # Arrange
        # Act
        # Assert
        out = str(tmp_path / "data.zarr")
        _save_zarr(np.arange(10), out, compressor="not-a-real-codec")
        root = zarr.open(out, mode="r")
        assert np.array_equal(root["data"][:], np.arange(10))

    def test_object_array_pickled(self, tmp_path):
        """Object-dtype arrays are pickled and tagged via _type attr."""
        # Lists become object arrays after np.asarray; alternatively
        # provide a dict whose value is a non-array object.
        # Arrange
        out = str(tmp_path / "data.zarr")
        obj = {"meta": np.array([{"a": 1}, {"b": 2}], dtype=object)}
        _save_zarr(obj, out, compressor="zstd")
        # Act
        root = zarr.open(out, mode="r")
        # The pickled tag should be present.
        # Assert
        assert root["meta"].attrs.get("_type") == "pickled"

    def test_consolidate_metadata_directory_store(self, tmp_path, capsys):
        # Arrange
        # Arrange
        out = str(tmp_path / "data.zarr")
        _save_zarr({"x": np.arange(4)}, out, consolidate_metadata=True)
        # Either consolidated or fallback line should print.
        # Act
        # Act
        captured = capsys.readouterr()
        # Assert
        # Assert
        assert "Saved to Zarr" in captured.out


class TestSaveZarrZipStore:
    def test_zip_store_round_trip(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        out = str(tmp_path / "data.zarr.zip")
        _save_zarr({"x": np.arange(16, dtype=np.int64)}, out)
        # Open the zip store directly to verify.
        store = zarr.storage.ZipStore(out, mode="r")
        try:
            root = zarr.open(store, mode="r")
            np.testing.assert_array_equal(root["x"][:], np.arange(16))
        finally:
            store.close()

    def test_zip_store_extension_zip(self, tmp_path):
        """A bare .zip path also routes to the ZipStore code path."""
        # Arrange
        # Act
        # Assert
        out = str(tmp_path / "data.zip")
        _save_zarr({"y": np.arange(5)}, out)
        store = zarr.storage.ZipStore(out, mode="r")
        try:
            root = zarr.open(store, mode="r")
            np.testing.assert_array_equal(root["y"][:], np.arange(5))
        finally:
            store.close()


class TestSaveZarrEdgeCases:
    def test_overwrite_existing_file(self, tmp_path):
        """Path exists as a regular file → implementation removes
        it and creates a directory store in its place."""
        # Arrange
        out = tmp_path / "data.zarr"
        out.write_bytes(b"stale content")
        # Act
        _save_zarr({"x": np.arange(3)}, str(out))
        # Assert
        assert out.is_dir(), "should now be a directory store"
        root = zarr.open(str(out), mode="r")
        np.testing.assert_array_equal(root["x"][:], np.arange(3))

    def test_explicit_directory_store_type(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        out = str(tmp_path / "data.zarr")
        _save_zarr({"x": np.arange(3)}, out, store_type="directory")
        # Act
        root = zarr.open(out, mode="r")
        # Assert
        assert np.array_equal(root["x"][:], np.arange(3))

    def test_explicit_zip_store_type(self, tmp_path):
        # When store_type=zip is forced, even non-.zip extensions
        # should route to ZipStore.
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        out = str(tmp_path / "data.bin")
        _save_zarr({"x": np.arange(3)}, out, store_type="zip")
        store = zarr.storage.ZipStore(out, mode="r")
        try:
            root = zarr.open(store, mode="r")
            np.testing.assert_array_equal(root["x"][:], np.arange(3))
        finally:
            store.close()
