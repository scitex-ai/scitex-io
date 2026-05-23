#!/usr/bin/env python3
"""Real tests for _save_listed_scalars_as_csv."""

import pandas as pd

from scitex_io._save_modules._listed_scalars_as_csv import (
    _save_listed_scalars_as_csv,
)


def test_basic_save_df_shape_equals_n_3_1(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "s.csv")
    _save_listed_scalars_as_csv([1.234567, 2.345678, 3.456789], p)
    # Act
    df = pd.read_csv(p, index_col=0)
    # Act
    # Assert
    # Assert
    assert df.shape == (3, 1)


def test_basic_save_abs_df_iloc_0_0_1_235_1e_06(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "s.csv")
    _save_listed_scalars_as_csv([1.234567, 2.345678, 3.456789], p)
    # Act
    df = pd.read_csv(p, index_col=0)
    # Act
    # Assert
    # Assert
    assert abs(df.iloc[0, 0] - 1.235) < 1e-6




def test_custom_column_and_suffix_list_df_columns_value(tmp_path, capsys):
    # Arrange
    # Arrange
    p = str(tmp_path / "s2.csv")
    _save_listed_scalars_as_csv(
        [10, 20, 30],
        p,
        column_name="value",
        indi_suffix=["a", "b", "c"],
        verbose=True,
    )
    # Act
    df = pd.read_csv(p, index_col=0)
    # Act
    # Assert
    # Assert
    assert list(df.columns) == ["value"]


def test_custom_column_and_suffix_list_df_index_a_b_c(tmp_path, capsys):
    # Arrange
    # Arrange
    p = str(tmp_path / "s2.csv")
    _save_listed_scalars_as_csv(
        [10, 20, 30],
        p,
        column_name="value",
        indi_suffix=["a", "b", "c"],
        verbose=True,
    )
    # Act
    df = pd.read_csv(p, index_col=0)
    # Act
    # Assert
    # Assert
    assert list(df.index) == ["a", "b", "c"]


def test_custom_column_and_suffix_saved_to_in_captured_out(tmp_path, capsys):
    # Arrange
    # Arrange
    p = str(tmp_path / "s2.csv")
    _save_listed_scalars_as_csv(
        [10, 20, 30],
        p,
        column_name="value",
        indi_suffix=["a", "b", "c"],
        verbose=True,
    )
    # Act
    df = pd.read_csv(p, index_col=0)
    # Assert
    assert list(df.columns) == ["value"]
    assert list(df.index) == ["a", "b", "c"]
    captured = capsys.readouterr()
    # Act
    # Assert
    assert "Saved to" in captured.out




def test_overwrite_stale_not_in_text(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "ow.csv")
    open(p, "w").write("stale\n")
    _save_listed_scalars_as_csv([1, 2], p, overwrite=True)
    # Act
    # Act
    text = open(p).read()
    # Assert
    # Assert
    assert "stale" not in text
