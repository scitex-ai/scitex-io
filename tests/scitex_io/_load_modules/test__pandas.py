#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:40:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__pandas.py

"""Tests for pandas file loading functionality.

This module tests the pandas loading functions from scitex_io._load_modules._pandas,
including _load_csv, _load_tsv, _load_excel, and _load_parquet.
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
import numpy as np
import pandas as pd


def test_load_csv_basic_round_trips_with_index_col():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    df = pd.DataFrame(
        {"A": [1, 2, 3, 4, 5], "B": ["a", "b", "c", "d", "e"], "C": [1.1, 2.2, 3.3, 4.4, 5.5]}
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=True)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path, index_col=0)
        # Assert
        assert loaded_df.equals(df)
    finally:
        os.unlink(temp_path)


def test_load_csv_unnamed_index_column_removed():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    df = pd.DataFrame({"A": [1, 2, 3], "B": [7, 8, 9]})
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=True)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path)
        # Assert
        assert loaded_df.shape[1] == df.shape[1]
    finally:
        os.unlink(temp_path)


def test_load_csv_removes_explicit_unnamed_columns():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    df = pd.DataFrame(
        {
            "A": [1, 2, 3],
            "Unnamed: 1": [4, 5, 6],
            "B": [7, 8, 9],
            "Unnamed: 3": [10, 11, 12],
        }
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path, index_col=None)
        # Assert
        assert "Unnamed: 1" not in loaded_df.columns
    finally:
        os.unlink(temp_path)


def test_load_csv_keeps_named_columns():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    df = pd.DataFrame(
        {"A": [1, 2, 3], "Unnamed: 1": [4, 5, 6], "B": [7, 8, 9]}
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path, index_col=None)
        # Assert
        assert "A" in loaded_df.columns
    finally:
        os.unlink(temp_path)


def test_load_csv_parse_dates_returns_datetime_dtype():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    data = "date,value,category\n2023-01-01,100.5,A\n2023-01-02,200.3,B\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(data)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path, index_col=None, parse_dates=["date"])
        # Assert
        assert pd.api.types.is_datetime64_any_dtype(loaded_df["date"])
    finally:
        os.unlink(temp_path)


def test_load_csv_invalid_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    # Act
    ctx = pytest.raises(ValueError, match="File must have .csv extension")
    # Assert
    with ctx:
        _load_csv("test.txt")


def test_load_tsv_basic_round_trips_frame():
    # Arrange
    from scitex_io._load_modules._pandas import _load_tsv

    df = pd.DataFrame(
        {"col1": ["a", "b", "c"], "col2": [1, 2, 3], "col3": [1.1, 2.2, 3.3]}
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
        df.to_csv(f.name, sep="\t", index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_tsv(temp_path)
        # Assert
        assert loaded_df.equals(df)
    finally:
        os.unlink(temp_path)


def test_load_tsv_invalid_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pandas import _load_tsv

    # Act
    ctx = pytest.raises(ValueError, match="File must have .tsv extension")
    # Assert
    with ctx:
        _load_tsv("test.csv")


def test_load_excel_basic_round_trips_frame():
    # Arrange
    from scitex_io._load_modules._pandas import _load_excel

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        pytest.skip("openpyxl not available")
    df = pd.DataFrame(
        {"Name": ["Alice", "Bob", "Charlie"], "Age": [25, 30, 35], "Score": [85.5, 90.0, 78.5]}
    )
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        df.to_excel(f.name, index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_excel(temp_path)
        # Assert
        pd.testing.assert_frame_equal(loaded_df, df)
    finally:
        os.unlink(temp_path)


def test_load_excel_returns_first_sheet_frame_when_named():
    # Arrange
    from scitex_io._load_modules._pandas import _load_excel

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        pytest.skip("openpyxl not available")
    df1 = pd.DataFrame({"A": [1, 2, 3]})
    df2 = pd.DataFrame({"B": [4, 5, 6]})
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        with pd.ExcelWriter(f.name) as writer:
            df1.to_excel(writer, sheet_name="Sheet1", index=False)
            df2.to_excel(writer, sheet_name="Sheet2", index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df1 = _load_excel(temp_path, sheet_name="Sheet1")
        # Assert
        pd.testing.assert_frame_equal(loaded_df1, df1)
    finally:
        os.unlink(temp_path)


def test_load_excel_invalid_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pandas import _load_excel

    # Act
    ctx = pytest.raises(ValueError, match="File must have Excel extension")
    # Assert
    with ctx:
        _load_excel("test.csv")


def test_load_parquet_round_trips_frame():
    # Arrange
    from scitex_io._load_modules._pandas import _load_parquet

    try:
        import pyarrow  # noqa: F401
    except ImportError:
        pytest.skip("pyarrow not available")
    df = pd.DataFrame(
        {"int_col": [1, 2, 3], "float_col": [1.1, 2.2, 3.3], "str_col": ["a", "b", "c"]}
    )
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df.to_parquet(f.name)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_parquet(temp_path)
        # Assert
        pd.testing.assert_frame_equal(loaded_df, df)
    finally:
        os.unlink(temp_path)


def test_load_parquet_invalid_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._pandas import _load_parquet

    # Act
    ctx = pytest.raises(ValueError, match="File must have .parquet extension")
    # Assert
    with ctx:
        _load_parquet("test.csv")


def test_load_csv_nonexistent_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_csv("/nonexistent/path/file.csv")


def test_load_csv_large_file_returns_expected_row_count():
    # Arrange
    from scitex_io._load_modules._pandas import _load_csv

    n_rows = 1000
    df = pd.DataFrame(
        {
            "id": range(n_rows),
            "value": np.random.rand(n_rows),
            "category": np.random.choice(["A", "B", "C"], n_rows),
        }
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_path = f.name
    try:
        # Act
        loaded_df = _load_csv(temp_path, index_col=None)
        # Assert
        assert len(loaded_df) == n_rows
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
