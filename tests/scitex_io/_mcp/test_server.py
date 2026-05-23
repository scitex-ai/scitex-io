#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._mcp.server — exercises every @mcp.tool() in server.py.

Tests call the underlying decorated functions directly. FastMCP's @mcp.tool()
returns a normal callable, so server.io_save(...) works.
"""

import json
import os
import pathlib

import pandas as pd
import scitex_io

from scitex_io._mcp import server

# ---------- module presence ----------


def test_module_imports_exposes_mcp_object():
    # Arrange
    from scitex_io._mcp import server as s
    # Act
    mcp_obj = s.mcp
    # Assert
    assert mcp_obj is not None


def test_module_imports_mcp_name_is_scitex_io():
    # Arrange
    from scitex_io._mcp import server as s
    # Act
    name = s.mcp.name
    # Assert
    assert name == "scitex-io"


# ---------- io_list_formats ----------


def test_io_list_formats_returns_dict_type():
    # Arrange
    # Act
    r = server.io_list_formats()
    # Assert
    assert isinstance(r, dict)


def test_io_list_formats_includes_save_and_load_keys():
    # Arrange
    # Act
    r = server.io_list_formats()
    # Assert
    assert set(r.keys()) >= {"save", "load"}


# ---------- io_register_info ----------


def test_io_register_info_includes_documented_keys():
    # Arrange
    # Act
    r = server.io_register_info()
    # Assert
    assert set(r.keys()) >= {"description", "save_example", "load_example", "note"}


def test_io_register_info_save_example_mentions_register_saver():
    # Arrange
    # Act
    r = server.io_register_info()
    # Assert
    assert "register_saver" in r["save_example"]


def test_io_register_info_load_example_mentions_register_loader():
    # Arrange
    # Act
    r = server.io_register_info()
    # Assert
    assert "register_loader" in r["load_example"]


# ---------- io_save / io_load round-trips ----------


def test_io_save_json_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True


def test_io_save_json_creates_file_on_disk(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    server.io_save(json.dumps(payload), p)
    # Assert
    assert os.path.exists(p)


def test_io_load_json_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    server.io_save(json.dumps({"a": 1, "b": [1, 2, 3]}), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert load_r["success"] is True


def test_io_load_json_reports_dict_type(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    server.io_save(json.dumps({"a": 1, "b": [1, 2, 3]}), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert load_r["type"] in ("dict",)


def test_io_load_json_reports_abspath(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    server.io_save(json.dumps({"a": 1, "b": [1, 2, 3]}), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert load_r["path"] == os.path.abspath(p)


def test_io_load_json_includes_preview_field(tmp_path):
    # Arrange
    p = str(tmp_path / "data.json")
    server.io_save(json.dumps({"a": 1, "b": [1, 2, 3]}), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert "preview" in load_r


def test_io_save_yaml_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.yaml")
    # Act
    save_r = server.io_save(json.dumps({"k": "v"}), p)
    # Assert
    assert save_r["success"] is True


def test_io_load_yaml_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.yaml")
    server.io_save(json.dumps({"k": "v"}), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert load_r["success"] is True


def test_io_save_csv_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    payload = df.to_dict(orient="list")
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True


def test_io_load_csv_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    server.io_save(json.dumps(df.to_dict(orient="list")), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert load_r["success"] is True


def test_io_load_csv_reports_shape(tmp_path):
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    server.io_save(json.dumps(df.to_dict(orient="list")), p)
    # Act
    load_r = server.io_load(p, cache=False)
    # Assert
    assert "shape" in load_r


def test_io_load_long_preview_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Assert
    assert r["success"] is True


def test_io_load_long_preview_truncated_with_ellipsis(tmp_path):
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Assert
    assert r["preview"].endswith("...")


def test_io_load_long_preview_capped_under_503(tmp_path):
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Assert
    assert len(r["preview"]) <= 503


def test_io_load_missing_returns_success_false(tmp_path):
    # Arrange
    # Act
    r = server.io_load(str(tmp_path / "does_not_exist.json"), cache=False)
    # Assert
    assert r["success"] is False


def test_io_load_missing_includes_error_field(tmp_path):
    # Arrange
    # Act
    r = server.io_load(str(tmp_path / "does_not_exist.json"), cache=False)
    # Assert
    assert "error" in r


def test_io_save_bad_json_returns_success_false(tmp_path):
    # Arrange
    # Act
    r = server.io_save("not valid json {{{", str(tmp_path / "x.json"))
    # Assert
    assert r["success"] is False


def test_io_save_bad_json_includes_error_field(tmp_path):
    # Arrange
    # Act
    r = server.io_save("not valid json {{{", str(tmp_path / "x.json"))
    # Assert
    assert "error" in r


def test_io_save_unsupported_ext_returns_dict(tmp_path):
    # Arrange
    # Act
    r = server.io_save(json.dumps({"a": 1}), str(tmp_path / "x.totallyunknownext"))
    # Assert
    assert isinstance(r, dict)


def test_io_save_unsupported_ext_has_success_field(tmp_path):
    # Arrange
    # Act
    r = server.io_save(json.dumps({"a": 1}), str(tmp_path / "x.totallyunknownext"))
    # Assert
    assert "success" in r


# ---------- io_load_configs ----------


def test_io_load_configs_happy_returns_success_true(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Assert
    assert r["success"] is True


def test_io_load_configs_happy_lists_path_namespace(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Assert
    assert "PATH" in r["namespaces"]


def test_io_load_configs_happy_lists_params_namespace(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Assert
    assert "PARAMS" in r["namespaces"]


def test_io_load_configs_happy_reports_abspath(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Assert
    assert r["config_dir"] == os.path.abspath(str(cfg))


def test_io_load_configs_happy_returns_configs_dict(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Assert
    assert isinstance(r["configs"], dict)


def test_io_load_configs_missing_dir_returns_envelope(tmp_path):
    # Arrange
    # Act
    r = server.io_load_configs(config_dir=str(tmp_path / "no_such_dir"))
    # Assert
    assert "success" in r


def test_io_load_configs_with_debug_flag_returns_success_true(tmp_path):
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "params.yaml").write_text("VAL: 1\nDEBUG_VAL: 99\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg), is_debug=True)
    # Assert
    assert r["success"] is True


# ---------- io_skills_list / io_skills_get ----------


def test_io_skills_list_returns_success_true():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert r["success"] is True


def test_io_skills_list_reports_package_scitex_io():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert r["package"] == "scitex-io"


def test_io_skills_list_skills_field_is_list_type():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert isinstance(r["skills"], list)


def test_io_skills_list_skills_is_nonempty():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert len(r["skills"]) > 0


def test_io_skills_list_skills_excludes_index_skill_md():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert "SKILL" not in r["skills"]


def test_io_skills_list_includes_known_save_and_load_skill():
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert any("save-and-load" in name for name in r["skills"])


def test_io_skills_get_known_skill_returns_success_true():
    # Arrange
    skills = json.loads(server.io_skills_list())["skills"]
    name = skills[0]
    # Act
    r = json.loads(server.io_skills_get(name))
    # Assert
    assert r["success"] is True


def test_io_skills_get_known_skill_echoes_name():
    # Arrange
    skills = json.loads(server.io_skills_list())["skills"]
    name = skills[0]
    # Act
    r = json.loads(server.io_skills_get(name))
    # Assert
    assert r["name"] == name


def test_io_skills_get_known_skill_content_is_string():
    # Arrange
    skills = json.loads(server.io_skills_list())["skills"]
    name = skills[0]
    # Act
    r = json.loads(server.io_skills_get(name))
    # Assert
    assert isinstance(r["content"], str)


def test_io_skills_get_known_skill_content_is_nonempty():
    # Arrange
    skills = json.loads(server.io_skills_list())["skills"]
    name = skills[0]
    # Act
    r = json.loads(server.io_skills_get(name))
    # Assert
    assert len(r["content"]) > 0


def test_io_skills_get_unknown_skill_returns_success_false():
    # Arrange
    # Act
    r = json.loads(server.io_skills_get("nonexistent_skill_xyz"))
    # Assert
    assert r["success"] is False


def test_io_skills_get_unknown_skill_error_mentions_available():
    # Arrange
    # Act
    r = json.loads(server.io_skills_get("nonexistent_skill_xyz"))
    # Assert
    assert "available" in r["error"]


# ---------- Numpy/pickle round-trips ----------


def test_io_save_npy_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "arr.npy")
    payload = [1, 2, 3, 4]
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Assert
    assert r["success"] is True


def test_io_load_npy_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "arr.npy")
    server.io_save(json.dumps([1, 2, 3, 4]), p)
    # Act
    rr = server.io_load(p, cache=False)
    # Assert
    assert rr["success"] is True


def test_io_load_npy_reports_shape(tmp_path):
    # Arrange
    p = str(tmp_path / "arr.npy")
    server.io_save(json.dumps([1, 2, 3, 4]), p)
    # Act
    rr = server.io_load(p, cache=False)
    # Assert
    assert "shape" in rr


def test_io_save_pkl_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "obj.pkl")
    payload = {"k": [1, 2, 3]}
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Assert
    assert r["success"] is True


def test_io_load_pkl_returns_success_true(tmp_path):
    # Arrange
    p = str(tmp_path / "obj.pkl")
    server.io_save(json.dumps({"k": [1, 2, 3]}), p)
    # Act
    rr = server.io_load(p, cache=False)
    # Assert
    assert rr["success"] is True


# ---------- resources ----------


def test_register_resources_populates_cheatsheet():
    # Arrange
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import CHEATSHEET, register_resources
    m = FastMCP(name="test")
    # Act
    register_resources(m)
    # Assert
    assert "scitex-io" in CHEATSHEET


def test_register_resources_populates_formats_doc():
    # Arrange
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import FORMATS, register_resources
    m = FastMCP(name="test")
    # Act
    register_resources(m)
    # Assert
    assert "Save Formats" in FORMATS


def test_resource_cheatsheet_reader_returns_scitex_io_text():
    # Arrange
    import asyncio
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import register_resources
    m = FastMCP(name="test")
    register_resources(m)
    # Act
    r1 = asyncio.run(m.read_resource("scitex-io://cheatsheet"))
    # Assert
    assert "scitex-io" in str(r1)


def test_resource_formats_reader_returns_save_formats_text():
    # Arrange
    import asyncio
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import register_resources
    m = FastMCP(name="test")
    register_resources(m)
    # Act
    r2 = asyncio.run(m.read_resource("scitex-io://formats"))
    # Assert
    assert "Save Formats" in str(r2)


# ---------- exception branches via attr_restore (no monkeypatch) ----------


def test_io_load_configs_when_helper_raises_returns_success_false(attr_restore, tmp_path):
    # Arrange
    def boom(**kwargs):
        raise RuntimeError("forced")
    attr_restore.set(scitex_io, "load_configs", boom)
    # Act
    r = server.io_load_configs(config_dir=str(tmp_path))
    # Assert
    assert r["success"] is False


def test_io_load_configs_when_helper_raises_propagates_error(attr_restore, tmp_path):
    # Arrange
    def boom(**kwargs):
        raise RuntimeError("forced")
    attr_restore.set(scitex_io, "load_configs", boom)
    # Act
    r = server.io_load_configs(config_dir=str(tmp_path))
    # Assert
    assert "forced" in r["error"]


def test_io_skills_list_when_path_raises_returns_success_false(attr_restore):
    # Arrange
    class BadPath:
        def __init__(self, *a, **kw):
            raise RuntimeError("boom-path")
    attr_restore.set(pathlib, "Path", BadPath)
    # Act
    r = json.loads(server.io_skills_list())
    # Assert
    assert r["success"] is False


def test_io_skills_get_when_path_raises_returns_success_false(attr_restore):
    # Arrange
    class BadPath:
        def __init__(self, *a, **kw):
            raise RuntimeError("boom-path")
    attr_restore.set(pathlib, "Path", BadPath)
    # Act
    r = json.loads(server.io_skills_get("anything"))
    # Assert
    assert r["success"] is False


# EOF
