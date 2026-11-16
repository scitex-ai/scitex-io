"""The native qualification route must not acquire publishing authority."""

from pathlib import Path
import re

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def _workflow():
    return yaml.safe_load((ROOT / ".github/workflows/native-qualification.yml").read_text())


def test_qualification_cannot_add_publishing_jobs_or_oidc_authority():
    # Arrange
    workflow = _workflow()
    jobs = workflow["jobs"]
    # Act
    publishing = any("environment" in job or
                     job.get("permissions", {}).get("id-token") == "write"
                     for job in jobs.values())
    # Assert
    assert (workflow["permissions"], set(jobs), publishing) == (
        {"contents": "read"}, {"admission", "preflight", "test", "build"}, False)


@pytest.mark.parametrize("operation", ["test", "build"])
def test_each_native_operation_requires_admission_and_resolved_tag_source(operation):
    # Arrange
    job = _workflow()["jobs"][operation]
    # Act
    pinned = re.fullmatch(
        r"scitex-ai/\.github/\.github/workflows/leaf-release-sif\.yml@[a-f0-9]{40}",
        job["uses"],
    ) is not None
    # Assert
    assert (set(job["needs"]) >= {"admission", "preflight"}, pinned,
            job["if"], job["with"]) == (
        True, True, "needs.admission.outputs.native_authorized == 'true'",
        {"operation": operation,
         "source_commit": "${{ needs.preflight.outputs.commit }}",
         "release_tag": "${{ needs.preflight.outputs.tag }}"})


def test_build_cannot_start_before_the_complete_test_matrix_succeeds():
    # Arrange
    job = _workflow()["jobs"]["build"]
    # Act
    requires_tests = "test" in job["needs"]
    # Assert
    assert (requires_tests, job.get("continue-on-error", False)) == (True, False)


def test_manual_request_accepts_a_tag_instead_of_an_arbitrary_source_override():
    # Arrange
    workflow = _workflow()
    triggers = workflow.get("on", workflow.get(True))
    # Act
    inputs = triggers["workflow_dispatch"]["inputs"]
    # Assert
    assert (set(triggers), set(inputs), inputs["tag"]["required"],
            workflow["env"]["RELEASE_TAG"]) == (
        {"workflow_dispatch"}, {"tag"}, True, "${{ inputs.tag }}")
