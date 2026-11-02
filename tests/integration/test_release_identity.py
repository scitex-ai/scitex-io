"""Run the actual release boundary controls against real Git/Hatch artifacts."""

import subprocess
import sys
from pathlib import Path


def test_actual_release_artifact_controls_pass():
    # Arrange: the actual standalone preflight fixture suite uses owned source.
    script = Path(__file__).resolve().parents[2] / ".github/ci/test_release_identity.py"
    # Act
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, timeout=120
    )
    # Assert
    assert result.returncode == 0, result.stdout + result.stderr
