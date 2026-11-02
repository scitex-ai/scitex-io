#!/usr/bin/env python3
"""Isolation for smoke tests — redirect SCITEX_DIR at a tmp dir.

Explicit save/restore (no ``monkeypatch``): snapshot on enter, restore
exact state on exit. ``SCITEX_DIR`` is the only scitex-io state root the
CLI happy-path touches; this package has no API-key var to blank.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def _smoke_env_isolation(tmp_path):
    snapshot = os.environ.copy()
    os.environ["SCITEX_DIR"] = str(tmp_path / "scitex_dir")
    try:
        yield
    finally:
        for key in list(os.environ.keys()):
            if key not in snapshot:
                del os.environ[key]
        for key, value in snapshot.items():
            if os.environ.get(key) != value:
                os.environ[key] = value
