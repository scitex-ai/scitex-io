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


def test_get_plugin_shape():
    p = get_plugin()
    assert set(p.keys()) >= {"rules", "call_rules", "axes_hints", "checkers"}
    rule_ids = {r.id for r in p["rules"]}
    expected = {f"STX-IO{n:03d}" for n in range(1, 15)} | {
        f"STX-PA{n:03d}" for n in range(1, 6)
    }
    assert expected <= rule_ids
    assert any(c is _UnknownExtChecker for c in p["checkers"])
    assert p["axes_hints"] == {}
    # call_rules has expected entries
    assert ("np", "save") in p["call_rules"]
    assert ("pickle", "dump") in p["call_rules"]
    assert ("os", "chdir") in p["call_rules"]
    # All rules have the register hint appended (except PA004 which has no requires hint)
    for r in p["rules"]:
        if r.id.startswith("STX-IO") and r.id != "STX-IO014":
            assert _REGISTER_HINT in r.suggestion


def test_builtin_extensions_includes_common():
    exts = _builtin_extensions()
    assert ".csv" in exts
    assert ".npy" in exts
    assert ".pkl" in exts
    assert ".h5" in exts
    assert ".zarr" in exts
    assert ".png" in exts
    assert ".json" in exts


def test_io001_np_save_detected():
    src = "import numpy as np\nnp.save('x.npy', [1, 2])\n"
    assert "STX-IO001" in _ids(lint_source(src))


def test_io002_np_load_detected():
    src = "import numpy as np\nnp.load('x.npy')\n"
    assert "STX-IO002" in _ids(lint_source(src))


def test_io003_pd_read_csv():
    src = "import pandas as pd\npd.read_csv('x.csv')\n"
    assert "STX-IO003" in _ids(lint_source(src))


def test_io004_to_csv():
    src = "df.to_csv('x.csv')\n"
    assert "STX-IO004" in _ids(lint_source(src))


def test_io005_pickle_dump_load():
    src = "import pickle\npickle.dump(o, f)\npickle.load(f)\n"
    ids = _ids(lint_source(src))
    assert ids.count("STX-IO005") == 2


def test_io006_json_dump():
    src = "import json\njson.dump(o, f)\njson.load(f)\n"
    assert _ids(lint_source(src)).count("STX-IO006") == 2


def test_io007_savefig():
    src = "fig.savefig('x.png')\n"
    assert "STX-IO007" in _ids(lint_source(src))


def test_io008_torch_save_load():
    src = "import torch\ntorch.save(m, 'x.pt')\ntorch.load('x.pt')\n"
    ids = _ids(lint_source(src))
    assert ids.count("STX-IO008") == 2


def test_io009_joblib():
    src = "import joblib\njoblib.dump(o, 'x.joblib')\njoblib.load('x.joblib')\n"
    assert _ids(lint_source(src)).count("STX-IO009") == 2


def test_io010_yaml():
    src = "import yaml\nyaml.safe_load(f)\nyaml.dump(o, f)\n"
    assert _ids(lint_source(src)).count("STX-IO010") == 2


def test_io012_cv2_imwrite():
    src = "import cv2\ncv2.imwrite('x.png', img)\ncv2.imread('x.png')\n"
    assert _ids(lint_source(src)).count("STX-IO012") == 2


def test_io013_h5py():
    src = "import h5py\nh5py.File('x.h5', 'w')\n"
    assert "STX-IO013" in _ids(lint_source(src))


def test_io014_unknown_extension_stx_io_save():
    src = "import scitex as stx\nstx.io.save(obj, 'out.weirdext')\n"
    issues = lint_source(src)
    assert "STX-IO014" in _ids(issues)
    msg = next(i for i in issues if i.rule.id == "STX-IO014").rule.message
    assert ".weirdext" in msg


def test_io014_known_extension_not_flagged():
    src = "import scitex as stx\nstx.io.save(obj, 'out.csv')\n"
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_no_extension():
    src = "import scitex as stx\nstx.io.save(obj, 'output')\n"
    issues = lint_source(src)
    msg = next(i for i in issues if i.rule.id == "STX-IO014").rule.message
    assert "(no extension)" in msg


def test_io014_double_extension_known():
    # .pkl.gz is registered → should not flag
    src = "import scitex as stx\nstx.io.save(obj, 'out.pkl.gz')\n"
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_scitex_io_save():
    src = "import scitex_io\nscitex_io.io.save(obj, 'out.bogusext')\n"
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_bare_scitex_io_save():
    src = "import scitex_io\nscitex_io.save(obj, 'out.bogusext')\n"
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_kwarg_path():
    src = "import scitex as stx\nstx.io.save(obj, path='out.bogusext')\n"
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_load_uses_index_0():
    src = "import scitex as stx\nstx.io.load('in.bogusext')\n"
    assert "STX-IO014" in _ids(lint_source(src))


def test_io014_non_string_path_ignored():
    # Non-constant path argument → checker skips silently
    src = "import scitex as stx\nstx.io.save(obj, some_var)\n"
    assert "STX-IO014" not in _ids(lint_source(src))


def test_io014_non_stx_io_call_ignored():
    src = "x.foo.save(obj, 'y.unknownext')\n"
    assert "STX-IO014" not in _ids(lint_source(src))


def test_pa003_makedirs():
    src = "import os\nos.makedirs('out')\n"
    assert "STX-PA003" in _ids(lint_source(src))


def test_pa004_chdir():
    src = "import os\nos.chdir('/tmp')\n"
    assert "STX-PA004" in _ids(lint_source(src))


def test_unknownextchecker_direct():
    """Exercise the checker class directly to cover edge paths."""
    import ast

    src = "import scitex as stx\nstx.io.save(obj, 'x.bogusext')\n"
    tree = ast.parse(src)
    chk = _UnknownExtChecker(src.splitlines())
    chk.visit(tree)
    assert len(chk.issues) == 1
    issue = chk.issues[0]
    assert issue.rule.id == "STX-IO014"
    assert issue.line == 2
    # _source for out-of-range
    assert chk._source(999) == ""
    assert chk._source(1) == "import scitex as stx"


def test_builtin_extensions_fallback(monkeypatch):
    """Force the registry-import path to fail → fallback set returned."""
    import builtins

    import scitex_io._linter_plugin as mod

    real_import = builtins.__import__

    def fake(name, *a, **kw):
        if "_registry" in name or "_builtin_handlers" in name:
            raise ImportError("boom")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake)
    exts = mod._builtin_extensions()
    assert ".csv" in exts
    assert ".h5" in exts
