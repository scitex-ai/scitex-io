"""Compile-only smoke for examples/02_custom_format.py (PS303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "02_custom_format.py"


def test_exists_example_exists():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert EXAMPLE.exists(), f"missing example: {EXAMPLE}"


def test_compiles_r_returncode_equals_n_0():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    _r = subprocess.run([sys.executable, "-m", "py_compile", str(EXAMPLE)], check=True)
    # Assert
    assert _r.returncode == 0
