#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io.bundle._storage`` — Storage backend abstraction."""

import pytest

from scitex_io.bundle._storage import DirStorage, Storage, ZipStorage, get_storage


def test_get_storage_returns_dir_storage_for_directory_path(tmp_path):
    # Arrange
    p = tmp_path / "bundle"
    p.mkdir()
    # Act
    storage = get_storage(p)
    # Assert
    assert isinstance(storage, DirStorage)


def test_get_storage_returns_zip_storage_for_zip_path(tmp_path):
    # Arrange
    p = tmp_path / "bundle.zip"
    # Act
    storage = get_storage(p)
    # Assert
    assert isinstance(storage, ZipStorage)


def test_dir_storage_round_trip_bytes(tmp_path):
    # Arrange
    storage = DirStorage(tmp_path)
    # Act
    storage.write("note.txt", b"hello")
    data = storage.read("note.txt")
    # Assert
    assert data == b"hello"


def test_dir_storage_round_trip_json(tmp_path):
    # Arrange
    storage = DirStorage(tmp_path)
    # Act
    storage.write_json("info.json", {"k": 2})
    payload = storage.read_json("info.json")
    # Assert
    assert payload == {"k": 2}


def test_storage_is_abstract_and_cannot_be_instantiated_directly(tmp_path):
    # Arrange
    target = tmp_path / "x"
    # Act / Assert
    # Assert
    with pytest.raises(TypeError):
        Storage(target)
