#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the less-exercised branches of `scitex_io._save.save`.

These cover code paths that the round-trip / dispatcher tests don't
naturally hit: Path-object inputs, f-string path expansion, the
jupyter / script / interactive env detection, dry-run output, symlink
side effects, the error envelope, and `_save_modules/__init__.py`
dispatcher edge cases.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path-like input handling (line 165 in _save.py)
# ---------------------------------------------------------------------------


class TestPathlibInput:
    def test_pathlib_path_input(self, tmp_path):
        import scitex_io as sio

        out = tmp_path / "data.json"
        # Pass an actual Path object — the save() entry point coerces it.
        sio.save({"a": 1}, out, verbose=False)
        assert out.is_file()
        assert sio.load(str(out)) == {"a": 1}

    def test_pathlib_path_via_load(self, tmp_path):
        import scitex_io as sio

        out = tmp_path / "data.npy"
        arr = np.arange(5)
        sio.save(arr, str(out), verbose=False)
        # Loader also accepts Path.
        back = sio.load(Path(out))
        np.testing.assert_array_equal(back, arr)


# ---------------------------------------------------------------------------
# f-string path expansion (lines 174-191)
# ---------------------------------------------------------------------------


class TestFStringPath:
    def test_f_string_rejects_invalid_variable_name(self, tmp_path):
        import scitex_io as sio

        # An f-expression with a non-identifier placeholder. The function
        # raises ValueError internally and the outer try/except returns
        # False (the function's error envelope).
        path = f'f"{tmp_path}/run_{{1invalid}}.json"'
        result = sio.save({"x": 1}, path, verbose=False)
        # Bad path → outer try/except returns False.
        assert result is False


# ---------------------------------------------------------------------------
# Absolute path bypasses routing (line 193)
# ---------------------------------------------------------------------------


class TestAbsolutePathBypass:
    def test_absolute_path_used_verbatim(self, tmp_path):
        import scitex_io as sio

        out = str(tmp_path / "abs.json")
        sio.save({"v": 1}, out, verbose=False)
        assert os.path.isfile(out)


# ---------------------------------------------------------------------------
# IPython / REPL routing into ~/.scitex/io/runtime/cache (lines 241-260)
# ---------------------------------------------------------------------------


class TestInteractiveRouting:
    def test_repl_env_routes_to_scitex_cache(self, tmp_path, monkeypatch):
        """When detect_environment() returns 'ipython', save() routes to
        $SCITEX_DIR/io/runtime/cache. The helper is imported lazily
        inside the save() body — patch on the _utils module."""
        import scitex_io as sio
        from scitex_io import _utils

        monkeypatch.setenv("SCITEX_DIR", str(tmp_path))
        monkeypatch.setattr(_utils, "detect_environment", lambda: "ipython")
        sio.save({"x": 1}, "result.json", verbose=False)
        out = tmp_path / "io" / "runtime" / "cache" / "result.json"
        assert out.is_file(), f"expected {out} to exist"


# ---------------------------------------------------------------------------
# dry_run path (line 280-290)
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_skips_write(self, tmp_path):
        import scitex_io as sio

        out = str(tmp_path / "dry.json")
        sio.save({"x": 1}, out, dry_run=True, verbose=False)
        # File NOT created.
        assert not os.path.isfile(out)


# ---------------------------------------------------------------------------
# Symlink-to path (lines 331-341)
# ---------------------------------------------------------------------------


class TestSymlinkTo:
    def test_symlink_to_creates_link(self, tmp_path):
        import scitex_io as sio

        out = str(tmp_path / "real.json")
        link = str(tmp_path / "links" / "alias.json")
        sio.save({"x": 1}, out, symlink_to=link, verbose=False)
        assert os.path.isfile(out)
        assert os.path.islink(link) or os.path.isfile(link)

    def test_symlink_to_accepts_pathlib(self, tmp_path):
        import scitex_io as sio

        out = str(tmp_path / "real.json")
        link = tmp_path / "alias.json"
        sio.save({"x": 1}, out, symlink_to=link, verbose=False)
        assert os.path.exists(link)


# ---------------------------------------------------------------------------
# Unknown extension → handler-missing error path
# ---------------------------------------------------------------------------


class TestUnknownExtension:
    def test_no_handler_returns_false(self, tmp_path):
        import scitex_io as sio

        # `.totally-fake` has no registered handler. save() catches the
        # ValueError and returns False.
        out = str(tmp_path / "data.totally-fake")
        assert sio.save({"x": 1}, out, verbose=False) is False


# ---------------------------------------------------------------------------
# Verbose success print (lines 386-394)
# ---------------------------------------------------------------------------


class TestVerboseLogging:
    def test_verbose_save_writes_file(self, tmp_path):
        import scitex_io as sio

        # verbose=True exercises the logger.success / readable_bytes
        # branch at the end of _save() regardless of where the log lands.
        out = str(tmp_path / "v.json")
        sio.save({"x": 1}, out, verbose=True)
        assert os.path.isfile(out)


# ---------------------------------------------------------------------------
# Compound .pkl.gz extension dispatch (line 361)
# ---------------------------------------------------------------------------


class TestCompoundExt:
    def test_pkl_gz_compressed_round_trip(self, tmp_path):
        import scitex_io as sio

        out = str(tmp_path / "obj.pkl.gz")
        df = pd.DataFrame({"x": [1, 2, 3]})
        sio.save(df, out, verbose=False)
        assert os.path.isfile(out)
        back = sio.load(out)
        pd.testing.assert_frame_equal(back, df)
