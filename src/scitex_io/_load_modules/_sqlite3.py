#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite3 loader for scitex-io.

Returns the *rich* SQLite wrapper from ``scitex_db`` when that package
is installed (the wrapper that exposes ``get_rows`` / ``load_arrays``
/ ``insert_many`` / …). Falls back to a minimal context-manager
wrapper around :class:`sqlite3.Connection` when ``scitex_db`` is not
available, so importing this module never raises.

Background
----------
Earlier versions of this loader returned a thin wrapper whose
``__enter__`` yielded the bare :class:`sqlite3.Connection`. Downstream
code (in particular ``neurovista/scripts/io/load_pac.py``) was written
against the older scitex API where ``stx.io.load(*.db)`` exposed
``get_rows`` / ``load_arrays`` directly, and broke at runtime with::

    AttributeError: 'sqlite3.Connection' object has no attribute 'get_rows'

The fix aligns the loader with ``scitex_db.SQLite3`` — the package
the rich SQLite API now lives in — without taking a hard dependency
on it. ``scitex-io`` stays usable in environments that only need the
thin connection wrapper; if ``scitex-db`` is on the import path, the
loader transparently upgrades.

Behaviour
---------
* ``with stx.io.load("file.db") as db:`` enters the context manager
  defined by ``scitex_db.SQLite3``: ``db`` is the ``SQLite3``
  instance itself, with ``get_rows`` / ``load_arrays`` / … available
  inside the ``with`` block.
* If ``scitex_db`` is not installed, ``db`` is the bare
  :class:`sqlite3.Connection` (the previous behaviour). The fallback
  class's docstring names the missing package so users get a hint
  when introspecting.
"""

from __future__ import annotations

import os
import sqlite3

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)


try:
    # Prefer the rich SQLite3 wrapper from scitex-db. Any import-time
    # failure (including the package not being installed) falls through
    # to the local minimal wrapper defined below.
    from scitex_db import SQLite3 as SQLite3  # type: ignore[no-redef]
except Exception:  # noqa: BLE001
    SQLite3 = None  # type: ignore[assignment]


if SQLite3 is None:

    class SQLite3:  # type: ignore[no-redef]
        """Minimal SQLite3 context-manager wrapper (fallback).

        Used when ``scitex-db`` is not installed. ``__enter__`` returns
        the bare :class:`sqlite3.Connection`. Install ``scitex-db`` for
        the rich API (``get_rows`` / ``load_arrays`` / …).
        """

        def __init__(self, db_path):
            self.conn = sqlite3.connect(db_path)

        def __enter__(self):
            return self.conn

        def __exit__(self, *args):
            self.conn.close()


_load_db_sqlite3 = SQLite3

__all__ = ["SQLite3", "_load_db_sqlite3"]

# EOF
