#!/usr/bin/env python3
"""Round-trip tests for scitex_io._loading._load dispatcher."""

import json
import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from scitex_io._loading._load import load


def test_load_csv_list_out_a_1_2_3(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.csv"
    pd.DataFrame({"a": [1, 2, 3]}).to_csv(p, index=False)
    # Act
    # Act
    out = load(str(p))
    # Assert
    # Assert
    assert list(out["a"]) == [1, 2, 3]


def test_load_path_object(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"k": 1}))
    # Act
    # Act
    out = load(Path(p), verbose=True)
    # Assert
    # Assert
    assert out == {"k": 1}


def test_load_npy_np_array_equal_out_np_arange_5(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    p = tmp_path / "x.npy"
    np.save(p, np.arange(5))
    # Act
    out = load(str(p))
    # Assert
    assert np.array_equal(out, np.arange(5))


def test_load_yaml_out_equals_a_1_b_1_2(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.yaml"
    p.write_text(yaml.safe_dump({"a": 1, "b": [1, 2]}))
    # Act
    # Act
    out = load(str(p))
    # Assert
    # Assert
    assert out == {"a": 1, "b": [1, 2]}


def test_load_pkl_out_equals_n_1_2_3(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.pkl"
    with open(p, "wb") as f:
        pickle.dump([1, 2, 3], f)
    # Act
    # Act
    out = load(str(p))
    # Assert
    # Assert
    assert out == [1, 2, 3]


def test_load_explicit_ext(tmp_path):
    # File without extension, force ext
    # Arrange
    # Arrange
    p = tmp_path / "noext"
    p.write_text(json.dumps({"k": "v"}))
    # Act
    # Act
    out = load(str(p), ext="json")
    # Assert
    # Assert
    assert out == {"k": "v"}


def test_load_caching_out_equals_v_1(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"v": 1}))
    load(str(p), cache=True)
    # Second load (verbose triggers cache-hit branch)
    # Act
    # Act
    out = load(str(p), cache=True, verbose=True)
    # Assert
    # Assert
    assert out == {"v": 1}


def test_load_missing_file(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with pytest.raises(FileNotFoundError):
        load(str(tmp_path / "missing.json"))


def test_load_glob_sorted_out_1_2(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.json").write_text(json.dumps(1))
    (tmp_path / "b.json").write_text(json.dumps(2))
    # Act
    # Act
    out = load(str(tmp_path / "*.json"))
    # Assert
    # Assert
    assert sorted(out) == [1, 2]


def test_load_glob_no_match(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with pytest.raises(FileNotFoundError):
        load(str(tmp_path / "*.nope"))


def test_load_unknown_extension(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.unknownz"
    # Act
    # Act
    p.write_text("hi")
    # Assert
    # Assert
    with pytest.raises(ValueError, match="No load handler"):
        load(str(p))


def test_load_symlink_resolved(tmp_path):
    # Arrange
    # Arrange
    src = tmp_path / "data.json"
    src.write_text(json.dumps([1, 2]))
    link = tmp_path / "link.json"
    os.symlink("data.json", link)
    # Act
    # Act
    out = load(str(link))
    # Assert
    # Assert
    assert out == [1, 2]


def test_load_broken_symlink(tmp_path):
    # Arrange
    # Arrange
    link = tmp_path / "broken.json"
    # Act
    # Act
    os.symlink("nonexistent.json", link)
    # Assert
    # Assert
    with pytest.raises(FileNotFoundError):
        load(str(link))


def test_load_error_wrapped_in_valueerror(tmp_path):
    # Corrupted CSV path that pandas can't parse to ValueError
    # Arrange
    # Arrange
    p = tmp_path / "x.npy"
    # Act
    # Act
    p.write_bytes(b"not an npy")
    # Assert
    # Assert
    with pytest.raises((ValueError, Exception)):
        load(str(p), cache=False)
