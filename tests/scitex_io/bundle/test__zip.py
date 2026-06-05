#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io.bundle._zip`` — ZIP bundle reader/writer."""

import zipfile

from scitex_io.bundle._zip import create, zip_directory
from scitex_io.bundle._zip import open as zip_open


def test_create_writes_a_zip_file(tmp_path):
    # Arrange
    target = tmp_path / "bundle.plot.zip"
    spec = {"schema": {"name": "scitex.plt", "version": "1.0"}}
    # Act
    out = create(target, spec)
    # Assert
    assert out.exists()


def test_create_round_trip_reads_spec_back(tmp_path):
    # Arrange
    target = tmp_path / "bundle.plot.zip"
    spec = {"schema": {"name": "scitex.plt", "version": "1.0"}}
    create(target, spec)
    # Act
    with zip_open(target, mode="r") as bundle:
        loaded = bundle.read_json("spec.json")
    # Assert
    assert loaded == spec


def test_zip_directory_packs_files_into_an_archive(tmp_path):
    # Arrange
    src = tmp_path / "src"
    src.mkdir()
    (src / "data.txt").write_text("hello")
    target = tmp_path / "out.zip"
    # Act
    zip_directory(src, target)
    # Assert
    assert zipfile.is_zipfile(target)


def test_zip_directory_preserves_file_names(tmp_path):
    # Arrange
    src = tmp_path / "src"
    src.mkdir()
    (src / "note.txt").write_text("x")
    target = tmp_path / "out.zip"
    zip_directory(src, target)
    # Act
    with zipfile.ZipFile(target) as zf:
        names = zf.namelist()
    # Assert
    assert any(n.endswith("note.txt") for n in names)
