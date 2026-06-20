#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io._path_modules._symlink``.

``_symlink`` / ``_symlink_to`` are the convenience-link helpers used by
``save(..., symlink_from_cwd=...)`` / ``symlink_to=...``. ``sh`` is the
small ``subprocess.run`` wrapper they use to shell out to ``ln`` / ``rm``.

Real-collaborator style: every test runs the real helpers against real
paths under ``tmp_path`` (and the real ``sh`` → real ``ln``/``rm``). No
mocks. The self-loop-guard test (scitex-io#55) crafts the exact argument
shape that drives ``_symlink``'s defensive ``rel_target == basename``
branch and asserts the link is refused.
"""

from __future__ import annotations

import os

from scitex_io._path_modules._symlink import _symlink, _symlink_to, sh

# ---------------------------------------------------------------------------
# sh — the subprocess wrapper
# ---------------------------------------------------------------------------


class TestSh:
    def test_sh_returns_true_on_success(self):
        # Arrange — `true` always exits 0.
        # Act
        ok = sh(["true"])
        # Assert
        assert ok is True

    def test_sh_returns_false_on_failure(self):
        # Arrange — `false` always exits non-zero.
        # Act
        ok = sh(["false"])
        # Assert
        assert ok is False

    def test_sh_runs_argv_list_not_just_first_token(self, tmp_path):
        # Regression: a prior shell=True bug ran only command[0]. Verify
        # the full argv reaches the program by having `touch` create a
        # real file named by argv[1].
        # Arrange
        target = tmp_path / "created_by_sh.txt"
        # Act
        ok = sh(["touch", str(target)])
        # Assert
        assert ok is True and target.exists()


# ---------------------------------------------------------------------------
# _symlink — cwd-anchor link creation
# ---------------------------------------------------------------------------


class TestSymlink:
    def test_creates_cwd_anchor_symlink(self, tmp_path):
        # Arrange — a real saved file + a distinct cwd-anchor location.
        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"\x00")
        anchor = tmp_path / "data.npy"
        # Act — spath != spath_cwd, target resolves elsewhere → link made.
        _symlink(
            spath=str(saved),
            spath_cwd=str(anchor),
            symlink_from_cwd=True,
            verbose=False,
            spath_final=str(saved),
        )
        # Assert
        assert anchor.is_symlink()

    def test_cwd_anchor_resolves_to_saved_file(self, tmp_path):
        # Arrange
        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"payload")
        anchor = tmp_path / "data.npy"
        # Act
        _symlink(
            spath=str(saved),
            spath_cwd=str(anchor),
            symlink_from_cwd=True,
            verbose=False,
            spath_final=str(saved),
        )
        # Assert — following the link reaches the real bytes.
        assert anchor.resolve().read_bytes() == b"payload"

    def test_no_link_when_symlink_from_cwd_false(self, tmp_path):
        # Arrange
        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"\x00")
        anchor = tmp_path / "data.npy"
        # Act — feature disabled → nothing created at the anchor.
        _symlink(
            spath=str(saved),
            spath_cwd=str(anchor),
            symlink_from_cwd=False,
            verbose=False,
            spath_final=str(saved),
        )
        # Assert
        assert not anchor.exists()

    def test_no_link_when_spath_equals_spath_cwd(self, tmp_path):
        # Arrange — when the saved path IS the anchor, there is nothing to
        # link (the `spath != spath_cwd` guard short-circuits).
        same = tmp_path / "data.npy"
        same.write_bytes(b"\x00")
        # Act
        _symlink(
            spath=str(same),
            spath_cwd=str(same),
            symlink_from_cwd=True,
            verbose=False,
            spath_final=str(same),
        )
        # Assert — still a regular file, not replaced by a self-symlink.
        assert same.is_file() and not same.is_symlink()

    def test_self_loop_guard_refuses_link_when_rel_target_is_own_basename(
        self, tmp_path
    ):
        # scitex-io#55 defensive guard: if the relative target computed
        # against dirname(spath_cwd) equals basename(spath_cwd), creating
        # the link would make a `x -> x` self-loop. The guard logs and
        # returns WITHOUT creating anything.
        #
        # Craft the exact shape: spath_cwd lives in <tmp>/d/x.csv; pass a
        # DISTINCT spath (so the `spath != spath_cwd` gate passes) but a
        # spath_final equal to spath_cwd, so
        # relpath(spath_final, dirname(spath_cwd)) == "x.csv" ==
        # basename(spath_cwd) → guard fires.
        # Arrange
        d = tmp_path / "d"
        d.mkdir()
        anchor = d / "x.csv"  # spath_cwd
        # Act
        _symlink(
            spath=str(tmp_path / "elsewhere" / "x.csv"),  # != anchor
            spath_cwd=str(anchor),
            symlink_from_cwd=True,
            verbose=False,
            spath_final=str(anchor),  # rel target folds to own basename
        )
        # Assert — guard refused: no file/symlink created at the anchor.
        assert not anchor.exists() and not anchor.is_symlink()

    def test_self_loop_guard_does_not_raise(self, tmp_path):
        # Arrange — same self-loop shape; the guard must return cleanly,
        # never raise.
        d = tmp_path / "d"
        d.mkdir()
        anchor = d / "x.csv"
        completed = False
        # Act
        _symlink(
            spath=str(tmp_path / "elsewhere" / "x.csv"),
            spath_cwd=str(anchor),
            symlink_from_cwd=True,
            verbose=False,
            spath_final=str(anchor),
        )
        completed = True
        # Assert
        assert completed


# ---------------------------------------------------------------------------
# _symlink_to — explicit destination link
# ---------------------------------------------------------------------------


class TestSymlinkTo:
    def test_creates_symlink_at_destination(self, tmp_path):
        # Arrange
        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"\x00")
        dest = tmp_path / "links" / "alias.npy"
        # Act
        _symlink_to(str(saved), str(dest), verbose=False)
        # Assert
        assert dest.is_symlink()

    def test_destination_resolves_to_saved_file(self, tmp_path):
        # Arrange
        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"payload")
        dest = tmp_path / "links" / "alias.npy"
        # Act
        _symlink_to(str(saved), str(dest), verbose=False)
        # Assert
        assert dest.resolve().read_bytes() == b"payload"

    def test_accepts_pathlib_destination(self, tmp_path):
        # Arrange — symlink_to passed as a Path is coerced via str().
        from pathlib import Path

        saved = tmp_path / "out" / "data.npy"
        saved.parent.mkdir(parents=True)
        saved.write_bytes(b"\x00")
        dest = Path(tmp_path) / "links" / "alias.npy"
        # Act
        _symlink_to(str(saved), dest, verbose=False)
        # Assert
        assert dest.is_symlink()

    def test_no_destination_creates_nothing(self, tmp_path):
        # Arrange — falsy symlink_to short-circuits (no link requested).
        saved = tmp_path / "data.npy"
        saved.write_bytes(b"\x00")
        before = set(os.listdir(tmp_path))
        # Act
        _symlink_to(str(saved), None, verbose=False)
        # Assert — directory contents unchanged.
        assert set(os.listdir(tmp_path)) == before


if __name__ == "__main__":
    import pytest

    pytest.main([os.path.abspath(__file__)])
