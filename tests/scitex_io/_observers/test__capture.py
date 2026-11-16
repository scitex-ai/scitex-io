#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every file a save writes fires one post-save hook; links are recorded.

Savers here are real callables registered through the public
``register_saver`` extension API and write real bytes to ``tmp_path``.
"""

from __future__ import annotations

import json
import logging
import os

import pytest

import scitex_io
from scitex_io._observers import observer_failures, register_post_save_hook
from scitex_io._registry import register_saver, unregister_saver


def _save_with_sidecar(obj, spath, **kwargs):
    with open(spath, "w") as f:
        f.write(str(obj))
    with open(os.path.splitext(spath)[0] + ".meta.json", "w") as f:
        json.dump({"len": len(str(obj))}, f)


@pytest.fixture
def sidecar_save(hooks, tmp_path):
    register_saver(".sidecartest", _save_with_sidecar)
    (tmp_path / "data_old.txt").write_text("pre-existing\n")
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append((str(p), obj, kw)))
    primary = tmp_path / "data.sidecartest"
    try:
        scitex_io.save("payload", str(primary), verbose=False)
    finally:
        unregister_saver(".sidecartest")
    return seen, primary, tmp_path


def test_save_reports_primary_then_sidecar(sidecar_save):
    # Arrange
    seen, primary, tmp_path = sidecar_save
    # Act
    paths = [s[0] for s in seen]
    # Assert
    assert paths == [
        os.path.realpath(primary),
        os.path.realpath(tmp_path / "data.meta.json"),
    ]


def test_sidecar_payload_points_at_its_primary(sidecar_save):
    # Arrange
    seen, primary, _ = sidecar_save
    # Act
    prov = seen[1][2]["provenance"]
    # Assert
    assert (prov["role"], prov["primary"]) == ("sidecar", os.path.realpath(primary))


def test_sidecar_hook_gets_no_object(sidecar_save):
    # Arrange
    seen, _, _ = sidecar_save
    # Act
    sidecar_obj = seen[1][1]
    # Assert
    assert sidecar_obj is None


def test_primary_hook_gets_object_and_track(sidecar_save):
    # Arrange
    seen, _, _ = sidecar_save
    # Act
    _, obj, kw = seen[0]
    # Assert
    assert (obj, kw["track"], kw["provenance"]["role"]) == ("payload", True, "primary")


def test_unchanged_neighbour_files_are_not_reported(sidecar_save):
    # Arrange
    seen, _, _ = sidecar_save
    # Act
    names = {os.path.basename(s[0]) for s in seen}
    # Assert
    assert "data_old.txt" not in names


@pytest.fixture
def linked_save(hooks, tmp_path):
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append((str(p), kw)))
    target = tmp_path / "out" / "res.txt"
    link = tmp_path / "cwd" / "res.txt"
    scitex_io.save("r", str(target), verbose=False, symlink_to=str(link))
    return seen, target, link


def test_symlinked_save_hashes_the_target_realpath(linked_save):
    # Arrange
    seen, target, _ = linked_save
    # Act
    ((path, _),) = seen
    # Assert
    assert path == os.path.realpath(target)


def test_symlinked_save_payload_records_the_link(linked_save):
    # Arrange
    seen, _, link = linked_save
    # Act
    ((_, kw),) = seen
    # Assert
    assert kw["provenance"]["symlinks"] == [str(link)]


def _bundle(obj, spath, **kwargs):
    with open(spath, "w") as f:
        f.write("index")
    scitex_io.save(obj, os.path.splitext(spath)[0] + "_part.txt", verbose=False)


def test_nested_public_save_is_reported_exactly_once(hooks, tmp_path):
    # Arrange
    register_saver(".bundletest", _bundle)
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(os.path.basename(p)))
    # Act
    try:
        scitex_io.save("x", str(tmp_path / "b.bundletest"), verbose=False)
    finally:
        unregister_saver(".bundletest")
    # Assert
    assert sorted(seen) == ["b.bundletest", "b_part.txt"]


@pytest.fixture
def ghost_save(hooks, tmp_path, caplog):
    register_saver(".noopsave", lambda obj, spath, **kw: None)
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(p))
    try:
        with caplog.at_level(logging.WARNING):
            scitex_io.save("x", str(tmp_path / "ghost.noopsave"), verbose=False)
    finally:
        unregister_saver(".noopsave")
    return seen, observer_failures(), caplog


def test_save_that_writes_nothing_is_counted(ghost_save):
    # Arrange
    _, report, _ = ghost_save
    # Act
    by_kind = report["by_kind"]
    # Assert
    assert by_kind == {"missing_output": 1}


def test_save_that_writes_nothing_warns(ghost_save, provenance_warnings):
    # Arrange
    _, _, caplog = ghost_save
    # Act
    warnings = provenance_warnings(caplog)
    # Assert
    assert len(warnings) == 1


@pytest.fixture
def figure_save(hooks, tmp_path):
    fr = pytest.importorskip("figrecipe")
    fig, ax = fr.subplots()
    ax.plot([0, 1, 2], [0, 1, 4], id="curve")
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(kw["provenance"]))
    scitex_io.save(fig, str(tmp_path / "fig.png"), verbose=False)
    written = {
        os.path.realpath(os.path.join(root, f))
        for root, _d, files in os.walk(tmp_path)
        for f in files
    }
    return seen, written


def test_figure_save_writes_sidecars(figure_save):
    # Arrange
    _, written = figure_save
    # Act
    n_files = len(written)
    # Assert
    assert n_files > 1


def test_every_figure_file_reaches_the_save_hook(figure_save):
    # Arrange
    seen, written = figure_save
    # Act
    reported = {p["realpath"] for p in seen}
    # Assert
    assert reported == written
