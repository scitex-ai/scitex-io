#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._save_modules._feather.

from __future__ import annotations
`_save_feather` accepts a DataFrame / dict / ndarray and writes a
Feather v2 file. Tests exercise:
  - DataFrame round-trip
  - dict → DataFrame coercion
  - ndarray → DataFrame coercion
  - kwargs pass-through to pandas
  - extension dispatch via scitex_io.save()
"""


import numpy as np
import pandas as pd
import pyarrow.feather as pf

from scitex_io._save_modules._feather import _save_feather


class TestSaveFeather:
    def test_dataframe_round_trip(self, tmp_path):
        # Arrange
        # Arrange
        df = pd.DataFrame({"x": [1, 2, 3], "y": [0.1, 0.2, 0.3]})
        out = tmp_path / "data.feather"
        # Act
        # Act
        _save_feather(df, str(out))
        # Assert
        # Assert
        assert out.is_file() and out.stat().st_size > 0
        back = pf.read_feather(str(out))
        pd.testing.assert_frame_equal(back, df)

    def test_dict_coerced_to_dataframe_preserves_values(self, tmp_path):
        # Arrange
        d = {"a": [1, 2], "b": ["x", "y"]}
        out = tmp_path / "data.feather"
        _save_feather(d, str(out))
        # Act
        back = pf.read_feather(str(out))
        # Assert
        assert back.equals(pd.DataFrame(d))

    def test_ndarray_coerced_to_dataframe_back_shape_equals_n_2_3(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.feather"
        _save_feather(arr, str(out))
        # Act
        back = pf.read_feather(str(out))
        # Act
        # Assert
        # Assert
        assert back.shape == (2, 3)

    def test_ndarray_coerced_to_dataframe_back_iloc_0_tolist_1_2_3(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.feather"
        _save_feather(arr, str(out))
        # Act
        back = pf.read_feather(str(out))
        # Act
        # Assert
        # Assert
        assert back.iloc[0].tolist() == [1, 2, 3]

    def test_ndarray_coerced_to_dataframe_back_iloc_1_tolist_4_5_6(self, tmp_path):
        # Arrange
        # Arrange
        arr = np.array([[1, 2, 3], [4, 5, 6]])
        out = tmp_path / "data.feather"
        _save_feather(arr, str(out))
        # Act
        back = pf.read_feather(str(out))
        # Act
        # Assert
        # Assert
        assert back.iloc[1].tolist() == [4, 5, 6]


    def test_kwargs_forwarded_size_uncompressed_0(self, tmp_path):
        # Arrange
        # Arrange
        df = pd.DataFrame({"x": list(range(100))})
        out = tmp_path / "data.feather"
        # Uncompressed should write
        _save_feather(df, str(out), compression="uncompressed")
        size_uncompressed = out.stat().st_size
        out2 = tmp_path / "data_zstd.feather"
        _save_feather(df, str(out2), compression="zstd")
        # Act
        size_zstd = out2.stat().st_size
        # Act
        # Assert
        # Assert
        assert size_uncompressed > 0

    def test_kwargs_forwarded_size_zstd_0(self, tmp_path):
        # Arrange
        # Arrange
        df = pd.DataFrame({"x": list(range(100))})
        out = tmp_path / "data.feather"
        # Uncompressed should write
        _save_feather(df, str(out), compression="uncompressed")
        size_uncompressed = out.stat().st_size
        out2 = tmp_path / "data_zstd.feather"
        _save_feather(df, str(out2), compression="zstd")
        # Act
        size_zstd = out2.stat().st_size
        # Act
        # Assert
        # Assert
        assert size_zstd > 0


    def test_dispatch_via_sio_save(self, tmp_path):
        """scitex_io.save dispatches .feather → _save_feather."""
        # Arrange
        import scitex_io as sio

        df = pd.DataFrame({"x": [1, 2, 3]})
        out = tmp_path / "data.feather"
        # Act
        sio.save(df, str(out), verbose=False)
        # Assert
        assert out.is_file()
        back = pf.read_feather(str(out))
        pd.testing.assert_frame_equal(back, df)
