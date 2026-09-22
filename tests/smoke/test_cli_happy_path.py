#!/usr/bin/env python3
"""Smoke layer — fast (<60s) subprocess-driven CLI happy-path tests.

Runs the real ``scitex-io`` entry point in a subprocess (no mocks);
the ``_smoke_env_isolation`` fixture redirects ``SCITEX_DIR`` at tmp.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

pytestmark = pytest.mark.smoke


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "scitex_io", *args],
        capture_output=True,
        text=True,
        timeout=60,
    )


def test_list_python_apis_exits_zero():
    # Arrange
    # Act
    proc = _run_cli("list-python-apis")
    # Assert
    assert proc.returncode == 0


def test_list_python_apis_names_core_save_api():
    # Arrange
    # Act
    proc = _run_cli("list-python-apis")
    # Assert
    assert "scitex_io.save" in proc.stdout
