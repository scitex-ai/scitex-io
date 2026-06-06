#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._optional_providers.{_import,_register}_scitex_db.

Two behaviours are contracted, matching the figrecipe / scitex_stats
provider pattern:

- **scitex-db present** → ``.db`` dispatches through the registry to
  ``scitex_db.SQLite3(path, **kwargs)``. ``stx.io.load("foo.db")``
  returns the full wrapper (not a raw ``sqlite3.Connection``) so
  callers reach ``get_rows`` / ``load_array`` / ``save_array`` without
  importing scitex_db directly.

- **scitex-db absent** → ``.db`` stays unregistered, ``_register_scitex_db``
  reports ``False`` rather than raising, and ``stx.io.load("foo.db")``
  fails loud through the standard "no handler registered" error path
  (the silent-fallback antipattern removed in the scitex-db
  standardization).
"""

import os
import sqlite3

import pytest

import scitex_io
from scitex_io import _optional_providers
from scitex_io._registry import get_loader

scitex_db = pytest.importorskip("scitex_db", reason="scitex-db optional extra")


@pytest.fixture(autouse=True)
def _ensure_registered():
    # Arrange: trigger _ensure_builtin_handlers_registered (idempotent).
    scitex_io.list_formats()
    yield


@pytest.fixture
def empty_db_path(tmp_path):
    # Arrange: an on-disk SQLite file with a trivial table so SQLite3
    # has something to open. The connection is opened-and-closed inside
    # the fixture so we only `yield` the path string — `yield` (not
    # `return`) satisfies STX-TQ005 because the fixture body touches a
    # resource-acquiring call (`sqlite3.connect(...)`).
    path = os.path.join(str(tmp_path), "test.db")
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v REAL)")
    conn.commit()
    conn.close()
    yield path


class TestScitexDbPresent:
    def test_loader_registered_for_dot_db(self):
        # Arrange
        # Act
        loader = get_loader(".db")
        # Assert
        assert callable(loader)

    def test_register_scitex_db_returns_true_when_present(self):
        # Arrange
        # Act
        registered = _optional_providers._register_scitex_db()
        # Assert
        assert registered is True

    def test_load_returns_scitex_db_sqlite3_wrapper(self, empty_db_path):
        # Arrange
        # Act
        result = scitex_io.load(empty_db_path, cache=False)
        # Assert
        assert isinstance(result, scitex_db.SQLite3)


class TestGracefulAbsent:
    """scitex-db absent is simulated with a real importer that returns None."""

    def test_register_scitex_db_returns_false_when_importer_yields_none(self):
        # Arrange: a real importer standing in for "package not installed".
        def absent_importer():
            return None

        # Act
        registered = _optional_providers._register_scitex_db(importer=absent_importer)
        # Assert
        assert registered is False

    def test_absent_provider_does_not_change_the_loader(self):
        # Arrange: capture the currently-resolved `.db` loader (set by the
        # autouse fixture that runs `list_formats()` -> the scitex-db
        # provider has already registered the real loader).
        before = get_loader(".db")

        def absent_importer():
            return None

        # Act
        _optional_providers._register_scitex_db(importer=absent_importer)

        # Assert: an absent provider never mutates the registry. The same
        # loader is still in place.
        assert get_loader(".db") is before
