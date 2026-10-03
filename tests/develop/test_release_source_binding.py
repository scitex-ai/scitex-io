"""Exercise release helper source selection against real, disposable Git history."""

import os
import subprocess
from pathlib import Path

import pytest
from ruamel.yaml import YAML

WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github/workflows/pypi-publish-and-github-release-on-tag.yml"
)


def _git(repo, *args, check=True):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Release test",
            "-c",
            "user.email=test@example.invalid",
            *args,
        ],
        cwd=repo,
        check=check,
        capture_output=True,
        text=True,
        timeout=5,
    )


@pytest.fixture
def history(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "develop")
    driver = repo / "publisher.sh"
    driver.write_text("tagged artifact helper\n")
    _git(repo, "add", "publisher.sh")
    _git(repo, "commit", "-qm", "artifact source")
    artifact_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    _git(repo, "tag", "v0.4.2")
    driver.write_text("later dispatch helper\n")
    _git(repo, "commit", "-qam", "dispatch source")
    dispatch_commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    return repo, artifact_commit, dispatch_commit


def _checkout_ref(job, outputs, dispatch_ref):
    checkout = next(
        step for step in job["steps"] if step.get("uses") == "actions/checkout@v4"
    )
    expression = checkout.get("with", {}).get("ref")
    if expression is None:
        return dispatch_ref
    refs = {
        "${{ needs.build.outputs.commit }}": outputs["commit"],
        "${{ needs.build.outputs.version }}": outputs["version"],
    }
    return refs[expression]


def _pin_actual_build_source(repo, tmp_path):
    workflow = YAML(typ="safe").load(WORKFLOW)
    build = workflow["jobs"]["build"]
    step = next(item for item in build["steps"] if item.get("id") == "source")
    output = tmp_path / "github-output"
    env = dict(os.environ, GITHUB_OUTPUT=str(output))
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-c", step["run"]],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=5,
    )
    values = (
        dict(line.split("=", 1) for line in output.read_text().splitlines())
        if output.exists()
        else {}
    )
    assert build["outputs"]["commit"] == "${{ steps.source.outputs.commit }}"
    return workflow, result, values


def _verify_actual_consumer_source(repo, job, commit):
    step = next(item for item in job["steps"] if item.get("id") == "source-check")
    assert step["env"]["BUILD_COMMIT"] == "${{ needs.build.outputs.commit }}"
    return subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-c", step["run"]],
        cwd=repo,
        env=dict(os.environ, BUILD_COMMIT=commit),
        capture_output=True,
        text=True,
        timeout=5,
    )


@pytest.mark.parametrize("job_name", ["publish", "release"])
@pytest.mark.parametrize(
    "observation", ["capture_status", "verification_status", "commit", "helper"]
)
def test_manual_dispatch_uses_the_artifact_commit(
    history, tmp_path, job_name, observation
):
    # Arrange
    repo, artifact_commit, dispatch_commit = history
    _git(repo, "checkout", "-q", "v0.4.2")
    workflow, pin, outputs = _pin_actual_build_source(repo, tmp_path)
    outputs["version"] = "v0.4.2"

    # Act
    ref = _checkout_ref(workflow["jobs"][job_name], outputs, dispatch_commit)
    _git(repo, "checkout", "-q", ref)
    verification = _verify_actual_consumer_source(
        repo, workflow["jobs"][job_name], outputs["commit"]
    )

    # Assert
    observed = {
        "capture_status": pin.returncode,
        "verification_status": verification.returncode,
        "commit": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "helper": (repo / "publisher.sh").read_text(),
    }
    expected = {
        "capture_status": 0,
        "verification_status": 0,
        "commit": artifact_commit,
        "helper": "tagged artifact helper\n",
    }
    assert observed[observation] == expected[observation]


@pytest.mark.parametrize("job_name", ["publish", "release"])
@pytest.mark.parametrize(
    "observation",
    ["capture_status", "verification_status", "moved_tag", "commit", "helper"],
)
def test_tag_movement_after_build_cannot_change_helpers(
    history, tmp_path, job_name, observation
):
    # Arrange
    repo, artifact_commit, dispatch_commit = history
    _git(repo, "checkout", "-q", "v0.4.2")
    workflow, pin, outputs = _pin_actual_build_source(repo, tmp_path)
    outputs["version"] = "v0.4.2"
    _git(repo, "tag", "-f", "v0.4.2", dispatch_commit)

    # Act
    ref = _checkout_ref(workflow["jobs"][job_name], outputs, dispatch_commit)
    _git(repo, "checkout", "-q", ref)
    verification = _verify_actual_consumer_source(
        repo, workflow["jobs"][job_name], outputs["commit"]
    )

    # Assert
    observed = {
        "capture_status": pin.returncode,
        "verification_status": verification.returncode,
        "moved_tag": _git(repo, "rev-parse", "v0.4.2").stdout.strip(),
        "commit": _git(repo, "rev-parse", "HEAD").stdout.strip(),
        "helper": (repo / "publisher.sh").read_text(),
    }
    expected = {
        "capture_status": 0,
        "verification_status": 0,
        "moved_tag": dispatch_commit,
        "commit": artifact_commit,
        "helper": "tagged artifact helper\n",
    }
    assert observed[observation] == expected[observation]


@pytest.mark.parametrize("observation", ["capture_status", "refs"])
def test_push_tag_keeps_the_same_helper_source(history, tmp_path, observation):
    # Arrange
    repo, artifact_commit, _ = history
    _git(repo, "checkout", "-q", "v0.4.2")
    workflow, pin, outputs = _pin_actual_build_source(repo, tmp_path)
    outputs["version"] = "v0.4.2"

    # Act
    refs = [
        _checkout_ref(workflow["jobs"][name], outputs, artifact_commit)
        for name in ("publish", "release")
    ]

    # Assert
    assert {"capture_status": pin.returncode, "refs": refs}[observation] == {
        "capture_status": 0,
        "refs": [artifact_commit, artifact_commit],
    }[observation]


def test_missing_release_tag_fails_checkout_before_source_capture(history):
    # Arrange
    repo, _, _ = history

    # Act
    result = _git(repo, "checkout", "v-missing", check=False)

    # Assert
    assert result.returncode != 0


@pytest.mark.parametrize("observation", ["failed", "commit_absent"])
def test_unborn_checkout_cannot_emit_an_artifact_commit(tmp_path, observation):
    # Arrange
    repo = tmp_path / "empty-repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "develop")

    # Act
    _, pin, outputs = _pin_actual_build_source(repo, tmp_path)

    # Assert
    assert {"failed": pin.returncode != 0, "commit_absent": "commit" not in outputs}[
        observation
    ]


@pytest.mark.parametrize("job_name", ["publish", "release"])
@pytest.mark.parametrize("missing_or_wrong", ["", "artifact"])
def test_missing_or_mismatched_commit_refuses_dispatch_helpers(
    history, job_name, missing_or_wrong
):
    # Arrange
    repo, artifact_commit, dispatch_commit = history
    workflow = YAML(typ="safe").load(WORKFLOW)
    _git(repo, "checkout", "-q", dispatch_commit)
    expected = artifact_commit if missing_or_wrong else ""

    # Act
    result = _verify_actual_consumer_source(repo, workflow["jobs"][job_name], expected)

    # Assert
    assert result.returncode != 0
