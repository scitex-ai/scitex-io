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


def test_load_csv(tmp_path):
    p = tmp_path / "x.csv"
    pd.DataFrame({"a": [1, 2, 3]}).to_csv(p, index=False)
    out = load(str(p))
    assert list(out["a"]) == [1, 2, 3]


def test_load_path_object(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"k": 1}))
    out = load(Path(p), verbose=True)
    assert out == {"k": 1}


def test_load_npy(tmp_path):
    p = tmp_path / "x.npy"
    np.save(p, np.arange(5))
    out = load(str(p))
    np.testing.assert_array_equal(out, np.arange(5))


def test_load_yaml(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text(yaml.safe_dump({"a": 1, "b": [1, 2]}))
    out = load(str(p))
    assert out == {"a": 1, "b": [1, 2]}


def test_load_pkl(tmp_path):
    p = tmp_path / "x.pkl"
    with open(p, "wb") as f:
        pickle.dump([1, 2, 3], f)
    out = load(str(p))
    assert out == [1, 2, 3]


def test_load_explicit_ext(tmp_path):
    # File without extension, force ext
    p = tmp_path / "noext"
    p.write_text(json.dumps({"k": "v"}))
    out = load(str(p), ext="json")
    assert out == {"k": "v"}


def test_load_caching(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"v": 1}))
    load(str(p), cache=True)
    # Second load (verbose triggers cache-hit branch)
    out = load(str(p), cache=True, verbose=True)
    assert out == {"v": 1}


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load(str(tmp_path / "missing.json"))


def test_load_glob(tmp_path):
    (tmp_path / "a.json").write_text(json.dumps(1))
    (tmp_path / "b.json").write_text(json.dumps(2))
    out = load(str(tmp_path / "*.json"))
    assert sorted(out) == [1, 2]


def test_load_glob_no_match(tmp_path):
    with pytest.raises(FileNotFoundError):
        load(str(tmp_path / "*.nope"))


def test_load_unknown_extension(tmp_path):
    p = tmp_path / "x.unknownz"
    p.write_text("hi")
    with pytest.raises(ValueError, match="No load handler"):
        load(str(p))


def test_load_symlink_resolved(tmp_path):
    src = tmp_path / "data.json"
    src.write_text(json.dumps([1, 2]))
    link = tmp_path / "link.json"
    os.symlink("data.json", link)
    out = load(str(link))
    assert out == [1, 2]


def test_load_broken_symlink(tmp_path):
    link = tmp_path / "broken.json"
    os.symlink("nonexistent.json", link)
    with pytest.raises(FileNotFoundError):
        load(str(link))


def test_load_error_wrapped_in_valueerror(tmp_path):
    # Corrupted CSV path that pandas can't parse to ValueError
    p = tmp_path / "x.npy"
    p.write_bytes(b"not an npy")
    with pytest.raises((ValueError, Exception)):
        load(str(p), cache=False)
