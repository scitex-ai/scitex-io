#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._mcp._tools_extra — §6 parity MCP tools."""

import json
import os

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from scitex_io._mcp import _tools_extra

# ---------- io_glob / io_parse_glob ----------


def test_io_glob_plain_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "*.txt"))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_glob_plain_len_r_result_is_2(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "*.txt"))
    # Act
    # Assert
    # Assert
    assert len(r["result"]) == 2




def test_io_glob_parse_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_glob_parse_len_paths_is_2(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    # Assert
    assert r["success"] is True
    # parse=True returns (paths, parsed)
    paths, parsed = r["result"]
    # Act
    # Assert
    assert len(paths) == 2


def test_io_glob_parse_n_1_2_idxs(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "exp01.csv").write_text("")
    (tmp_path / "exp02.csv").write_text("")
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "exp{idx}.csv"), parse=True)
    # Assert
    assert r["success"] is True
    # parse=True returns (paths, parsed)
    paths, parsed = r["result"]
    assert len(paths) == 2
    idxs = {p.get("idx") for p in parsed}
    # Act
    # Assert
    assert {1, 2} <= idxs




def test_io_glob_ensure_one_failure_r_success_is_false(tmp_path):
    # 0 matches should fail (ensure_one)
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "no_match_*.xyz"), ensure_one=True)
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_glob_ensure_one_failure_error_in_r(tmp_path):
    # 0 matches should fail (ensure_one)
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_glob(str(tmp_path / "no_match_*.xyz"), ensure_one=True)
    # Act
    # Assert
    # Assert
    assert "error" in r




def test_io_parse_glob_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "foo.txt").write_text("")
    (tmp_path / "bar.txt").write_text("")
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "{name}.txt"))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_parse_glob_foo_bar_names(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "foo.txt").write_text("")
    (tmp_path / "bar.txt").write_text("")
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "{name}.txt"))
    # Assert
    assert r["success"] is True
    # parse_glob returns (paths, parsed) tuple
    parsed_part = r["parsed"]
    if isinstance(parsed_part, tuple):
        _paths, parsed = parsed_part
    else:
        parsed = parsed_part
    names = {d["name"] for d in parsed}
    # Act
    # Assert
    assert {"foo", "bar"} <= names




def test_io_parse_glob_error_ensure_one(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    r = _tools_extra.io_parse_glob(str(tmp_path / "no_such_{x}.q"), ensure_one=True)
    # Assert
    # Assert
    assert r["success"] is False


# ---------- io_get_loader / io_get_saver ----------


def test_io_get_loader_known_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_get_loader_known_r_ext_csv():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Act
    # Assert
    # Assert
    assert r["ext"] == ".csv"


def test_io_get_loader_known_r_loader_is_not_none():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Act
    # Assert
    # Assert
    assert r["loader"] is not None


def test_io_get_loader_known_in_r_loader():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".csv")
    # Act
    # Assert
    # Assert
    assert "." in r["loader"]




def test_io_get_loader_unknown_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".totallyunknownXYZ")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_get_loader_unknown_r_loader_is_none():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_loader(".totallyunknownXYZ")
    # Act
    # Assert
    # Assert
    assert r["loader"] is None




def test_io_get_saver_known_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".json")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_get_saver_known_r_saver_is_not_none():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".json")
    # Act
    # Assert
    # Assert
    assert r["saver"] is not None




def test_io_get_saver_unknown_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".totallyunknownXYZ")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_get_saver_unknown_r_saver_is_none():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_saver(".totallyunknownXYZ")
    # Act
    # Assert
    # Assert
    assert r["saver"] is None




# ---------- metadata tools ----------


def _make_png(path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    fig.savefig(path)
    plt.close(fig)


def test_io_has_metadata_empty_png_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    r = _tools_extra.io_has_metadata(str(p))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_has_metadata_empty_png_r_has_metadata_is_false(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    r = _tools_extra.io_has_metadata(str(p))
    # Act
    # Assert
    # Assert
    assert r["has_metadata"] is False




def test_io_embed_and_read_metadata_r1_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Act
    # Assert
    # Assert
    assert r1["success"] is True


def test_io_embed_and_read_metadata_r1_path_os_path_abspath_str_p(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Act
    # Assert
    # Assert
    assert r1["path"] == os.path.abspath(str(p))


def test_io_embed_and_read_metadata_r2_has_metadata_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r1["success"] is True
    assert r1["path"] == os.path.abspath(str(p))
    r2 = _tools_extra.io_has_metadata(str(p))
    # Act
    # Assert
    assert r2["has_metadata"] is True


def test_io_embed_and_read_metadata_r3_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r1["success"] is True
    assert r1["path"] == os.path.abspath(str(p))
    r2 = _tools_extra.io_has_metadata(str(p))
    assert r2["has_metadata"] is True
    r3 = _tools_extra.io_read_metadata(str(p))
    # Act
    # Assert
    assert r3["success"] is True


def test_io_embed_and_read_metadata_r3_metadata_k_v(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r1["success"] is True
    assert r1["path"] == os.path.abspath(str(p))
    r2 = _tools_extra.io_has_metadata(str(p))
    assert r2["has_metadata"] is True
    r3 = _tools_extra.io_read_metadata(str(p))
    # Act
    # Assert
    assert r3["metadata"]["k"] == "v"


def test_io_embed_and_read_metadata_r3_metadata_n_7(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    md = {"k": "v", "n": 7}
    # Act
    r1 = _tools_extra.io_embed_metadata(str(p), json.dumps(md))
    # Assert
    assert r1["success"] is True
    assert r1["path"] == os.path.abspath(str(p))
    r2 = _tools_extra.io_has_metadata(str(p))
    assert r2["has_metadata"] is True
    r3 = _tools_extra.io_read_metadata(str(p))
    # Act
    # Assert
    assert r3["metadata"]["n"] == 7




def test_io_read_metadata_missing_file_error_r_success_is_false(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_read_metadata(str(tmp_path / "nope.png"))
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_read_metadata_missing_file_error_error_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_read_metadata(str(tmp_path / "nope.png"))
    # Act
    # Assert
    # Assert
    assert "error" in r




def test_io_embed_metadata_missing_file_error(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    r = _tools_extra.io_embed_metadata(str(tmp_path / "nope.png"), "{}")
    # Assert
    # Assert
    assert r["success"] is False


def test_io_embed_metadata_bad_json(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "fig.png"
    _make_png(p)
    # Act
    # Act
    r = _tools_extra.io_embed_metadata(str(p), "not json {{{")
    # Assert
    # Assert
    assert r["success"] is False


# ---------- cache tools ----------


def test_io_get_cache_info_shape_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_cache_info()
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_get_cache_info_shape_any_k_in_r_for_k_in_stats_config_metadata_size_data_size():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_get_cache_info()
    # Act
    # Assert
    # Assert
    assert any(k in r for k in ("stats", "config", "metadata_size", "data_size"))




def test_io_clear_load_cache():
    # Arrange
    # Act
    # Arrange
    # Act
    r = _tools_extra.io_clear_load_cache()
    # Assert
    # Assert
    assert r["success"] is True


def test_io_configure_cache_toggle_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_configure_cache(enabled=False)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_configure_cache_toggle_r2_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_configure_cache(enabled=False)
    # Assert
    assert r["success"] is True
    # restore
    r2 = _tools_extra.io_configure_cache(enabled=True, max_size=32, verbose=False)
    # Act
    # Assert
    assert r2["success"] is True




# ---------- HDF5 tools ----------


def _make_h5(path):
    with h5py.File(path, "w") as f:
        f.create_dataset("a/b", data=np.arange(5))
        f.create_dataset("top", data=np.array([1.0, 2.0]))


def test_io_explore_h5_real_file_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "test.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_explore_h5(str(p))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_explore_h5_real_file_r_path_os_path_abspath_str_p(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "test.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_explore_h5(str(p))
    # Act
    # Assert
    # Assert
    assert r["path"] == os.path.abspath(str(p))




def test_io_explore_h5_missing_file_r_is_dict(tmp_path):
    # explore_h5 on missing file only warns (doesn't raise) → envelope is still
    # success=True. We just verify the envelope shape stays consistent.
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_explore_h5(str(tmp_path / "nope.h5"))
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_explore_h5_missing_file_success_in_r(tmp_path):
    # explore_h5 on missing file only warns (doesn't raise) → envelope is still
    # success=True. We just verify the envelope shape stays consistent.
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_explore_h5(str(tmp_path / "nope.h5"))
    # Act
    # Assert
    # Assert
    assert "success" in r




def test_io_has_h5_key_true_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "a/b")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_has_h5_key_true_r_has_key_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "a/b")
    # Act
    # Assert
    # Assert
    assert r["has_key"] is True




def test_io_has_h5_key_false_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "no/such/key")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_has_h5_key_false_r_has_key_is_false(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "k.h5"
    _make_h5(p)
    # Act
    r = _tools_extra.io_has_h5_key(str(p), "no/such/key")
    # Act
    # Assert
    # Assert
    assert r["has_key"] is False




def test_io_has_h5_key_missing_file_r_is_dict(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_has_h5_key(str(tmp_path / "nope.h5"), "x")
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_has_h5_key_missing_file_success_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_has_h5_key(str(tmp_path / "nope.h5"), "x")
    # Act
    # Assert
    # Assert
    assert "success" in r




# ---------- Zarr tools ----------


def _make_zarr(path):
    import zarr

    store = zarr.open(str(path), mode="w")
    arr = store.create_array("arr1", shape=(10,), dtype="int64")
    arr[:] = np.arange(10)


def test_io_explore_zarr_envelope_r_is_dict(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "test.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_explore_zarr_envelope_success_in_r(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "test.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Act
    # Assert
    # Assert
    assert "success" in r




def test_io_explore_zarr_missing_r_is_dict(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_explore_zarr(str(tmp_path / "nope.zarr"))
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_explore_zarr_missing_success_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_explore_zarr(str(tmp_path / "nope.zarr"))
    # Act
    # Assert
    # Assert
    assert "success" in r




def test_io_has_zarr_key_true_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "arr1")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_has_zarr_key_true_r_has_key_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "arr1")
    # Act
    # Assert
    # Assert
    assert r["has_key"] is True




def test_io_has_zarr_key_false_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "missing_key")
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_has_zarr_key_false_r_has_key_is_false(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "kz.zarr"
    _make_zarr(p)
    # Act
    r = _tools_extra.io_has_zarr_key(str(p), "missing_key")
    # Act
    # Assert
    # Assert
    assert r["has_key"] is False




def test_io_has_zarr_key_missing_store_r_is_dict(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_has_zarr_key(str(tmp_path / "no_such.zarr"), "k")
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_has_zarr_key_missing_store_success_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_has_zarr_key(str(tmp_path / "no_such.zarr"), "k")
    # Act
    # Assert
    # Assert
    assert "success" in r




# ---------- io_json2md ----------


def test_io_json2md_simple_r_success_is_true():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_json2md_simple_isinstance_r_markdown_str():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Act
    # Assert
    # Assert
    assert isinstance(r["markdown"], str)


def test_io_json2md_simple_a_in_r_markdown():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_json2md(json.dumps({"a": 1, "b": "x"}))
    # Act
    # Assert
    # Assert
    assert "a" in r["markdown"]




def test_io_json2md_nested_level_r_success_is_true():
    # Arrange
    # Arrange
    payload = {"section": {"sub": [1, 2, 3]}}
    # Act
    r = _tools_extra.io_json2md(json.dumps(payload), level=2)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_json2md_nested_level_section_in_r_markdown():
    # Arrange
    # Arrange
    payload = {"section": {"sub": [1, 2, 3]}}
    # Act
    r = _tools_extra.io_json2md(json.dumps(payload), level=2)
    # Act
    # Assert
    # Assert
    assert "section" in r["markdown"]




def test_io_json2md_bad_json_r_success_is_false():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_json2md("not valid {{{")
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_json2md_bad_json_error_in_r():
    # Arrange
    # Arrange
    # Act
    r = _tools_extra.io_json2md("not valid {{{")
    # Act
    # Assert
    # Assert
    assert "error" in r




# ---------- monkey-patched exception branches ----------


def test_io_has_metadata_exception_r_success_is_false(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-meta")
    monkeypatch.setattr("scitex_io.has_metadata", boom)
    # Act
    r = _tools_extra.io_has_metadata("/anything")
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_has_metadata_exception_forced_meta_in_r_error(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-meta")
    monkeypatch.setattr("scitex_io.has_metadata", boom)
    # Act
    r = _tools_extra.io_has_metadata("/anything")
    # Act
    # Assert
    # Assert
    assert "forced-meta" in r["error"]




def test_io_explore_h5_exception_r_success_is_false(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-h5")
    monkeypatch.setattr("scitex_io.explore_h5", boom)
    # Act
    r = _tools_extra.io_explore_h5("/anything")
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_explore_h5_exception_forced_h5_in_r_error(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p):
        raise RuntimeError("forced-h5")
    monkeypatch.setattr("scitex_io.explore_h5", boom)
    # Act
    r = _tools_extra.io_explore_h5("/anything")
    # Act
    # Assert
    # Assert
    assert "forced-h5" in r["error"]




def test_io_has_h5_key_exception_r_success_is_false(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-h5-key")
    monkeypatch.setattr("scitex_io.has_h5_key", boom)
    # Act
    r = _tools_extra.io_has_h5_key("/anything", "k")
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_has_h5_key_exception_forced_h5_key_in_r_error(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-h5-key")
    monkeypatch.setattr("scitex_io.has_h5_key", boom)
    # Act
    r = _tools_extra.io_has_h5_key("/anything", "k")
    # Act
    # Assert
    # Assert
    assert "forced-h5-key" in r["error"]




def test_io_explore_zarr_success_path_r_success_is_true(monkeypatch, tmp_path):
    # Arrange
    # Arrange
    def fake_explore(_p):
        return None
    monkeypatch.setattr("scitex_io.explore_zarr", fake_explore)
    p = tmp_path / "fake.zarr"
    p.mkdir()
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_explore_zarr_success_path_r_path_os_path_abspath_str_p(monkeypatch, tmp_path):
    # Arrange
    # Arrange
    def fake_explore(_p):
        return None
    monkeypatch.setattr("scitex_io.explore_zarr", fake_explore)
    p = tmp_path / "fake.zarr"
    p.mkdir()
    # Act
    r = _tools_extra.io_explore_zarr(str(p))
    # Act
    # Assert
    # Assert
    assert r["path"] == os.path.abspath(str(p))




def test_io_has_zarr_key_exception(monkeypatch):
    # Arrange
    # Arrange
    def boom(_p, _k):
        raise RuntimeError("forced-zarr-key")

    monkeypatch.setattr("scitex_io.has_zarr_key", boom)
    # Act
    # Act
    r = _tools_extra.io_has_zarr_key("/anything", "k")
    # Assert
    # Assert
    assert r["success"] is False


# EOF
