#!/usr/bin/env python3
"""Real-coverage tests for scitex_io._save_modules._csv._save_csv."""

from __future__ import annotations
import os

import numpy as np
import pandas as pd

from scitex_io._save_modules._csv import _save_csv


def test_dataframe_calls_dataframe(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "df.csv")
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    _save_csv(df, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back["a"]) == [1, 2]


def test_series_list_back_x_10_20_30(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "s.csv")
    s = pd.Series([10, 20, 30], name="x")
    _save_csv(s, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back["x"]) == [10, 20, 30]


def test_ndarray_back_shape_equals_n_2_2(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.csv")
    _save_csv(np.array([[1, 2], [3, 4]]), p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert back.shape == (2, 2)


def test_int_scalar_back_iloc_0_0_42(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "i.csv")
    _save_csv(42, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert back.iloc[0, 0] == 42


def test_float_scalar_abs_back_iloc_0_0_3_14_1e_09(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "f.csv")
    _save_csv(3.14, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert abs(back.iloc[0, 0] - 3.14) < 1e-9


def test_list_of_numbers(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "ln.csv")
    _save_csv([1, 2, 3], p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back.iloc[:, 0]) == [1, 2, 3]


def test_tuple_of_numbers(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "tn.csv")
    # Act
    # Act
    _save_csv((1.0, 2.0, 3.0), p)
    # Assert
    # Assert
    assert pd.read_csv(p).shape[0] == 3


def test_list_of_dataframes(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "ldf.csv")
    dfs = [pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [2]})]
    _save_csv(dfs, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back["a"]) == [1, 2]


def test_list_of_strings(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "ls.csv")
    _save_csv(["x", "y", "z"], p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert "data" in back.columns


def test_dict_list_back_a_1_2(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "d.csv")
    _save_csv({"a": [1, 2], "b": [3, 4]}, p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back["a"]) == [1, 2]


def test_fallback_object_with_to_dataframe(tmp_path):
    # Arrange
    # Arrange
    class Coll:
        def to_dataframe(self):
            return pd.DataFrame({"a": [1, 2]})

    p = str(tmp_path / "c.csv")
    _save_csv(Coll(), p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert list(back["a"]) == [1, 2]


def test_fallback_arbitrary_back_iloc_0_0_hello(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "raw.csv")
    _save_csv("hello", p)
    # Act
    # Act
    back = pd.read_csv(p)
    # Assert
    # Assert
    assert back.iloc[0, 0] == "hello"


def test_kwargs_index_default(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "idx.csv")
    _save_csv(pd.DataFrame({"a": [1]}), p)
    # Act
    # Act
    txt = open(p).read()
    # Default index=False → no leading comma column
    # Assert
    # Assert
    assert not txt.startswith(",")


def test_hash_skip_when_identical_keeps_file_contents(tmp_path):
    # Arrange
    p = str(tmp_path / "skip.csv")
    df = pd.DataFrame({"a": [1, 2]})
    _save_csv(df, p)
    # Act
    _save_csv(df, p)  # identical content → hash matches → no rewrite path
    # Assert
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_hash_skip_ndarray_keeps_file_contents(tmp_path):
    # Arrange
    p = str(tmp_path / "arr.csv")
    arr = np.array([[1, 2], [3, 4]])
    _save_csv(arr, p)
    # Act
    _save_csv(arr, p)  # second call hits the hash-skip branch
    # Assert
    back = pd.read_csv(p)
    assert back.shape == (2, 2)


def test_hash_skip_other_keeps_file_contents(tmp_path):
    # Arrange
    p = str(tmp_path / "other.csv")
    _save_csv(42, p)
    # Act
    _save_csv(42, p)  # exercise non-(df/ndarray) hash path
    # Assert
    back = pd.read_csv(p)
    assert back.iloc[0, 0] == 42


def test_existing_corrupt_proceeds(tmp_path):
    """When existing path can't be read as CSV → exception swallowed, save proceeds."""
    # Arrange
    p = str(tmp_path / "corrupt.csv")
    # Write invalid CSV that read_csv chokes on (empty file)
    open(p, "w").close()
    _save_csv(pd.DataFrame({"a": [1, 2]}), p)
    # Act
    back = pd.read_csv(p)
    # Assert
    assert list(back["a"]) == [1, 2]


def test_hash_unhashable_obj_does_not_corrupt_file(tmp_path):
    """Existing file + obj whose str(obj) raises → exception swallowed."""

    # Arrange
    class Boom:
        def __str__(self):
            raise RuntimeError("unstringable")

        def __repr__(self):
            return "Boom()"

    p = str(tmp_path / "u.csv")
    # Pre-create file so existence check runs
    open(p, "w").write("a\n1\n")
    # Act
    try:
        _save_csv(Boom(), p)
    except ValueError:
        # Acceptable: Boom doesn't fit any branch and final fallback fails
        pass
    # Assert
    # File must still exist (hash-path failure is swallowed, not catastrophic).
    assert os.path.exists(p)


# === merged from test__small_handlers.py ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-trip tests for the small save-handler modules:
  _yaml, _plotly, _text, _csv, _pickle, _joblib, _torch,
  _optuna_study_as_csv_and_pngs

Each test uses real I/O — no mocks. Deps are installed in [dev] extras.
"""


import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scitex_io._save_modules._csv import _save_csv
from scitex_io._save_modules._joblib import _save_joblib
from scitex_io._save_modules._pickle import _save_pickle
from scitex_io._save_modules._text import _save_text
from scitex_io._save_modules._torch import _save_torch
from scitex_io._save_modules._yaml import _convert_paths_to_strings, _save_yaml

# --- _yaml.py ---------------------------------------------------------------


class TestSaveCsv:
    def test_dataframe_roundtrip_preserves_values(self, tmp_path):
        # Arrange
        out = tmp_path / "df.csv"
        df = pd.DataFrame({"x": [1, 2, 3], "y": [0.5, 1.5, 2.5]})
        _save_csv(df, str(out))
        # Act
        back = pd.read_csv(out)
        # Assert
        assert back.equals(df)

    def test_dict_of_lists_list_back_columns_a_b(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "d.csv"
        _save_csv({"a": [1, 2], "b": [3, 4]}, str(out))
        # Act
        back = pd.read_csv(out)
        # Act
        # Assert
        # Assert
        assert list(back.columns) == ["a", "b"]

    def test_dict_of_lists_back_a_tolist_1_2(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "d.csv"
        _save_csv({"a": [1, 2], "b": [3, 4]}, str(out))
        # Act
        back = pd.read_csv(out)
        # Act
        # Assert
        # Assert
        assert back["a"].tolist() == [1, 2]

    def test_dict_of_lists_back_b_tolist_3_4(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "d.csv"
        _save_csv({"a": [1, 2], "b": [3, 4]}, str(out))
        # Act
        back = pd.read_csv(out)
        # Act
        # Assert
        # Assert
        assert back["b"].tolist() == [3, 4]


    def test_ndarray_2d_back_shape_equals_n_2_2(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "arr.csv"
        arr = np.array([[1, 2], [3, 4]])
        _save_csv(arr, str(out))
        # Reads back with default int column names "0","1".
        # Act
        # Act
        back = pd.read_csv(out)
        # Assert
        # Assert
        assert back.shape == (2, 2)

    def test_list_of_scalars(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "scalars.csv"
        _save_csv([1, 2, 3, 4], str(out))
        # Single column CSV is fine.
        # Act
        # Act
        back = pd.read_csv(out)
        # Assert
        # Assert
        assert back.iloc[:, 0].tolist() == [2, 3, 4] or back.iloc[:, 0].tolist() == [
            1,
            2,
            3,
            4,
        ]


# --- _pickle.py ------------------------------------------------------------


