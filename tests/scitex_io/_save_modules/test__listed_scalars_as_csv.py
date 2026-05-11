#!/usr/bin/env python3
"""Real tests for _save_listed_scalars_as_csv."""

import pandas as pd

from scitex_io._save_modules._listed_scalars_as_csv import (
    _save_listed_scalars_as_csv,
)


def test_basic_save(tmp_path):
    p = str(tmp_path / "s.csv")
    _save_listed_scalars_as_csv([1.234567, 2.345678, 3.456789], p)
    df = pd.read_csv(p, index_col=0)
    assert df.shape == (3, 1)
    # default round=3
    assert abs(df.iloc[0, 0] - 1.235) < 1e-6


def test_custom_column_and_suffix(tmp_path, capsys):
    p = str(tmp_path / "s2.csv")
    _save_listed_scalars_as_csv(
        [10, 20, 30],
        p,
        column_name="value",
        indi_suffix=["a", "b", "c"],
        verbose=True,
    )
    df = pd.read_csv(p, index_col=0)
    assert list(df.columns) == ["value"]
    assert list(df.index) == ["a", "b", "c"]
    captured = capsys.readouterr()
    assert "Saved to" in captured.out


def test_overwrite(tmp_path):
    p = str(tmp_path / "ow.csv")
    open(p, "w").write("stale\n")
    _save_listed_scalars_as_csv([1, 2], p, overwrite=True)
    text = open(p).read()
    assert "stale" not in text
