#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._save_modules._parquet.

from __future__ import annotations
`_save_parquet` accepts a DataFrame / dict / ndarray and writes a
Parquet file. Tests exercise:
  - DataFrame round-trip
  - dict / ndarray coercion
  - kwargs pass-through (compression, engine)
  - extension dispatch via scitex_io.save()
"""


import numpy as np
import pandas as pd

from scitex_io._save_modules._parquet import _save_parquet


class TestSaveParquet:
    def test_dataframe_round_trip(self, tmp_path):
        # Arrange
        # Arrange
        df = pd.DataFrame({"x": [1, 2, 3], "y": [0.1, 0.2, 0.3]})
        out = tmp_path / "data.parquet"
        # Act
        # Act
        _save_parquet(df, str(out))
        # Assert
        # Assert
        assert out.is_file() and out.stat().st_size > 0
        back = pd.read_parquet(str(out))
        pd.testing.assert_frame_equal(back, df)

    def test_dict_coerced_to_dataframe_preserves_values(self, tmp_path):
        # Arrange
        d = {"a": [1, 2, 3], "b": ["x", "y", "z"]}
        out = tmp_path / "data.parquet"
        _save_parquet(d, str(out))
        # Act
        back = pd.read_parquet(str(out))
        # Assert
        assert back.equals(pd.DataFrame(d))

    def test_ndarray_coerced_to_dataframe_back_shape_equals_n_2_3(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.parquet"
        _save_parquet(arr, str(out))
        # Act
        back = pd.read_parquet(str(out))
        # Act
        # Assert
        # Assert
        assert back.shape == (2, 3)

    def test_ndarray_coerced_to_dataframe_back_iloc_0_tolist_1_2_3(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.parquet"
        _save_parquet(arr, str(out))
        # Act
        back = pd.read_parquet(str(out))
        # Act
        # Assert
        # Assert
        assert back.iloc[0].tolist() == [1, 2, 3]

    def test_ndarray_coerced_to_dataframe_back_iloc_1_tolist_4_5_6(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.parquet"
        _save_parquet(arr, str(out))
        # Act
        back = pd.read_parquet(str(out))
        # Act
        # Assert
        # Assert
        assert back.iloc[1].tolist() == [4, 5, 6]


    def test_compression_kwarg_forwarded(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        df = pd.DataFrame({"x": list(range(500))})
        out_snap = tmp_path / "snappy.parquet"
        out_gzip = tmp_path / "gzip.parquet"
        _save_parquet(df, str(out_snap), compression="snappy")
        _save_parquet(df, str(out_gzip), compression="gzip")
        # Both should write and both should round-trip.
        for p in (out_snap, out_gzip):
            assert p.stat().st_size > 0
            pd.testing.assert_frame_equal(pd.read_parquet(str(p)), df)

    def test_dispatch_via_sio_save(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        df = pd.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        out = tmp_path / "data.parquet"
        # Act
        # Act
        sio.save(df, str(out), verbose=False)
        # Assert
        # Assert
        assert out.is_file()
        back = pd.read_parquet(str(out))
        pd.testing.assert_frame_equal(back, df)
