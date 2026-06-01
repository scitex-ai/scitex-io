#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ``scitex_io._load_modules._sqlite3``.

Covers two code paths:

1. **Rich path** — when ``scitex_db`` is importable, the loader's
   ``SQLite3`` symbol IS ``scitex_db.SQLite3`` (identity check), and the
   rich methods (``get_rows`` / ``load_arrays`` / ``insert_many``) are
   present on the class.

2. **Fallback path** — when ``scitex_db`` cannot be imported, the
   loader exposes a minimal context-manager class whose ``__enter__``
   yields the bare :class:`sqlite3.Connection`. Simulated by hiding
   ``scitex_db`` from ``sys.modules`` and reimporting the module.

3. **Runtime smoke** — under whichever code path is active, calling the
   loader on a temp on-disk SQLite DB round-trips a small table.

These tests do not depend on any external data file.
"""

from __future__ import annotations

import builtins
import importlib
import os
import sqlite3
import sys
import tempfile

import pytest


SQLITE3_LOADER_MODULE = "scitex_io._load_modules._sqlite3"


def _reimport_loader():
    """Drop the cached loader module and re-import. Returns the module."""
    sys.modules.pop(SQLITE3_LOADER_MODULE, None)
    return importlib.import_module(SQLITE3_LOADER_MODULE)


def _has_scitex_db() -> bool:
    try:
        importlib.import_module("scitex_db")
        return True
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------- #
# 1. Rich path (only meaningful when scitex_db is installed)
# --------------------------------------------------------------------- #
@pytest.mark.skipif(
    not _has_scitex_db(), reason="scitex_db not installed"
)
def test_rich_path_is_scitex_db_sqlite3():
    mod = _reimport_loader()
    from scitex_db import SQLite3 as DBSQLite3

    # The loader's SQLite3 IS the scitex_db SQLite3 class.
    assert mod.SQLite3 is DBSQLite3, (
        "with scitex_db installed, the loader must alias "
        "scitex_db.SQLite3 directly (no re-wrapping)."
    )
    # `_load_db_sqlite3` is the registry-facing alias and must agree.
    assert mod._load_db_sqlite3 is mod.SQLite3


@pytest.mark.skipif(
    not _has_scitex_db(), reason="scitex_db not installed"
)
def test_rich_path_exposes_get_rows_and_load_arrays():
    mod = _reimport_loader()
    for required in ("get_rows", "load_arrays"):
        assert hasattr(mod.SQLite3, required), (
            f"rich SQLite3 wrapper must expose `{required}` "
            f"(this method is what downstream load_pac-style code calls)"
        )


# --------------------------------------------------------------------- #
# 2. Fallback path (simulated by hiding scitex_db)
# --------------------------------------------------------------------- #
def test_fallback_path_when_scitex_db_missing(monkeypatch):
    # Force the import to fail by stubbing sys.modules + __import__.
    monkeypatch.setitem(sys.modules, "scitex_db", None)
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "scitex_db" or name.startswith("scitex_db."):
            raise ImportError("simulated: scitex_db not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    mod = _reimport_loader()

    # Fallback class is defined in THIS module, not scitex_db.
    assert mod.SQLite3.__module__ == SQLITE3_LOADER_MODULE, (
        "with scitex_db unavailable, the loader must fall back to its "
        "own minimal wrapper; got "
        f"{mod.SQLite3.__module__!r}"
    )
    assert mod._load_db_sqlite3 is mod.SQLite3

    # __enter__ must yield a bare sqlite3.Connection (legacy behaviour).
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    try:
        with mod.SQLite3(tmp.name) as conn:
            assert isinstance(conn, sqlite3.Connection)
            conn.execute("CREATE TABLE t (k INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO t VALUES (1)")
            conn.commit()
            (got,) = conn.execute("SELECT k FROM t").fetchone()
            assert got == 1
    finally:
        os.unlink(tmp.name)


# --------------------------------------------------------------------- #
# 3. Runtime smoke under whichever path is active
# --------------------------------------------------------------------- #
def test_runtime_smoke_roundtrips_a_tiny_table():
    """Whichever path is active, the registered `.db` loader must
    let a caller open a real SQLite file and read back a row.

    This intentionally goes through `_load_db_sqlite3` (the registry
    entry point, identical to `SQLite3`), so it pins the contract the
    registry depends on.
    """
    from scitex_io._load_modules._sqlite3 import _load_db_sqlite3

    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    # Pre-populate the file with one row using stdlib sqlite3.
    raw = sqlite3.connect(tmp.name)
    try:
        raw.execute("CREATE TABLE t (k INTEGER, v TEXT)")
        raw.execute("INSERT INTO t VALUES (?, ?)", (42, "hello"))
        raw.commit()
    finally:
        raw.close()

    try:
        with _load_db_sqlite3(tmp.name) as db:
            # Both code paths must support raw SQL via .execute(...) or
            # via the rich wrapper's `get_rows`. We probe both:
            if hasattr(db, "get_rows"):
                df = db.get_rows("t")
                assert len(df) == 1
                assert int(df.iloc[0]["k"]) == 42
                assert df.iloc[0]["v"] == "hello"
            else:
                # Fallback path: db is the bare Connection.
                (k, v) = db.execute("SELECT k, v FROM t").fetchone()
                assert k == 42 and v == "hello"
    finally:
        os.unlink(tmp.name)


# --------------------------------------------------------------------- #
# Standalone runner (kept for parity with other tests in this dir)
# --------------------------------------------------------------------- #
if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
