"""Tests for scitex_io._path helpers."""


from __future__ import annotations
import os
from pathlib import Path

import pytest

from scitex_io._path import (
    find,
    find_latest,
    find_the_git_root_dir,
    split_fpath,
    touch,
)


# -----------------------------
# split_fpath
# -----------------------------
def test_split_fpath_basic_d_equals_a_b_c():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/b/c/file.txt")
    # Act
    # Assert
    # Assert
    assert d == "/a/b/c/"


def test_split_fpath_basic_n_equals_file():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/b/c/file.txt")
    # Act
    # Assert
    # Assert
    assert n == "file"


def test_split_fpath_basic_e_equals_txt():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/b/c/file.txt")
    # Act
    # Assert
    # Assert
    assert e == ".txt"




def test_split_fpath_no_extension_d_equals_a():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/file")
    # Act
    # Assert
    # Assert
    assert d == "/a/"


def test_split_fpath_no_extension_n_equals_file():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/file")
    # Act
    # Assert
    # Assert
    assert n == "file"


def test_split_fpath_no_extension_e_equals_case():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("/a/file")
    # Act
    # Assert
    # Assert
    assert e == ""




def test_split_fpath_relative_d_equals_rel_dir():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("rel/dir/x.mat")
    # Act
    # Assert
    # Assert
    assert d == "rel/dir/"


def test_split_fpath_relative_n_equals_x():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("rel/dir/x.mat")
    # Act
    # Assert
    # Assert
    assert n == "x"


def test_split_fpath_relative_e_equals_mat():
    # Arrange
    # Arrange
    # Act
    d, n, e = split_fpath("rel/dir/x.mat")
    # Act
    # Assert
    # Assert
    assert e == ".mat"




# -----------------------------
# touch
# -----------------------------
def test_touch_creates_file_not_p_exists(tmp_path):
    # Arrange
    # Arrange
    # Act
    p = tmp_path / "new.txt"
    # Act
    # Assert
    # Assert
    assert not p.exists()


def test_touch_creates_file_p_exists_after_call(tmp_path):
    # Arrange
    p = tmp_path / "new.txt"
    # Act
    touch(str(p))
    # Assert
    assert p.exists()




def test_touch_updates_mtime(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "exist.txt"
    p.write_text("hi")
    old = p.stat().st_mtime
    # Force a different mtime by setting it backwards.
    os.utime(str(p), (old - 100, old - 100))
    # Act
    # Act
    touch(str(p))
    # Assert
    # Assert
    assert p.stat().st_mtime > old - 100


# -----------------------------
# find
# -----------------------------
def test_find_files_by_pattern(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    (tmp_path / "b.log").write_text("y")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("z")
    out = find(str(tmp_path), type="f", exp="*.txt")
    # Act
    # Act
    names = sorted(os.path.basename(p) for p in out)
    # Assert
    # Assert
    assert names == ["a.txt", "c.txt"]


def test_find_directories_d1_in_names_and_d2_in_names(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    (tmp_path / "f.txt").write_text("x")
    out = find(str(tmp_path), type="d", exp="*")
    # Act
    names = sorted(os.path.basename(p) for p in out)
    # Act
    # Assert
    # Assert
    assert "d1" in names and "d2" in names


def test_find_directories_f_txt_not_in_names(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "d1").mkdir()
    (tmp_path / "d2").mkdir()
    (tmp_path / "f.txt").write_text("x")
    out = find(str(tmp_path), type="d", exp="*")
    # Act
    names = sorted(os.path.basename(p) for p in out)
    # Act
    # Assert
    # Assert
    assert "f.txt" not in names




def test_find_all_types(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "f.txt").write_text("x")
    (tmp_path / "d").mkdir()
    out = find(str(tmp_path), type=None, exp="*")
    # Act
    # Act
    names = sorted(os.path.basename(p) for p in out)
    # Assert
    # Assert
    assert "f.txt" in names and "d" in names


def test_find_multiple_patterns(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.txt").write_text("1")
    (tmp_path / "b.md").write_text("2")
    (tmp_path / "c.py").write_text("3")
    out = find(str(tmp_path), type="f", exp=["*.txt", "*.md"])
    # Act
    # Act
    names = sorted(os.path.basename(p) for p in out)
    # Assert
    # Assert
    assert names == ["a.txt", "b.md"]


def test_find_no_matches(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "a.txt").write_text("x")
    # Act
    # Act
    out = find(str(tmp_path), type="f", exp="*.xyz")
    # Assert
    # Assert
    assert out == []


# -----------------------------
# find_latest
# -----------------------------
def test_find_latest_picks_highest_version_latest_is_not_none(tmp_path):
    # Arrange
    # Arrange
    for v in [1, 2, 5, 3]:
        (tmp_path / f"data_v{v}.txt").write_text("x")
    # Act
    latest = find_latest(str(tmp_path), "data", ".txt")
    # Act
    # Assert
    # Assert
    assert latest is not None


def test_find_latest_picks_highest_version_latest_endswith_data_v5_txt(tmp_path):
    # Arrange
    # Arrange
    for v in [1, 2, 5, 3]:
        (tmp_path / f"data_v{v}.txt").write_text("x")
    # Act
    latest = find_latest(str(tmp_path), "data", ".txt")
    # Act
    # Assert
    # Assert
    assert latest.endswith("data_v5.txt")




def test_find_latest_returns_none_when_missing(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert find_latest(str(tmp_path), "absent", ".txt") is None


def test_find_latest_with_custom_prefix(tmp_path):
    # Arrange
    # Arrange
    (tmp_path / "file-r2.bin").write_text("x")
    (tmp_path / "file-r10.bin").write_text("y")
    # Act
    # Act
    latest = find_latest(str(tmp_path), "file", ".bin", version_prefix="-r")
    # Assert
    # Assert
    assert latest.endswith("file-r10.bin")


# -----------------------------
# find_the_git_root_dir
# -----------------------------
def _git_available():
    try:
        import git  # noqa: F401

        return True
    except ImportError:
        return False


_GIT_AVAILABLE = _git_available()


@pytest.mark.skipif(not _GIT_AVAILABLE, reason="GitPython not installed")
def test_find_the_git_root_dir_returns_non_none_path():
    # Arrange
    old = os.getcwd()
    os.chdir(Path(__file__).parent)
    try:
        # Act
        root = find_the_git_root_dir()
    finally:
        os.chdir(old)
    # Assert
    assert root is not None


@pytest.mark.skipif(not _GIT_AVAILABLE, reason="GitPython not installed")
def test_find_the_git_root_dir_returns_existing_directory():
    # Arrange
    old = os.getcwd()
    os.chdir(Path(__file__).parent)
    try:
        # Act
        root = find_the_git_root_dir()
    finally:
        os.chdir(old)
    # Assert
    assert os.path.isdir(root)


@pytest.mark.skipif(_GIT_AVAILABLE, reason="Requires GitPython to be missing")
def test_find_the_git_root_dir_without_git_raises_modulenotfound():
    # Arrange
    # Function imports `git` lazily — raises ModuleNotFoundError when missing.
    # Act
    ctx = pytest.raises(ModuleNotFoundError)
    # Assert
    with ctx:
        find_the_git_root_dir()


@pytest.mark.skipif(not _GIT_AVAILABLE, reason="GitPython not installed")
def test_find_the_git_root_dir_outside_repo_raises_invalid_repo(tmp_path):
    # Arrange
    import git

    old = os.getcwd()
    os.chdir(tmp_path)
    # Act
    ctx = pytest.raises(git.exc.InvalidGitRepositoryError)
    try:
        # Assert
        with ctx:
            find_the_git_root_dir()
    finally:
        os.chdir(old)
