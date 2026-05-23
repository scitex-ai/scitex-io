#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the less-exercised branches of `scitex_io._save.save`.

from __future__ import annotations
These cover code paths that the round-trip / dispatcher tests don't
naturally hit: Path-object inputs, f-string path expansion, the
jupyter / script / interactive env detection, dry-run output, symlink
side effects, the error envelope, and `_save_modules/__init__.py`
dispatcher edge cases.
"""


import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path-like input handling (line 165 in _save.py)
# ---------------------------------------------------------------------------


class TestPathlibInput:
    def test_pathlib_path_input_out_is_file(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio
        out = tmp_path / "data.json"
        # Pass an actual Path object — the save() entry point coerces it.
        # Act
        sio.save({"a": 1}, out, verbose=False)
        # Act
        # Assert
        # Assert
        assert out.is_file()

    def test_pathlib_path_input_sio_load_str_out_a_1(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio
        out = tmp_path / "data.json"
        # Pass an actual Path object — the save() entry point coerces it.
        # Act
        sio.save({"a": 1}, out, verbose=False)
        # Act
        # Assert
        # Assert
        assert sio.load(str(out)) == {"a": 1}


    def test_pathlib_path_via_load(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        import scitex_io as sio

        out = tmp_path / "data.npy"
        arr = np.arange(5)
        sio.save(arr, str(out), verbose=False)
        # Loader also accepts Path.
        # Act
        back = sio.load(Path(out))
        # Assert
        assert np.array_equal(back, arr)


# ---------------------------------------------------------------------------
# f-string path expansion (lines 174-191)
# ---------------------------------------------------------------------------


class TestFStringPath:
    def test_f_string_rejects_invalid_variable_name(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        # An f-expression with a non-identifier placeholder. The function
        # raises ValueError internally and the outer try/except returns
        # False (the function's error envelope).
        path = f'f"{tmp_path}/run_{{1invalid}}.json"'
        # Act
        # Act
        result = sio.save({"x": 1}, path, verbose=False)
        # Bad path → outer try/except returns False.
        # Assert
        # Assert
        assert result is False


# ---------------------------------------------------------------------------
# Absolute path bypasses routing (line 193)
# ---------------------------------------------------------------------------


class TestAbsolutePathBypass:
    def test_absolute_path_used_verbatim(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = str(tmp_path / "abs.json")
        # Act
        # Act
        sio.save({"v": 1}, out, verbose=False)
        # Assert
        # Assert
        assert os.path.isfile(out)


# ---------------------------------------------------------------------------
# IPython / REPL routing into ~/.scitex/io/runtime/cache (lines 241-260)
# ---------------------------------------------------------------------------


class TestInteractiveRouting:
    def test_repl_env_routes_to_scitex_cache(self, tmp_path, monkeypatch):
        """When detect_environment() returns 'ipython', save() routes to
        $SCITEX_DIR/io/runtime/cache. The helper is imported lazily
        inside the save() body — patch on the _utils module."""
        # Arrange
        import scitex_io as sio
        from scitex_io import _utils

        monkeypatch.setenv("SCITEX_DIR", str(tmp_path))
        monkeypatch.setattr(_utils, "detect_environment", lambda: "ipython")
        sio.save({"x": 1}, "result.json", verbose=False)
        # Act
        out = tmp_path / "io" / "runtime" / "cache" / "result.json"
        # Assert
        assert out.is_file(), f"expected {out} to exist"


# ---------------------------------------------------------------------------
# dry_run path (line 280-290)
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_skips_write(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = str(tmp_path / "dry.json")
        # Act
        # Act
        sio.save({"x": 1}, out, dry_run=True, verbose=False)
        # File NOT created.
        # Assert
        # Assert
        assert not os.path.isfile(out)


# ---------------------------------------------------------------------------
# Symlink-to path (lines 331-341)
# ---------------------------------------------------------------------------


class TestSymlinkTo:
    def test_symlink_to_creates_link_os_path_isfile_out(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio
        out = str(tmp_path / "real.json")
        link = str(tmp_path / "links" / "alias.json")
        # Act
        sio.save({"x": 1}, out, symlink_to=link, verbose=False)
        # Act
        # Assert
        # Assert
        assert os.path.isfile(out)

    def test_symlink_to_creates_link_os_path_islink_link_or_os_path_isfile_link(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio
        out = str(tmp_path / "real.json")
        link = str(tmp_path / "links" / "alias.json")
        # Act
        sio.save({"x": 1}, out, symlink_to=link, verbose=False)
        # Act
        # Assert
        # Assert
        assert os.path.islink(link) or os.path.isfile(link)


    def test_symlink_to_accepts_pathlib(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = str(tmp_path / "real.json")
        link = tmp_path / "alias.json"
        # Act
        # Act
        sio.save({"x": 1}, out, symlink_to=link, verbose=False)
        # Assert
        # Assert
        assert os.path.exists(link)


# ---------------------------------------------------------------------------
# Unknown extension → handler-missing error path
# ---------------------------------------------------------------------------


class TestUnknownExtension:
    def test_no_handler_returns_false(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        # `.totally-fake` has no registered handler. save() catches the
        # ValueError and returns False.
        # Act
        # Act
        out = str(tmp_path / "data.totally-fake")
        # Assert
        # Assert
        assert sio.save({"x": 1}, out, verbose=False) is False


# ---------------------------------------------------------------------------
# Verbose success print (lines 386-394)
# ---------------------------------------------------------------------------


class TestVerboseLogging:
    def test_verbose_save_writes_file(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        # verbose=True exercises the logger.success / readable_bytes
        # branch at the end of _save() regardless of where the log lands.
        out = str(tmp_path / "v.json")
        # Act
        # Act
        sio.save({"x": 1}, out, verbose=True)
        # Assert
        # Assert
        assert os.path.isfile(out)


# ---------------------------------------------------------------------------
# Compound .pkl.gz extension dispatch (line 361)
# ---------------------------------------------------------------------------


class TestCompoundExt:
    def test_pkl_gz_compressed_round_trip(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = str(tmp_path / "obj.pkl.gz")
        df = pd.DataFrame({"x": [1, 2, 3]})
        # Act
        # Act
        sio.save(df, out, verbose=False)
        # Assert
        # Assert
        assert os.path.isfile(out)
        back = sio.load(out)
        pd.testing.assert_frame_equal(back, df)
