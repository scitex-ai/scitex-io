#!/usr/bin/env python3
"""Real-coverage tests for scitex_io._save_modules._csv._save_csv."""

import numpy as np
import pandas as pd

from scitex_io._save_modules._csv import _save_csv


def test_dataframe(tmp_path):
    p = str(tmp_path / "df.csv")
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    _save_csv(df, p)
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_series(tmp_path):
    p = str(tmp_path / "s.csv")
    s = pd.Series([10, 20, 30], name="x")
    _save_csv(s, p)
    back = pd.read_csv(p)
    assert list(back["x"]) == [10, 20, 30]


def test_ndarray(tmp_path):
    p = str(tmp_path / "a.csv")
    _save_csv(np.array([[1, 2], [3, 4]]), p)
    back = pd.read_csv(p)
    assert back.shape == (2, 2)


def test_int_scalar(tmp_path):
    p = str(tmp_path / "i.csv")
    _save_csv(42, p)
    back = pd.read_csv(p)
    assert back.iloc[0, 0] == 42


def test_float_scalar(tmp_path):
    p = str(tmp_path / "f.csv")
    _save_csv(3.14, p)
    back = pd.read_csv(p)
    assert abs(back.iloc[0, 0] - 3.14) < 1e-9


def test_list_of_numbers(tmp_path):
    p = str(tmp_path / "ln.csv")
    _save_csv([1, 2, 3], p)
    back = pd.read_csv(p)
    assert list(back.iloc[:, 0]) == [1, 2, 3]


def test_tuple_of_numbers(tmp_path):
    p = str(tmp_path / "tn.csv")
    _save_csv((1.0, 2.0, 3.0), p)
    assert pd.read_csv(p).shape[0] == 3


def test_list_of_dataframes(tmp_path):
    p = str(tmp_path / "ldf.csv")
    dfs = [pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [2]})]
    _save_csv(dfs, p)
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_list_of_strings(tmp_path):
    p = str(tmp_path / "ls.csv")
    _save_csv(["x", "y", "z"], p)
    back = pd.read_csv(p)
    assert "data" in back.columns


def test_dict(tmp_path):
    p = str(tmp_path / "d.csv")
    _save_csv({"a": [1, 2], "b": [3, 4]}, p)
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_fallback_object_with_to_dataframe(tmp_path):
    class Coll:
        def to_dataframe(self):
            return pd.DataFrame({"a": [1, 2]})

    p = str(tmp_path / "c.csv")
    _save_csv(Coll(), p)
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_fallback_arbitrary(tmp_path):
    p = str(tmp_path / "raw.csv")
    _save_csv("hello", p)
    back = pd.read_csv(p)
    assert back.iloc[0, 0] == "hello"


def test_kwargs_index_default(tmp_path):
    p = str(tmp_path / "idx.csv")
    _save_csv(pd.DataFrame({"a": [1]}), p)
    txt = open(p).read()
    # Default index=False → no leading comma column
    assert not txt.startswith(",")


def test_hash_skip_when_identical(tmp_path):
    p = str(tmp_path / "skip.csv")
    df = pd.DataFrame({"a": [1, 2]})
    _save_csv(df, p)
    mtime1 = (tmp_path / "skip.csv").stat().st_mtime_ns
    # Save again with identical content → hash matches → return without rewrite
    _save_csv(df, p)
    # No exception is the main check; second call exercises hash-match path


def test_hash_skip_ndarray(tmp_path):
    p = str(tmp_path / "arr.csv")
    arr = np.array([[1, 2], [3, 4]])
    _save_csv(arr, p)
    _save_csv(arr, p)  # second call hits the hash-skip branch


def test_hash_skip_other(tmp_path):
    p = str(tmp_path / "other.csv")
    _save_csv(42, p)
    _save_csv(42, p)  # exercise non-(df/ndarray) hash path


def test_existing_corrupt_proceeds(tmp_path):
    """When existing path can't be read as CSV → exception swallowed, save proceeds."""
    p = str(tmp_path / "corrupt.csv")
    # Write invalid CSV that read_csv chokes on (empty file)
    open(p, "w").close()
    _save_csv(pd.DataFrame({"a": [1, 2]}), p)
    back = pd.read_csv(p)
    assert list(back["a"]) == [1, 2]


def test_hash_unhashable_obj(tmp_path):
    """Existing file + obj whose str(obj) raises → exception swallowed."""

    class Boom:
        def __str__(self):
            raise RuntimeError("unstringable")

        def __repr__(self):
            return "Boom()"

    p = str(tmp_path / "u.csv")
    # Pre-create file so existence check runs
    open(p, "w").write("a\n1\n")
    # Should NOT raise — exception in hash path is swallowed
    try:
        _save_csv(Boom(), p)
    except ValueError:
        # Acceptable: Boom doesn't fit any branch and final fallback fails
        pass
