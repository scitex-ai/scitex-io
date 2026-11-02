"""Ordinary tests never inherit a fleet store; native claims require ownership."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "_owned_io_store", ROOT / ".github/ci/io_test_store.py"
)
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


def test_ordinary_test_store_replaces_ambient_route_without_connecting():
    # Arrange
    environment = {
        "SCITEX_STORE_DSN": "postgresql://unowned.invalid/fleet",
        "PGHOSTADDR": "192.0.2.1",
        "PGPASSWORD": "owned-fixture-only",
    }
    # Act
    owned = GUARD.protect_suite_store(environment)
    try:
        observed = (
            "unavailable" in environment["SCITEX_STORE_DSN"],
            environment["SCITEX_CARDS_DB"] == environment["SCITEX_STORE_DSN"],
            "PGHOSTADDR" not in environment,
            "PGPASSWORD" not in environment,
            Path(environment["PGPASSFILE"]).stat().st_size,
        )
    finally:
        owned.cleanup()
    # Assert
    assert observed == (True, True, True, True, 0)


def test_native_marker_alone_cannot_authorize_tcp_store():
    # Arrange
    dsn = "postgresql://unowned.invalid/fleet"
    environment = {
        "SCITEX_IO_TEST_PG_REQUIRED": "1",
        "SCITEX_IO_TEST_PG_DSN": dsn,
        "SCITEX_STORE_DSN": dsn,
        "SCITEX_CARDS_DB": dsn,
    }
    # Act
    # Assert
    with pytest.raises(RuntimeError, match="Unix-socket DSN"):
        GUARD.protect_suite_store(environment)


def test_native_root_identity_mismatch_refuses_before_any_connection(tmp_path):
    # Arrange
    root = tmp_path / "scitex-store-test-owned-fixture"
    root.mkdir(mode=0o700)
    dsn = f"postgresql://postgres@/postgres?host={root / 'run'}"
    environment = {
        "SCITEX_IO_TEST_PG_REQUIRED": "1",
        "SCITEX_IO_TEST_PG_DSN": dsn,
        "SCITEX_STORE_DSN": dsn,
        "SCITEX_CARDS_DB": dsn,
        "TMPDIR": str(tmp_path),
        "SCITEX_IO_TEST_PG_ROOT": str(root),
        "SCITEX_IO_TEST_PG_ROOT_ID": f"0:0:{os.getuid()}:448",
    }
    # Act
    # Assert
    with pytest.raises(RuntimeError, match="ownership or identity"):
        GUARD.protect_suite_store(environment)
