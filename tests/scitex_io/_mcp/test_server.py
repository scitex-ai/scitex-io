#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._mcp.server — exercises every @mcp.tool() in server.py.

Tests call the underlying decorated functions directly. FastMCP's @mcp.tool()
returns a normal callable, so server.io_save(...) works.
"""

import json
import os

import pandas as pd

from scitex_io._mcp import server

# ---------- module presence ----------


def test_module_imports_s_mcp_is_not_none():
    # Arrange
    # Arrange
    # Act
    from scitex_io._mcp import server as s
    # Act
    # Assert
    # Assert
    assert s.mcp is not None


def test_module_imports_s_mcp_name_scitex_io():
    # Arrange
    # Arrange
    # Act
    from scitex_io._mcp import server as s
    # Act
    # Assert
    # Assert
    assert s.mcp.name == "scitex-io"




# ---------- io_list_formats ----------


def test_io_list_formats_shape_r_is_dict():
    # Arrange
    # Arrange
    # Act
    r = server.io_list_formats()
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_list_formats_shape_set_r_keys_save_load():
    # Arrange
    # Arrange
    # Act
    r = server.io_list_formats()
    # Act
    # Assert
    # Assert
    assert set(r.keys()) >= {"save", "load"}




# ---------- io_register_info ----------


def test_io_register_info_shape_set_r_keys_description_save_example_load_example_note():
    # Arrange
    # Arrange
    # Act
    r = server.io_register_info()
    # Act
    # Assert
    # Assert
    assert set(r.keys()) >= {"description", "save_example", "load_example", "note"}


def test_io_register_info_shape_register_saver_in_r_save_example():
    # Arrange
    # Arrange
    # Act
    r = server.io_register_info()
    # Act
    # Assert
    # Assert
    assert "register_saver" in r["save_example"]


def test_io_register_info_shape_register_loader_in_r_load_example():
    # Arrange
    # Arrange
    # Act
    r = server.io_register_info()
    # Act
    # Assert
    # Assert
    assert "register_loader" in r["load_example"]




# ---------- io_save / io_load round-trips ----------


def test_io_save_load_json_save_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Act
    # Assert
    # Assert
    assert save_r["success"] is True


def test_io_save_load_json_os_path_exists_p(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Act
    # Assert
    # Assert
    assert os.path.exists(p)


def test_io_save_load_json_load_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    assert os.path.exists(p)
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert load_r["success"] is True


def test_io_save_load_json_load_r_type_in_dict(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    assert os.path.exists(p)
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert load_r["type"] in ("dict",)


def test_io_save_load_json_load_r_path_os_path_abspath_p(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    assert os.path.exists(p)
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert load_r["path"] == os.path.abspath(p)


def test_io_save_load_json_preview_in_load_r(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.json")
    payload = {"a": 1, "b": [1, 2, 3]}
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    assert os.path.exists(p)
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert "preview" in load_r




def test_io_save_load_yaml_save_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.yaml")
    # Act
    save_r = server.io_save(json.dumps({"k": "v"}), p)
    # Act
    # Assert
    # Assert
    assert save_r["success"] is True


def test_io_save_load_yaml_load_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "data.yaml")
    # Act
    save_r = server.io_save(json.dumps({"k": "v"}), p)
    # Assert
    assert save_r["success"] is True
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert load_r["success"] is True




def test_io_save_load_csv_save_r_success_is_true(tmp_path):
    # Save a list-of-dicts JSON to .csv — scitex_io handles via pandas
    # Arrange
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    # pass via JSON (list-of-records)
    payload = df.to_dict(orient="list")
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Act
    # Assert
    # Assert
    assert save_r["success"] is True


def test_io_save_load_csv_load_r_success_is_true(tmp_path):
    # Save a list-of-dicts JSON to .csv — scitex_io handles via pandas
    # Arrange
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    # pass via JSON (list-of-records)
    payload = df.to_dict(orient="list")
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert load_r["success"] is True


def test_io_save_load_csv_shape_in_load_r(tmp_path):
    # Save a list-of-dicts JSON to .csv — scitex_io handles via pandas
    # Arrange
    # Arrange
    p = str(tmp_path / "data.csv")
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    # pass via JSON (list-of-records)
    payload = df.to_dict(orient="list")
    # Act
    save_r = server.io_save(json.dumps(payload), p)
    # Assert
    assert save_r["success"] is True
    load_r = server.io_load(p, cache=False)
    # Act
    # Assert
    assert "shape" in load_r




def test_io_save_load_long_preview_truncated_r_success_is_true(tmp_path):
    # Make a load output whose repr exceeds 500 chars
    # Arrange
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_save_load_long_preview_truncated_r_preview_endswith(tmp_path):
    # Make a load output whose repr exceeds 500 chars
    # Arrange
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Act
    # Assert
    # Assert
    assert r["preview"].endswith("...")


def test_io_save_load_long_preview_truncated_len_r_preview_503(tmp_path):
    # Make a load output whose repr exceeds 500 chars
    # Arrange
    # Arrange
    p = str(tmp_path / "big.json")
    server.io_save(json.dumps({"k" + str(i): "v" * 20 for i in range(50)}), p)
    # Act
    r = server.io_load(p, cache=False)
    # Act
    # Assert
    # Assert
    assert len(r["preview"]) <= 503




def test_io_load_missing_returns_error_r_success_is_false(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = server.io_load(str(tmp_path / "does_not_exist.json"), cache=False)
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_load_missing_returns_error_error_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = server.io_load(str(tmp_path / "does_not_exist.json"), cache=False)
    # Act
    # Assert
    # Assert
    assert "error" in r




def test_io_save_bad_json_returns_error_r_success_is_false(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = server.io_save("not valid json {{{", str(tmp_path / "x.json"))
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_save_bad_json_returns_error_error_in_r(tmp_path):
    # Arrange
    # Arrange
    # Act
    r = server.io_save("not valid json {{{", str(tmp_path / "x.json"))
    # Act
    # Assert
    # Assert
    assert "error" in r




def test_io_save_unsupported_ext_envelope_r_is_dict(tmp_path):
    # scitex_io.save() swallows the unknown-ext error internally (logs it).
    # We only assert the envelope shape — either success=False or success=True.
    # Arrange
    # Arrange
    # Act
    r = server.io_save(json.dumps({"a": 1}), str(tmp_path / "x.totallyunknownext"))
    # Act
    # Assert
    # Assert
    assert isinstance(r, dict)


def test_io_save_unsupported_ext_envelope_success_in_r(tmp_path):
    # scitex_io.save() swallows the unknown-ext error internally (logs it).
    # We only assert the envelope shape — either success=False or success=True.
    # Arrange
    # Arrange
    # Act
    r = server.io_save(json.dumps({"a": 1}), str(tmp_path / "x.totallyunknownext"))
    # Act
    # Assert
    # Assert
    assert "success" in r




# ---------- io_load_configs ----------


def test_io_load_configs_happy_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_load_configs_happy_path_in_r_namespaces(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Act
    # Assert
    # Assert
    assert "PATH" in r["namespaces"]


def test_io_load_configs_happy_params_in_r_namespaces(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Act
    # Assert
    # Assert
    assert "PARAMS" in r["namespaces"]


def test_io_load_configs_happy_r_config_dir_os_path_abspath_str_cfg(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Act
    # Assert
    # Assert
    assert r["config_dir"] == os.path.abspath(str(cfg))


def test_io_load_configs_happy_isinstance_r_configs_dict(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "path.yaml").write_text("data_dir: /tmp/data\n")
    (cfg / "params.yaml").write_text("hidden_dim: 256\n")
    # Act
    r = server.io_load_configs(config_dir=str(cfg))
    # Act
    # Assert
    # Assert
    assert isinstance(r["configs"], dict)




def test_io_load_configs_missing_dir(tmp_path):
    # nonexistent path — function may either error or return empty namespaces.
    # Arrange
    # Act
    # Arrange
    # Act
    r = server.io_load_configs(config_dir=str(tmp_path / "no_such_dir"))
    # Either path exercised; just assert envelope shape.
    # Assert
    # Assert
    assert "success" in r


def test_io_load_configs_with_debug_flag(tmp_path):
    # Arrange
    # Arrange
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "params.yaml").write_text("VAL: 1\nDEBUG_VAL: 99\n")
    # Act
    # Act
    r = server.io_load_configs(config_dir=str(cfg), is_debug=True)
    # Assert
    # Assert
    assert r["success"] is True


# ---------- io_skills_list / io_skills_get ----------


def test_io_skills_list_real_package_r_success_is_true():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_skills_list_real_package_r_package_scitex_io():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert r["package"] == "scitex-io"


def test_io_skills_list_real_package_isinstance_r_skills_list():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert isinstance(r["skills"], list)


def test_io_skills_list_real_package_len_r_skills_0():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert len(r["skills"]) > 0


def test_io_skills_list_real_package_skill_not_in_r_skills():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert "SKILL" not in r["skills"]


def test_io_skills_list_real_package_any_save_and_load_in_name_for_name_in_r_skills():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert any("save-and-load" in name for name in r["skills"])




def test_io_skills_get_real_skill_r_success_is_true():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    skills = json.loads(raw)["skills"]
    name = skills[0]
    raw_get = server.io_skills_get(name)
    # Act
    r = json.loads(raw_get)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_skills_get_real_skill_r_name_name():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    skills = json.loads(raw)["skills"]
    name = skills[0]
    raw_get = server.io_skills_get(name)
    # Act
    r = json.loads(raw_get)
    # Act
    # Assert
    # Assert
    assert r["name"] == name


def test_io_skills_get_real_skill_isinstance_r_content_str():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    skills = json.loads(raw)["skills"]
    name = skills[0]
    raw_get = server.io_skills_get(name)
    # Act
    r = json.loads(raw_get)
    # Act
    # Assert
    # Assert
    assert isinstance(r["content"], str)


def test_io_skills_get_real_skill_len_r_content_0():
    # Arrange
    # Arrange
    raw = server.io_skills_list()
    skills = json.loads(raw)["skills"]
    name = skills[0]
    raw_get = server.io_skills_get(name)
    # Act
    r = json.loads(raw_get)
    # Act
    # Assert
    # Assert
    assert len(r["content"]) > 0




def test_io_skills_get_unknown_skill_r_success_is_false():
    # Arrange
    # Arrange
    raw = server.io_skills_get("nonexistent_skill_xyz")
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_skills_get_unknown_skill_available_in_r_error():
    # Arrange
    # Arrange
    raw = server.io_skills_get("nonexistent_skill_xyz")
    # Act
    r = json.loads(raw)
    # Act
    # Assert
    # Assert
    assert "available" in r["error"]




# ---------- Numpy/pickle round-trips ----------


def test_io_save_load_npy_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "arr.npy")
    payload = [1, 2, 3, 4]
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_save_load_npy_rr_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "arr.npy")
    payload = [1, 2, 3, 4]
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Assert
    assert r["success"] is True
    rr = server.io_load(p, cache=False)
    # Act
    # Assert
    assert rr["success"] is True


def test_io_save_load_npy_shape_in_rr(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "arr.npy")
    payload = [1, 2, 3, 4]
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Assert
    assert r["success"] is True
    rr = server.io_load(p, cache=False)
    # Act
    # Assert
    assert "shape" in rr




def test_io_save_load_pkl_r_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "obj.pkl")
    payload = {"k": [1, 2, 3]}
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Act
    # Assert
    # Assert
    assert r["success"] is True


def test_io_save_load_pkl_rr_success_is_true(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "obj.pkl")
    payload = {"k": [1, 2, 3]}
    # Act
    r = server.io_save(json.dumps(payload), p)
    # Assert
    assert r["success"] is True
    rr = server.io_load(p, cache=False)
    # Act
    # Assert
    assert rr["success"] is True




# ---------- resources ----------


def test_resources_register_scitex_io_in_cheatsheet():
    # Arrange
    # Arrange
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import CHEATSHEET, FORMATS, register_resources
    m = FastMCP(name="test")
    # Act
    register_resources(m)
    # Act
    # Assert
    # Assert
    assert "scitex-io" in CHEATSHEET


def test_resources_register_save_formats_in_formats():
    # Arrange
    # Arrange
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import CHEATSHEET, FORMATS, register_resources
    m = FastMCP(name="test")
    # Act
    register_resources(m)
    # Act
    # Assert
    # Assert
    assert "Save Formats" in FORMATS




def test_resources_readers_invoke_scitex_io_in_str_r1():
    # Arrange
    # Arrange
    import asyncio
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import register_resources
    m = FastMCP(name="test")
    register_resources(m)
    async def go():
        return (
            await m.read_resource("scitex-io://cheatsheet"),
            await m.read_resource("scitex-io://formats"),
        )
    # Act
    r1, r2 = asyncio.run(go())
    # Act
    # Assert
    # Assert
    assert "scitex-io" in str(r1)


def test_resources_readers_invoke_save_formats_in_str_r2():
    # Arrange
    # Arrange
    import asyncio
    from fastmcp import FastMCP
    from scitex_io._mcp._resources import register_resources
    m = FastMCP(name="test")
    register_resources(m)
    async def go():
        return (
            await m.read_resource("scitex-io://cheatsheet"),
            await m.read_resource("scitex-io://formats"),
        )
    # Act
    r1, r2 = asyncio.run(go())
    # Act
    # Assert
    # Assert
    assert "Save Formats" in str(r2)




# Trigger remaining `except Exception` paths in tools that wrap a function
# that normally won't fail. We use a temporary monkey-patch.


def test_io_load_configs_exception_path_r_success_is_false(monkeypatch, tmp_path):
    # Arrange
    # Arrange
    from scitex_io._mcp import server as server_mod
    def boom(**kwargs):
        raise RuntimeError("forced")
    monkeypatch.setattr("scitex_io.load_configs", boom)
    # Act
    r = server_mod.io_load_configs(config_dir=str(tmp_path))
    # Act
    # Assert
    # Assert
    assert r["success"] is False


def test_io_load_configs_exception_path_forced_in_r_error(monkeypatch, tmp_path):
    # Arrange
    # Arrange
    from scitex_io._mcp import server as server_mod
    def boom(**kwargs):
        raise RuntimeError("forced")
    monkeypatch.setattr("scitex_io.load_configs", boom)
    # Act
    r = server_mod.io_load_configs(config_dir=str(tmp_path))
    # Act
    # Assert
    # Assert
    assert "forced" in r["error"]




def test_io_skills_list_exception_path(monkeypatch):
    """Force io_skills_list into its except branch."""
    # Arrange
    from scitex_io._mcp import server as server_mod

    class BadPath:
        def __init__(self, *a, **kw):
            raise RuntimeError("boom-path")

    monkeypatch.setattr("scitex_io._mcp.server.Path", BadPath, raising=False)
    # The function imports Path inside the body — patch via builtins module
    monkeypatch.setattr("pathlib.Path", BadPath)
    raw = server_mod.io_skills_list()
    # Act
    r = json.loads(raw)
    # Assert
    assert r["success"] is False


def test_io_skills_get_exception_path(monkeypatch):
    # Arrange
    # Arrange
    from scitex_io._mcp import server as server_mod

    class BadPath:
        def __init__(self, *a, **kw):
            raise RuntimeError("boom-path")

    monkeypatch.setattr("pathlib.Path", BadPath)
    raw = server_mod.io_skills_get("anything")
    # Act
    # Act
    r = json.loads(raw)
    # Assert
    # Assert
    assert r["success"] is False


# EOF
