#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every file a load reads fires one post-load hook, with its realpath."""

from __future__ import annotations

import os

import pytest

import scitex_io
from scitex_io._observers import register_post_load_hook


@pytest.fixture
def glob_load(hooks, tmp_path):
    for i in range(3):
        (tmp_path / f"part_{i}.txt").write_text(f"v{i}\n")
    seen = []
    register_post_load_hook(lambda p, r, info: seen.append((str(p), info["glob"])))
    pattern = str(tmp_path / "part_*.txt")
    results = scitex_io.load(pattern)
    expected = [os.path.realpath(tmp_path / f"part_{i}.txt") for i in range(3)]
    return seen, results, pattern, expected


def test_glob_load_fires_once_per_matched_file(glob_load):
    # Arrange
    seen, _, _, expected = glob_load
    # Act
    paths = [p for p, _ in seen]
    # Assert
    assert paths == expected


def test_glob_load_hook_info_names_the_pattern(glob_load):
    # Arrange
    seen, _, pattern, _ = glob_load
    # Act
    patterns = {g for _, g in seen}
    # Assert
    assert patterns == {pattern}


def test_glob_load_still_returns_every_file(glob_load):
    # Arrange
    _, results, _, _ = glob_load
    # Act
    flat = [r[0] for r in results]
    # Assert
    assert flat == ["v0", "v1", "v2"]


def test_glob_as_path_object_never_fires_for_the_pattern(hooks, tmp_path):
    # Arrange
    (tmp_path / "only_1.txt").write_text("v\n")
    seen = []
    register_post_load_hook(lambda p, r: seen.append(str(p)))
    # Act
    scitex_io.load(tmp_path / "only_*.txt")
    # Assert
    assert seen == [os.path.realpath(tmp_path / "only_1.txt")]


def test_literal_filename_with_bracket_fires_its_hook(hooks, tmp_path):
    # Arrange
    path = tmp_path / "run[1].txt"
    path.write_text("literal\n")
    seen = []
    register_post_load_hook(lambda p, r: seen.append((str(p), r)))
    # Act
    scitex_io.load(str(path))
    # Assert
    assert seen == [(os.path.realpath(path), ["literal"])]


def test_two_argument_load_hooks_keep_working(hooks, tmp_path):
    # Arrange
    path = tmp_path / "two.txt"
    path.write_text("t\n")
    seen = []
    register_post_load_hook(lambda p, r: seen.append(r))
    # Act
    scitex_io.load(str(path))
    # Assert
    assert seen == [["t"]]


@pytest.fixture
def symlink_load(hooks, tmp_path):
    target = tmp_path / "real.txt"
    target.write_text("z\n")
    link = tmp_path / "alias.txt"
    link.symlink_to(target)
    seen = []
    register_post_load_hook(lambda p, r, info: seen.append((str(p), info)))
    scitex_io.load(str(link), cache=False)
    return seen, target, link


def test_load_through_symlink_hashes_the_target(symlink_load):
    # Arrange
    seen, target, _ = symlink_load
    # Act
    ((path, _),) = seen
    # Assert
    assert path == os.path.realpath(target)


def test_load_through_symlink_records_the_link(symlink_load):
    # Arrange
    seen, _, link = symlink_load
    # Act
    ((_, info),) = seen
    # Assert
    assert (info["symlink"], info["requested"]) == (True, str(link))
