#!/usr/bin/env python3
"""Real tests for _save_listed_dfs_as_csv."""


import pandas as pd

from scitex_io._save_modules._listed_dfs_as_csv import _save_listed_dfs_as_csv


def test_default_suffixes(tmp_path):
    p = str(tmp_path / "out.csv")
    dfs = [pd.DataFrame({"x": [1, 2]}), pd.DataFrame({"x": [3, 4]})]
    _save_listed_dfs_as_csv(dfs, p)
    text = open(p).read()
    # Default indi_suffix uses np.arange → row markers "0" and "1"
    assert "\n0\n" in text or text.startswith("0\n")
    assert "1\n" in text


def test_custom_suffixes(tmp_path):
    p = str(tmp_path / "out2.csv")
    dfs = [pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]})]
    _save_listed_dfs_as_csv(dfs, p, indi_suffix=["alpha", "beta"])
    text = open(p).read()
    assert "alpha" in text
    assert "beta" in text


def test_verbose(tmp_path, capsys):
    p = str(tmp_path / "verb.csv")
    _save_listed_dfs_as_csv([pd.DataFrame({"x": [1]})], p, verbose=True)
    captured = capsys.readouterr()
    assert "Saved to" in captured.out


def test_overwrite(tmp_path):
    p = str(tmp_path / "ow.csv")
    # Create existing file first
    open(p, "w").write("stale\n")
    _save_listed_dfs_as_csv([pd.DataFrame({"x": [1, 2]})], p, overwrite=True)
    # File is rewritten — original "stale" should not remain at top
    assert "stale" not in open(p).read()
