#!/usr/bin/env python3
"""Real tests for _save_listed_dfs_as_csv."""


import pandas as pd

from scitex_io._save_modules._listed_dfs_as_csv import _save_listed_dfs_as_csv


def test_default_suffixes_n0_n_in_text_or_text_startswith_0_n(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "out.csv")
    dfs = [pd.DataFrame({"x": [1, 2]}), pd.DataFrame({"x": [3, 4]})]
    _save_listed_dfs_as_csv(dfs, p)
    # Act
    text = open(p).read()
    # Act
    # Assert
    # Assert
    assert "\n0\n" in text or text.startswith("0\n")


def test_default_suffixes_n_1_n_in_text(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "out.csv")
    dfs = [pd.DataFrame({"x": [1, 2]}), pd.DataFrame({"x": [3, 4]})]
    _save_listed_dfs_as_csv(dfs, p)
    # Act
    text = open(p).read()
    # Act
    # Assert
    # Assert
    assert "1\n" in text




def test_custom_suffixes_alpha_in_text(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "out2.csv")
    dfs = [pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]})]
    _save_listed_dfs_as_csv(dfs, p, indi_suffix=["alpha", "beta"])
    # Act
    text = open(p).read()
    # Act
    # Assert
    # Assert
    assert "alpha" in text


def test_custom_suffixes_beta_in_text(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "out2.csv")
    dfs = [pd.DataFrame({"x": [1]}), pd.DataFrame({"x": [2]})]
    _save_listed_dfs_as_csv(dfs, p, indi_suffix=["alpha", "beta"])
    # Act
    text = open(p).read()
    # Act
    # Assert
    # Assert
    assert "beta" in text




def test_verbose_saved_to_in_captured_out(tmp_path, capsys):
    # Arrange
    # Arrange
    p = str(tmp_path / "verb.csv")
    _save_listed_dfs_as_csv([pd.DataFrame({"x": [1]})], p, verbose=True)
    # Act
    # Act
    captured = capsys.readouterr()
    # Assert
    # Assert
    assert "Saved to" in captured.out


def test_overwrite_stale_not_in_open_p_read(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "ow.csv")
    # Create existing file first
    open(p, "w").write("stale\n")
    # Act
    # Act
    _save_listed_dfs_as_csv([pd.DataFrame({"x": [1, 2]})], p, overwrite=True)
    # File is rewritten — original "stale" should not remain at top
    # Assert
    # Assert
    assert "stale" not in open(p).read()


import pytest


@pytest.mark.parametrize("level, disabled", [("CRITICAL", False), ("INFO", True)])
def test_requested_display_survives_logging_threshold_and_disabled_logger(tmp_path, capsys, level, disabled):
    # Arrange: actual module logger; neither global configuration nor INFO masking.
    import importlib

    module = importlib.import_module('scitex_io._save_modules._listed_dfs_as_csv')
    previous = (module.log.level, module.log.disabled)
    path = str(tmp_path / "visible.csv")
    capsys.readouterr()
    try:
        module.log.setLevel(level)
        module.log.disabled = disabled
        # Act
        _save_listed_dfs_as_csv([pd.DataFrame({"x": [1]})], path, verbose=True)
        actual = capsys.readouterr().out
    finally:
        module.log.setLevel(previous[0])
        module.log.disabled = previous[1]
    # Assert: exact requested stdout payload and newline, independent of logger.
    assert actual == f"Saved to: {path}\n"
