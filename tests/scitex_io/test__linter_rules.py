#!/usr/bin/env python3
"""Tests for scitex_io._linter.rules."""

import scitex_io
from scitex_io._linter.rules import IOBypassTarget, iter_io_bypass_targets

# Alias spellings that appear as call_rules keys but must NOT surface as a
# module_path — callers import by module, so aliases have to be canonicalised.
_ALIASES = {"np", "pd", "sio", "plt", "Image", "cPickle"}
_CANONICAL = {"numpy", "pandas", "scipy.io", "matplotlib.pyplot", "PIL.Image"}


def test_public_export_on_package():
    # Arrange
    # Act
    exported = scitex_io.iter_io_bypass_targets
    # Assert
    assert exported is iter_io_bypass_targets


def test_returns_nonempty_target_list():
    # Arrange
    # Act
    targets = list(iter_io_bypass_targets())
    # Assert
    assert targets


def test_returns_iobypass_target_tuples():
    # Arrange
    # Act
    targets = list(iter_io_bypass_targets())
    # Assert
    assert all(isinstance(t, IOBypassTarget) for t in targets)


def test_no_duplicate_module_attr_pairs():
    # Arrange
    targets = list(iter_io_bypass_targets())
    # Act
    pairs = [(t.module_path, t.attr) for t in targets]
    # Assert
    assert len(pairs) == len(set(pairs))


def test_aliases_do_not_leak_as_module_paths():
    # Arrange
    targets = list(iter_io_bypass_targets())
    # Act
    modules = {t.module_path for t in targets}
    # Assert
    assert not (modules & _ALIASES)


def test_canonical_modules_are_present():
    # Arrange
    targets = list(iter_io_bypass_targets())
    # Act
    modules = {t.module_path for t in targets}
    # Assert
    assert _CANONICAL <= modules


def test_receiver_agnostic_rules_are_skipped():
    # Arrange
    # (None, "savefig") in call_rules has no module path to import.
    targets = list(iter_io_bypass_targets())
    # Act
    savefig_targets = [t for t in targets if t.attr == "savefig"]
    # Assert
    assert not savefig_targets


def test_sqlite3_connect_present_with_io015():
    # Arrange
    targets = list(iter_io_bypass_targets())
    # Act
    rule_ids = [
        t.rule_id
        for t in targets
        if t.module_path == "sqlite3" and t.attr == "connect"
    ]
    # Assert
    assert rule_ids == ["STX-IO015"]


def test_severity_is_passed_through_unfiltered():
    # Arrange
    # Both warning (default IO/PA rules) and info (PA003) must survive —
    # this module does not filter by severity, callers decide policy.
    targets = list(iter_io_bypass_targets())
    # Act
    severities = {t.severity for t in targets}
    # Assert
    assert {"warning", "info"} <= severities
