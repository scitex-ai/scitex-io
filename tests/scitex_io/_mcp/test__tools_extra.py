#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._mcp._tools_extra — §6 parity MCP tools."""

import json
import os

import h5py
import matplotlib
import numpy as np
import scitex_io

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scitex_io._mcp import _tools_extra

# ---------- io_glob / io_parse_glob ----------


def test_io_glob_plain_returns_success_true(tmp_path):
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "*.txt"))
    # Assert
    assert r["success"] is True


def test_io_glob_plain_finds_two_files(tmp_path):
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "*.txt"))
    # Assert
    assert len(r["result"]) == 2


def test_io_glob_parse_returns_success_true(tmp_path):
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    # Assert
    assert r["success"] is True


def test_io_glob_parse_returns_two_paths(tmp_path):
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    paths, _parsed = r["result"]
    # Assert
    assert len(paths) == 2


def test_io_glob_parse_extracts_idx_values(tmp_path):
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    _paths, parsed = r["result"]
    idxs = {p.get("idx") for p in parsed}
    # Assert
    assert {1, 2} <= idxs


def test_io_glob_ensure_one_zero_matches_returns_failure(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "no_match_*.zz"), ensure_one=True)
    # Assert
    assert r["success"] is False


def test_io_parse_glob_basic_returns_success_true(tmp_path):
    # Arrange
    (tmp_path / "foo.txt").write_text("")
    (tmp_path / "bar.txt").write_text("")
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "{name}.txt"))
    # Assert
    assert r["success"] is True


def test_io_parse_glob_extracts_name_values(tmp_path):
    # Arrange
    (tmp_path / "foo.txt").write_text("")
    (tmp_path / "bar.txt").write_text("")
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "{name}.txt"))
    parsed_part = r["parsed"]
    parsed = parsed_part[1] if isinstance(parsed_part, tuple) else parsed_part
    names = {d["name"] for d in parsed}
    # Assert
    assert {"foo", "bar"} <= names


def test_io_parse_glob_ensure_one_zero_matches_returns_failure(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "no_such_{x}.q"), ensure_one=True)
    # Assert
    assert r["success"] is False


# ---------- io_get_loader / io_get_saver ----------


def test_io_get_loader_known_extension_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Assert
    assert r["success"] is True


def test_io_get_loader_known_extension_echoes_ext():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Assert
    assert r["ext"] == ".csv"


def test_io_get_loader_known_extension_returns_loader_value():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Assert
    assert r["loader"] is not None


def test_io_get_loader_known_extension_loader_string_dotted():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Assert
    assert "." in r["loader"]


def test_io_get_loader_unknown_extension_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".totallyunknownXYZ")
    # Assert
    assert r["success"] is True


def test_io_get_loader_unknown_extension_loader_is_none():
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".totallyunknownXYZ")
    # Assert
    assert r["loader"] is None


def test_io_get_saver_known_extension_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".json")
    # Assert
    assert r["success"] is True


def test_io_get_saver_known_extension_returns_saver_value():
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".json")
    # Assert
    assert r["saver"] is not None


def test_io_get_saver_unknown_extension_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".totallyunknownXYZ")
    # Assert
    assert r["success"] is True


def test_io_get_saver_unknown_extension_saver_is_none():
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".totallyunknownXYZ")
    # Assert
    assert r["saver"] is None


# ---------- metadata tools ----------


def _make_png(path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    fig.savefig(path)
    plt.close(fig)


def test_io_has_metadata_empty_png_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    r = _tools_extra.io_has_metadata(str(p))
    # Assert
    assert r["success"] is True


def test_io_has_metadata_empty_png_reports_no_metadata(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    r = _tools_extra.io_has_metadata(str(p))
    # Assert
    assert r["has_metadata"] is False


def test_io_embed_metadata_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r["success"] is True


def test_io_embed_metadata_returns_abspath(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r["path"] == os.path.abspath(str(p))


def test_io_has_metadata_after_embed_reports_true(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    _tools_extra.io_embed_metadata(str(p), json.dumps({"k": "v"}))
    # Act
    r = _tools_extra.io_has_metadata(str(p))
    # Assert
    assert r["has_metadata"] is True


def test_io_read_metadata_after_embed_reports_success(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    _tools_extra.io_embed_metadata(str(p), json.dumps({"k": "v"}))
    # Act
    r = _tools_extra.io_read_metadata(str(p))
    # Assert
    assert r["success"] is True


def test_io_read_metadata_after_embed_returns_value(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    _tools_extra.io_embed_metadata(str(p), json.dumps({"k": "v", "n": 7}))
    # Act
    r = _tools_extra.io_read_metadata(str(p))
    # Assert
    assert r["metadata"]["k"] == "v"


def test_io_read_metadata_after_embed_returns_numeric(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    _tools_extra.io_embed_metadata(str(p), json.dumps({"k": "v", "n": 7}))
    # Act
    r = _tools_extra.io_read_metadata(str(p))
    # Assert
    assert r["metadata"]["n"] == 7


def test_io_read_metadata_missing_file_returns_failure(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_read_metadata(str(tmp_path / "nope.png"))
    # Assert
    assert r["success"] is False


def test_io_read_metadata_missing_file_includes_error_field(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_read_metadata(str(tmp_path / "nope.png"))
    # Assert
    assert "error" in r


def test_io_embed_metadata_missing_file_returns_failure(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_embed_metadata(str(tmp_path / "nope.png"), "{}")
    # Assert
    assert r["success"] is False


def test_io_embed_metadata_bad_json_returns_failure(tmp_path):
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    r = _tools_extra.io_embed_metadata(str(p), "not json {{{")
    # Assert
    assert r["success"] is False


# ---------- cache tools ----------


def test_io_get_cache_info_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_get_cache_info()
    # Assert
    assert r["success"] is True


def test_io_get_cache_info_includes_known_field():
    # Arrange
    # Act
    r = _tools_extra.io_get_cache_info()
    # Assert
    assert any(k in r for k in ("stats", "config", "metadata_size", "data_size"))


def test_io_clear_load_cache_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_clear_load_cache()
    # Assert
    assert r["success"] is True


def test_io_configure_cache_disable_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_configure_cache(enabled=False)
    # Assert
    assert r["success"] is True


def test_io_configure_cache_restore_returns_success_true():
    # Arrange
    _tools_extra.io_configure_cache(enabled=False)
    # Act
    r = _tools_extra.io_configure_cache(enabled=True, max_size=32, verbose=False)
    # Assert
    assert r["success"] is True


# ---------- HDF5 tools ----------


def _make_h5(path):
    with h5py.File(path, "w") as f:
        f.create_dataset("a/b", data=np.arange(5))
        f.create_dataset("top", data=np.array([1.0, 2.0]))


def test_io_explore_h5_real_file_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "test.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_explore_h5(str(p))
    # Assert
    assert r["success"] is True


def test_io_explore_h5_real_file_returns_abspath(tmp_path):
    # Arrange
    p = tmp_path / "test.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_explore_h5(str(p))
    # Assert
    assert r["path"] == os.path.abspath(str(p))


def test_io_explore_h5_missing_file_returns_dict(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_explore_h5(str(tmp_path / "nope.h5"))
    # Assert
    assert isinstance(r, dict)


def test_io_explore_h5_missing_file_has_success_field(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_explore_h5(str(tmp_path / "nope.h5"))
    # Assert
    assert "success" in r


def test_io_has_h5_key_present_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "a/b")
    # Assert
    assert r["success"] is True


def test_io_has_h5_key_present_reports_has_key_true(tmp_path):
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "a/b")
    # Assert
    assert r["has_key"] is True


def test_io_has_h5_key_absent_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "no/such/key")
    # Assert
    assert r["success"] is True


def test_io_has_h5_key_absent_reports_has_key_false(tmp_path):
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "no/such/key")
    # Assert
    assert r["has_key"] is False


def test_io_has_h5_key_missing_file_returns_dict(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_has_h5_key(str(tmp_path / "nope.h5"), "x")
    # Assert
    assert isinstance(r, dict)


def test_io_has_h5_key_missing_file_has_success_field(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_has_h5_key(str(tmp_path / "nope.h5"), "x")
    # Assert
    assert "success" in r


# ---------- Zarr tools ----------


def _make_zarr(path):
    import zarr

    store = zarr.open(str(path), mode="w")
    arr = store.create_array("arr1", shape=(10,), dtype="int64")
    arr[:] = np.arange(10)


def test_io_explore_zarr_returns_dict(tmp_path):
    # Arrange
    p = tmp_path / "test.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Assert
    assert isinstance(r, dict)


def test_io_explore_zarr_has_success_field(tmp_path):
    # Arrange
    p = tmp_path / "test.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Assert
    assert "success" in r


def test_io_explore_zarr_missing_returns_dict(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_explore_zarr(str(tmp_path / "nope.zarr"))
    # Assert
    assert isinstance(r, dict)


def test_io_explore_zarr_missing_has_success_field(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_explore_zarr(str(tmp_path / "nope.zarr"))
    # Assert
    assert "success" in r


def test_io_has_zarr_key_present_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "arr1")
    # Assert
    assert r["success"] is True


def test_io_has_zarr_key_present_reports_has_key_true(tmp_path):
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "arr1")
    # Assert
    assert r["has_key"] is True


def test_io_has_zarr_key_absent_returns_success_true(tmp_path):
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "missing_key")
    # Assert
    assert r["success"] is True


def test_io_has_zarr_key_absent_reports_has_key_false(tmp_path):
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "missing_key")
    # Assert
    assert r["has_key"] is False


def test_io_has_zarr_key_missing_store_returns_dict(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_has_zarr_key(str(tmp_path / "no_such.zarr"), "k")
    # Assert
    assert isinstance(r, dict)


def test_io_has_zarr_key_missing_store_has_success_field(tmp_path):
    # Arrange
    # Act
    r = _tools_extra.io_has_zarr_key(str(tmp_path / "no_such.zarr"), "k")
    # Assert
    assert "success" in r


# ---------- io_json2md ----------


def test_io_json2md_simple_returns_success_true():
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Assert
    assert r["success"] is True


def test_io_json2md_simple_markdown_is_string():
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Assert
    assert isinstance(r["markdown"], str)


def test_io_json2md_simple_markdown_includes_key_name():
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Assert
    assert "a" in r["markdown"]


def test_io_json2md_nested_level_returns_success_true():
    # Arrange
    payload = {"section": {"sub": [1, 2, 3]}}
    # Act
    r = _tools_extra.io_json2md(json.dumps(payload), level=2)
    # Assert
    assert r["success"] is True


def test_io_json2md_nested_markdown_includes_section_key():
    # Arrange
    payload = {"section": {"sub": [1, 2, 3]}}
    # Act
    r = _tools_extra.io_json2md(json.dumps(payload), level=2)
    # Assert
    assert "section" in r["markdown"]


def test_io_json2md_bad_json_returns_failure():
    # Arrange
    # Act
    r = _tools_extra.io_json2md("not valid {{{")
    # Assert
    assert r["success"] is False


def test_io_json2md_bad_json_includes_error_field():
    # Arrange
    # Act
    r = _tools_extra.io_json2md("not valid {{{")
    # Assert
    assert "error" in r


# ---------- collaborator-failure branches (attr swap, not mock) ----------


def test_io_has_metadata_when_helper_raises_returns_failure(attr_restore):
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-meta")
    attr_restore.set(scitex_io, "has_metadata", boom)
    # Act
    r = _tools_extra.io_has_metadata("/anything")
    # Assert
    assert r["success"] is False


def test_io_has_metadata_when_helper_raises_propagates_error(attr_restore):
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-meta")
    attr_restore.set(scitex_io, "has_metadata", boom)
    # Act
    r = _tools_extra.io_has_metadata("/anything")
    # Assert
    assert "forced-meta" in r["error"]


def test_io_explore_h5_when_helper_raises_returns_failure(attr_restore):
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-h5")
    attr_restore.set(scitex_io, "explore_h5", boom)
    # Act
    r = _tools_extra.io_explore_h5("/anything")
    # Assert
    assert r["success"] is False


def test_io_explore_h5_when_helper_raises_propagates_error(attr_restore):
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-h5")
    attr_restore.set(scitex_io, "explore_h5", boom)
    # Act
    r = _tools_extra.io_explore_h5("/anything")
    # Assert
    assert "forced-h5" in r["error"]


def test_io_has_h5_key_when_helper_raises_returns_failure(attr_restore):
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-h5-key")
    attr_restore.set(scitex_io, "has_h5_key", boom)
    # Act
    r = _tools_extra.io_has_h5_key("/anything", "k")
    # Assert
    assert r["success"] is False


def test_io_has_h5_key_when_helper_raises_propagates_error(attr_restore):
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-h5-key")
    attr_restore.set(scitex_io, "has_h5_key", boom)
    # Act
    r = _tools_extra.io_has_h5_key("/anything", "k")
    # Assert
    assert "forced-h5-key" in r["error"]


def test_io_explore_zarr_when_helper_succeeds_returns_success_true(attr_restore, tmp_path):
    # Arrange
    def fake_explore(_p):
        return None
    attr_restore.set(scitex_io, "explore_zarr", fake_explore)
    p = tmp_path / "fake.zarr"
    p.mkdir()
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Assert
    assert r["success"] is True


def test_io_explore_zarr_when_helper_succeeds_returns_abspath(attr_restore, tmp_path):
    # Arrange
    def fake_explore(_p):
        return None
    attr_restore.set(scitex_io, "explore_zarr", fake_explore)
    p = tmp_path / "fake.zarr"
    p.mkdir()
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Assert
    assert r["path"] == os.path.abspath(str(p))


def test_io_has_zarr_key_when_helper_raises_returns_failure(attr_restore):
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-zarr-key")
    attr_restore.set(scitex_io, "has_zarr_key", boom)
    # Act
    r = _tools_extra.io_has_zarr_key("/anything", "k")
    # Assert
    assert r["success"] is False


# EOF
