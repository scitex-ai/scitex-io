"""Exercise real Bash ownership/cleanup and refusal boundaries, without SIF execution."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / ".github/ci/release-context.sh"
EXECUTOR = ROOT / ".github/ci/exec-in-sif.sh"


def shell(body):
    return (
        'set -euo pipefail\nSCRATCH_PREFIX="/tmp/io-control-test-"\n'
        f'source "{CONTEXT}"\n'
        'printf "OWNED=%s\\n" "$OWNED_TMPDIR"\n'
        "driver_body() {\n" + body + "\n}\nrun_owned_body\n"
    )


def run_body(body, timeout=15):
    return subprocess.run(
        ["bash", "-c", shell(body)], capture_output=True, text=True, timeout=timeout
    )


def owned_path(stdout):
    match = re.search(r"^OWNED=(/tmp/io-control-test-[A-Za-z0-9]{6})$", stdout, re.M)
    assert match is not None
    return Path(match.group(1))


def test_normal_body_cleans_only_its_exclusive_context():
    # Arrange
    body = 'printf fixture > "$TMPDIR/owned.txt"'
    # Act
    result = run_body(body)
    # Assert
    assert result.returncode == 0 and not owned_path(result.stdout).exists()


def test_body_failure_preserves_exit_status_after_cleanup():
    # Arrange
    body = "exit 23"
    # Act
    result = run_body(body)
    # Assert
    assert result.returncode == 23 and not owned_path(result.stdout).exists()


def test_replaced_context_is_not_deleted_by_cleanup():
    # Arrange
    body = 'mv "$TMPDIR" "$TMPDIR.moved"; mkdir "$TMPDIR"; printf keep > "$TMPDIR/sentinel"'
    # Act
    result = run_body(body)
    original = owned_path(result.stdout)
    try:
        # Assert
        assert result.returncode != 0 and (original / "sentinel").read_text() == "keep"
    finally:
        shutil.rmtree(original)
        shutil.rmtree(Path(str(original) + ".moved"))


def test_native_wrapper_refuses_unknown_driver_before_runtime_use():
    # Arrange
    command = ["bash", str(EXECUTOR), "unknown.sh", "3.12"]
    # Act
    result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    # Assert
    assert result.returncode != 0 and "unregistered release driver" in result.stderr


def test_native_wrapper_refuses_invalid_interpreter_before_runtime_use():
    # Arrange
    command = ["bash", str(EXECUTOR), "run-in-sif.sh", "3.12;false"]
    # Act
    result = subprocess.run(command, capture_output=True, text=True, timeout=5)
    # Assert
    assert result.returncode != 0


def test_native_wrapper_requires_verified_image_and_runtime_context():
    # Arrange: no actual image, runtime, or credentials can be reached.
    env = {k: v for k, v in os.environ.items() if not k.startswith("SCITEX_CI_")}
    # Act
    result = subprocess.run(
        ["bash", str(EXECUTOR), "run-in-sif.sh", "3.12"],
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    # Assert
    assert result.returncode != 0 and "SCITEX_CI_SIF" in result.stderr


@pytest.mark.parametrize(
    ("entries", "allocated", "expected"),
    [
        (10000, 1073741824, "10"),
        (10001, 0, "60"),
        (113918, 16009404416, "60"),
        (200000, 34359738368, "60"),
    ],
)
def test_reviewed_cleanup_budget_bounds(entries, allocated, expected):
    # Arrange
    body = f'printf "BUDGET=%s\\n" "$(owned_cleanup_budget {entries} {allocated})"'
    # Act
    result = run_body(body)
    # Assert
    assert f"BUDGET={expected}" in result.stdout and result.returncode == 0


@pytest.mark.parametrize(("entries", "allocated"), [(200001, 0), (1, 34359738369)])
def test_cleanup_budget_refuses_unreviewed_size(entries, allocated):
    # Arrange
    body = f"owned_cleanup_budget {entries} {allocated}"
    # Act
    result = run_body(body)
    # Assert
    assert result.returncode != 0


def test_cleanup_survey_counts_directory_entries():
    # Arrange
    body = """python3 -I -S - <<'PYTHON'
import os
from pathlib import Path
root = Path(os.environ["TMPDIR"])
for index in range(10001):
    (root / str(index)).mkdir()
PYTHON"""
    # Act
    # The new filesystem fixture has its reviewed 60s removal budget,
    # plus 15s for arranging real directories. Product deadlines are separate.
    result = run_body(body, timeout=75)
    # Assert
    assert result.returncode == 0 and "budget_seconds=60" in result.stderr
