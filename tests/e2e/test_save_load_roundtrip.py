#!/usr/bin/env python3
"""E2E layer — save/load round-trips against real subsystems (no network).

Gated by ``RUN_E2E=1`` (skipped by default); the ``_e2e_env_isolation``
fixture redirects ``SCITEX_DIR`` at tmp. Real collaborators only.
"""

from __future__ import annotations

import os

import pytest

import scitex_io

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("RUN_E2E") != "1",
        reason="e2e: set RUN_E2E=1 to run end-to-end workflows",
    ),
]


def test_json_roundtrip_value_matches(tmp_path):
    # Arrange
    out = str(tmp_path / "payload.json")
    # Act
    scitex_io.save({"a": 1}, out)
    # Assert
    assert scitex_io.load(out)["a"] == 1


def test_csv_roundtrip_shape_matches(tmp_path):
    # Arrange
    pd = pytest.importorskip("pandas")
    out = str(tmp_path / "frame.csv")
    # Act
    scitex_io.save(pd.DataFrame({"x": [1, 2, 3]}), out)
    # Assert
    assert scitex_io.load(out).shape == (3, 1)
