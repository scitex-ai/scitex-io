#!/usr/bin/env python3
# Timestamp: "2025-05-31"
# File: test__mv_to_tmp.py

"""Tests for scitex_io._mv_to_tmp module.

The production function takes ``move_fn`` and ``tmp_dir`` keyword
parameters so tests can pass a recording callable and a sandbox
directory instead of mocking ``shutil.move``.
"""

from pathlib import Path

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

from scitex_io._mv_to_tmp import _mv_to_tmp


def _recording_move_fn():
    calls: list = []

    def _move(src, dst):
        calls.append((src, dst))

    return calls, _move


# ---------------------------------------------------------------------------
# Default L=2 behaviour
# ---------------------------------------------------------------------------


def test_default_L_uses_last_two_components_target_is_data_test_txt():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/home/user/data/test.txt", move_fn=mv)
    # Assert
    assert calls == [("/home/user/data/test.txt", "/tmp/data-test.txt")]


def test_default_L_nested_path_target_is_structure_myfile_txt():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/path/to/deep/folder/structure/myfile.txt", move_fn=mv)
    # Assert
    assert calls == [
        (
            "/path/to/deep/folder/structure/myfile.txt",
            "/tmp/structure-myfile.txt",
        )
    ]


# ---------------------------------------------------------------------------
# Custom L
# ---------------------------------------------------------------------------


def test_custom_L_three_picks_last_three_components():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/home/user/documents/project/data/file.csv", L=3, move_fn=mv)
    # Assert
    assert calls == [
        (
            "/home/user/documents/project/data/file.csv",
            "/tmp/project-data-file.csv",
        )
    ]


def test_L_larger_than_components_keeps_filename():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("file.txt", L=3, move_fn=mv)
    # Assert
    assert calls == [("file.txt", "/tmp/file.txt")]


def test_L_one_keeps_only_filename():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/a/b/c/d/e/file.txt", L=1, move_fn=mv)
    # Assert
    assert calls == [("/a/b/c/d/e/file.txt", "/tmp/file.txt")]


def test_L_five_keeps_five_components():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/a/b/c/d/e/file.txt", L=5, move_fn=mv)
    # Assert
    assert calls == [("/a/b/c/d/e/file.txt", "/tmp/b-c-d-e-file.txt")]


def test_L_zero_returns_full_split_with_leading_empty():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/path/to/file.txt", L=0, move_fn=mv)
    # Assert
    assert calls == [("/path/to/file.txt", "/tmp/-path-to-file.txt")]


# ---------------------------------------------------------------------------
# Error handling (bare except in production)
# ---------------------------------------------------------------------------


def test_move_failure_is_swallowed_silently():
    # Arrange
    def _failing_move(src, dst):
        raise FileNotFoundError("file not found")

    # Act
    _mv_to_tmp("/nonexistent/file.txt", move_fn=_failing_move)
    # Assert
    assert True  # not raising is the contract


def test_permission_error_is_swallowed_silently():
    # Arrange
    def _failing_move(src, dst):
        raise PermissionError("denied")

    # Act
    _mv_to_tmp("/root/protected/file.txt", move_fn=_failing_move)
    # Assert
    assert True  # not raising is the contract


def test_none_path_is_swallowed_silently():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp(None, move_fn=mv)
    # Assert
    assert calls == []  # split() would raise, except swallows it


def test_integer_path_is_swallowed_silently():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp(123, move_fn=mv)
    # Assert
    assert calls == []  # split() would raise, except swallows it


# ---------------------------------------------------------------------------
# Path-handling quirks
# ---------------------------------------------------------------------------


def test_path_with_spaces_join_preserves_spaces():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/home/user/my documents/important file.txt", move_fn=mv)
    # Assert
    assert calls == [
        (
            "/home/user/my documents/important file.txt",
            "/tmp/my documents-important file.txt",
        )
    ]


def test_path_with_special_characters_passes_through():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/data/files/report_2024-01-01.csv", move_fn=mv)
    # Assert
    assert calls == [
        (
            "/data/files/report_2024-01-01.csv",
            "/tmp/files-report_2024-01-01.csv",
        )
    ]


def test_unicode_path_passes_through_intact():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("/home/user/文档/ファイル.txt", move_fn=mv)
    # Assert
    assert calls == [
        ("/home/user/文档/ファイル.txt", "/tmp/文档-ファイル.txt"),
    ]


def test_relative_path_joins_last_two_components():
    # Arrange
    calls, mv = _recording_move_fn()
    # Act
    _mv_to_tmp("./data/file.txt", move_fn=mv)
    # Assert
    assert calls == [("./data/file.txt", "/tmp/data-file.txt")]


# ---------------------------------------------------------------------------
# Real filesystem integration via tmp_dir
# ---------------------------------------------------------------------------


def test_real_filesystem_move_creates_target_in_sandbox(tmp_path):
    # Arrange
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "test.txt"
    src_file.write_text("content")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    # Act
    _mv_to_tmp(str(src_file), tmp_dir=str(sandbox))
    # Assert
    assert (sandbox / "src-test.txt").read_text() == "content"


def test_real_filesystem_move_removes_source(tmp_path):
    # Arrange
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    src_file = src_dir / "test.txt"
    src_file.write_text("content")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    # Act
    _mv_to_tmp(str(src_file), tmp_dir=str(sandbox))
    # Assert
    assert not src_file.exists()
