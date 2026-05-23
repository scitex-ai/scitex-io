#!/usr/bin/env python3
"""Tests for scitex_io._linter_plugin."""

from scitex_dev.linter.checker import lint_source

from scitex_io._linter_plugin import (
    _REGISTER_HINT,
    _builtin_extensions,
    _UnknownExtChecker,
    get_plugin,
)


def _ids(issues):
    return [i.rule.id for i in issues]


def test_get_plugin_shape_set_p_keys_rules_call_rules_axes_hints_checkers():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert set(p.keys()) >= {"rules", "call_rules", "axes_hints", "checkers"}


def test_get_plugin_shape_expected_rule_ids():
    # Arrange
    expected = {f"STX-IO{n:03d}" for n in range(1, 15)} | {
        f"STX-PA{n:03d}" for n in range(1, 6)
    }
    # Act
    rule_ids = {r.id for r in get_plugin()["rules"]}
    # Assert
    assert expected <= rule_ids


def test_get_plugin_shape_any_c_is_unknownextchecker_for_c_in_p_checkers():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert any(c is _UnknownExtChecker for c in p["checkers"])


def test_get_plugin_shape_p_axes_hints():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert p["axes_hints"] == {}


def test_get_plugin_shape_np_save_in_p_call_rules():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert ("np", "save") in p["call_rules"]


def test_get_plugin_shape_pickle_dump_in_p_call_rules():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert ("pickle", "dump") in p["call_rules"]


def test_get_plugin_shape_os_chdir_in_p_call_rules():
    # Arrange
    # Act
    p = get_plugin()
    # Assert
    assert ("os", "chdir") in p["call_rules"]




def test_builtin_extensions_includes_common_csv_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".csv" in exts


def test_builtin_extensions_includes_common_npy_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".npy" in exts


def test_builtin_extensions_includes_common_pkl_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".pkl" in exts


def test_builtin_extensions_includes_common_h5_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".h5" in exts


def test_builtin_extensions_includes_common_zarr_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".zarr" in exts


def test_builtin_extensions_includes_common_png_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".png" in exts


def test_builtin_extensions_includes_common_json_in_exts():
    # Arrange
    # Arrange
    # Act
    exts = _builtin_extensions()
    # Act
    # Assert
    # Assert
    assert ".json" in exts




def test_io001_np_save_detected():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import numpy as np\nnp.save('x.npy', [1, 2])\n"
    # Assert
    # Assert
    assert "STX-IO001" in _ids(lint_source(src))


def test_io002_np_load_detected():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import numpy as np\nnp.load('x.npy')\n"
    # Assert
    # Assert
    assert "STX-IO002" in _ids(lint_source(src))


def test_io003_pd_read_csv():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import pandas as pd\npd.read_csv('x.csv')\n"
    # Assert
    # Assert
    assert "STX-IO003" in _ids(lint_source(src))


def test_io004_to_csv():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "df.to_csv('x.csv')\n"
    # Assert
    # Assert
    assert "STX-IO004" in _ids(lint_source(src))


def test_io005_pickle_dump_load():
    # Arrange
    # Arrange
    src = "import pickle\npickle.dump(o, f)\npickle.load(f)\n"
    # Act
    # Act
    ids = _ids(lint_source(src))
    # Assert
    # Assert
    assert ids.count("STX-IO005") == 2


def test_io006_json_dump():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import json\njson.dump(o, f)\njson.load(f)\n"
    # Assert
    # Assert
    assert _ids(lint_source(src)).count("STX-IO006") == 2


def test_io007_savefig_stx_io007_in_ids_lint_source_src():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "fig.savefig('x.png')\n"
    # Assert
    # Assert
    assert "STX-IO007" in _ids(lint_source(src))


def test_io008_torch_save_load():
    # Arrange
    # Arrange
    src = "import torch\ntorch.save(m, 'x.pt')\ntorch.load('x.pt')\n"
    # Act
    # Act
    ids = _ids(lint_source(src))
    # Assert
    # Assert
    assert ids.count("STX-IO008") == 2


def test_io009_joblib_ids_lint_source_src_count_stx_io009_2():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import joblib\njoblib.dump(o, 'x.joblib')\njoblib.load('x.joblib')\n"
    # Assert
    # Assert
    assert _ids(lint_source(src)).count("STX-IO009") == 2


def test_io010_yaml_ids_lint_source_src_count_stx_io010_2():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import yaml\nyaml.safe_load(f)\nyaml.dump(o, f)\n"
    # Assert
    # Assert
    assert _ids(lint_source(src)).count("STX-IO010") == 2


def test_io012_cv2_imwrite():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import cv2\ncv2.imwrite('x.png', img)\ncv2.imread('x.png')\n"
    # Assert
    # Assert
    assert _ids(lint_source(src)).count("STX-IO012") == 2


def test_io013_h5py_stx_io013_in_ids_lint_source_src():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import h5py\nh5py.File('x.h5', 'w')\n"
    # Assert
    # Assert
    assert "STX-IO013" in _ids(lint_source(src))


def test_io014_unknown_extension_stx_io_save_stx_io014_in_ids_issues():
    # Arrange
    # Arrange
    src = "import scitex as stx\nstx.io.save(obj, 'out.weirdext')\n"
    # Act
    issues = lint_source(src)
    # Act
    # Assert
    # Assert
    assert "STX-IO014" in _ids(issues)


def test_io014_unknown_extension_stx_io_save_weirdext_in_msg():
    # Arrange
    src = "import scitex as stx\nstx.io.save(obj, 'out.weirdext')\n"
    # Act
    issues = lint_source(src)
    msg = next(i for i in issues if i.rule.id == "STX-IO014").rule.message
    # Assert
    assert ".weirdext" in msg




def test_io014_known_extension_not_flagged():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex as stx\nstx.io.save(obj, 'out.csv')\n"
    # Assert
    # Assert
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_no_extension():
    # Arrange
    # Arrange
    src = "import scitex as stx\nstx.io.save(obj, 'output')\n"
    issues = lint_source(src)
    # Act
    # Act
    msg = next(i for i in issues if i.rule.id == "STX-IO014").rule.message
    # Assert
    # Assert
    assert "(no extension)" in msg


def test_io014_double_extension_known():
    # .pkl.gz is registered → should not flag
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex as stx\nstx.io.save(obj, 'out.pkl.gz')\n"
    # Assert
    # Assert
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_scitex_io_save():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex_io\nscitex_io.io.save(obj, 'out.bogusext')\n"
    # Assert
    # Assert
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_bare_scitex_io_save():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex_io\nscitex_io.save(obj, 'out.bogusext')\n"
    # Assert
    # Assert
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_kwarg_path():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex as stx\nstx.io.save(obj, path='out.bogusext')\n"
    # Assert
    # Assert
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_load_uses_index_0():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex as stx\nstx.io.load('in.bogusext')\n"
    # Assert
    # Assert
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_non_string_path_ignored():
    # Non-constant path argument → checker skips silently
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import scitex as stx\nstx.io.save(obj, some_var)\n"
    # Assert
    # Assert
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_non_stx_io_call_ignored():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "x.foo.save(obj, 'y.unknownext')\n"
    # Assert
    # Assert
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_bare_function_call_ignored():
    """Bare function call (not an Attribute) → checker returns None early."""
    # Arrange
    # Act
    src = "save(obj, 'y.unknownext')\n"
    # Assert
    assert "STX-IO014" not in _ids(lint_source(src))


def test_pa003_makedirs_stx_pa003_in_ids_lint_source_src():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import os\nos.makedirs('out')\n"
    # Assert
    # Assert
    assert "STX-PA003" in _ids(lint_source(src))


def test_pa004_chdir_stx_pa004_in_ids_lint_source_src():
    # Arrange
    # Act
    # Arrange
    # Act
    src = "import os\nos.chdir('/tmp')\n"
    # Assert
    # Assert
    assert "STX-PA004" in _ids(lint_source(src))


def test_unknownextchecker_direct_len_chk_issues_is_1():
    # Arrange
    # Arrange
    import ast
    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    # Act
    chk.visit(tree)
    # Act
    # Assert
    # Assert
    assert len(chk.issues) == 1


def test_unknownextchecker_direct_issue_rule_id_stx_io014():
    # Arrange
    import ast
    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    # Act
    chk.visit(tree)
    # Assert
    assert chk.issues[0].rule.id == "STX-IO014"


def test_unknownextchecker_direct_issue_line_equals_n_2():
    # Arrange
    import ast
    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    # Act
    chk.visit(tree)
    # Assert
    assert chk.issues[0].line == 2


def test_unknownextchecker_direct_chk_source_999():
    # Arrange
    import ast
    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    # Act
    chk.visit(tree)
    # Assert
    assert chk._source(999) == ""


def test_unknownextchecker_direct_chk_source_1_import_scitex_as_stx():
    # Arrange
    import ast
    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    # Act
    chk.visit(tree)
    # Assert
    assert chk._source(1) == "import scitex as stx"




def test_builtin_extensions_fallback_csv_in_exts(attr_restore):
    # Arrange
    import scitex_io._linter_plugin as mod
    import scitex_io._registry as reg
    # Clobber the registry tier attrs so the function raises and hits except
    attr_restore.set(reg, "_builtin_savers", None)
    # Act
    exts = mod._builtin_extensions()
    # Assert
    assert ".csv" in exts


def test_builtin_extensions_fallback_h5_in_exts(attr_restore):
    # Arrange
    import scitex_io._linter_plugin as mod
    import scitex_io._registry as reg
    attr_restore.set(reg, "_builtin_savers", None)
    # Act
    exts = mod._builtin_extensions()
    # Assert
    assert ".h5" in exts


def test_builtin_extensions_fallback_exts_is_set(attr_restore):
    # Arrange
    import scitex_io._linter_plugin as mod
    import scitex_io._registry as reg
    attr_restore.set(reg, "_builtin_savers", None)
    # Act
    exts = mod._builtin_extensions()
    # Assert
    assert isinstance(exts, set)


def test_builtin_extensions_fallback_png_in_exts(attr_restore):
    # Arrange
    import scitex_io._linter_plugin as mod
    import scitex_io._registry as reg
    attr_restore.set(reg, "_builtin_savers", None)
    # Act
    exts = mod._builtin_extensions()
    # Assert
    assert ".png" in exts


