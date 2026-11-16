#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Observer failures are counted, WARNed once per kind, fatal in strict mode."""

from __future__ import annotations

import logging

import pytest

import scitex_io
from scitex_io._observers import (
    ProvenanceError,
    observer_failures,
    provenance_scope,
    register_post_load_hook,
    register_post_save_hook,
)


@pytest.fixture
def two_failing_saves(hooks, boom, tmp_path, caplog):
    register_post_save_hook(boom)
    with caplog.at_level(logging.DEBUG):
        scitex_io.save("a", str(tmp_path / "a.txt"), verbose=False)
        scitex_io.save("b", str(tmp_path / "b.txt"), verbose=False)
    return observer_failures(), caplog


def test_failing_save_hook_counts_every_failure(two_failing_saves):
    # Arrange
    report, _ = two_failing_saves
    # Act
    total = report["total"]
    # Assert
    assert total == 2


def test_failing_save_hook_is_tallied_under_post_save(two_failing_saves):
    # Arrange
    report, _ = two_failing_saves
    # Act
    by_kind = report["by_kind"]
    # Assert
    assert by_kind == {"post_save": 2}


def test_failing_save_hook_event_records_hook_and_error(two_failing_saves):
    # Arrange
    report, _ = two_failing_saves
    # Act
    (event,) = report["events"]
    # Assert
    assert (event["hook"].endswith("._boom"), event["error_type"], event["count"]) == (
        True,
        "RuntimeError",
        2,
    )


def test_failing_save_hook_warns_exactly_once(two_failing_saves, provenance_warnings):
    # Arrange
    _, caplog = two_failing_saves
    # Act
    warnings = provenance_warnings(caplog)
    # Assert
    assert len(warnings) == 1


def test_failure_warning_carries_the_exception(two_failing_saves, provenance_warnings):
    # Arrange
    _, caplog = two_failing_saves
    # Act
    (warning,) = provenance_warnings(caplog)
    # Assert
    assert isinstance(warning.exc_info[1], RuntimeError)


def test_failing_load_hook_is_tallied_under_post_load(hooks, boom, tmp_path):
    # Arrange
    path = tmp_path / "x.txt"
    scitex_io.save("x", str(path), verbose=False)
    register_post_load_hook(boom)
    # Act
    scitex_io.load(str(path))
    # Assert
    assert observer_failures()["by_kind"] == {"post_load": 1}


def test_failing_load_hook_does_not_break_the_load(hooks, boom, tmp_path):
    # Arrange
    path = tmp_path / "y.txt"
    scitex_io.save("y", str(path), verbose=False)
    register_post_load_hook(boom)
    # Act
    data = scitex_io.load(str(path))
    # Assert
    assert data == ["y"]


def test_strict_mode_save_raises_provenance_error(strict_env, boom, tmp_path):
    # Arrange
    register_post_save_hook(boom)
    # Act
    call = lambda: scitex_io.save("s", str(tmp_path / "s.txt"), verbose=False)  # noqa: E731
    # Assert
    with pytest.raises(ProvenanceError, match="observer exploded"):
        call()


def test_strict_mode_still_writes_the_data(strict_env, boom, tmp_path):
    # Arrange
    register_post_save_hook(boom)
    path = tmp_path / "kept.txt"
    # Act
    try:
        scitex_io.save("s", str(path), verbose=False)
    except ProvenanceError:
        pass
    # Assert
    assert path.read_text() == "s"


def test_strict_mode_load_raises_provenance_error(strict_env, boom, tmp_path):
    # Arrange
    path = tmp_path / "strict_load.txt"
    path.write_text("s\n")
    register_post_load_hook(boom)
    # Act
    call = lambda: scitex_io.load(str(path), cache=False)  # noqa: E731
    # Assert
    with pytest.raises(ProvenanceError):
        call()


def test_report_states_strict_mode(strict_env):
    # Arrange
    # Act
    report = observer_failures()
    # Assert
    assert report["strict"] is True


def test_counters_are_public_api():
    # Arrange
    # Act
    exposed = (scitex_io.observer_failures, scitex_io.ProvenanceError)
    # Assert
    assert exposed == (observer_failures, ProvenanceError)


@pytest.fixture
def scoped_run(hooks, boom, tmp_path):
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(kw["provenance"]))
    scitex_io.save("o", str(tmp_path / "outside.txt"), verbose=False)
    register_post_save_hook(boom)
    with provenance_scope("run-1") as scope:
        scitex_io.save("i", str(tmp_path / "inside.txt"), verbose=False)
    return seen, scope, observer_failures()


def test_out_of_scope_save_is_flagged_in_payload(scoped_run):
    # Arrange
    seen, _, _ = scoped_run
    # Act
    outside = seen[0]
    # Assert
    assert (outside["in_scope"], outside["scope"]) == (False, None)


def test_in_scope_save_names_its_scope(scoped_run):
    # Arrange
    seen, _, _ = scoped_run
    # Act
    inside = seen[1]
    # Assert
    assert (inside["in_scope"], inside["scope"]) == (True, "run-1")


def test_scope_counts_only_its_own_failures(scoped_run):
    # Arrange
    _, scope, _ = scoped_run
    # Act
    failures = scope.failures()
    # Assert
    assert (failures["total"], failures["scope"]) == (1, "run-1")


def test_out_of_scope_saves_are_counted(scoped_run):
    # Arrange
    _, _, report = scoped_run
    # Act
    unscoped = report["unscoped_saves"]
    # Assert
    assert unscoped == 1
