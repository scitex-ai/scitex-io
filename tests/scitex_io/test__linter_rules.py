#!/usr/bin/env python3
"""Tests for scitex_io._linter_rules."""

import scitex_io
from scitex_io._linter_rules import IOBypassTarget, iter_io_bypass_targets


def test_public_export_on_package():
    assert scitex_io.iter_io_bypass_targets is iter_io_bypass_targets


def test_returns_iobypass_target_tuples():
    targets = list(iter_io_bypass_targets())
    assert targets
    assert all(isinstance(t, IOBypassTarget) for t in targets)


def test_no_duplicate_module_attr_pairs():
    targets = list(iter_io_bypass_targets())
    pairs = [(t.module_path, t.attr) for t in targets]
    assert len(pairs) == len(set(pairs))


def test_aliases_collapse_to_canonical_module():
    targets = list(iter_io_bypass_targets())
    modules = {t.module_path for t in targets}
    # Aliases must not leak through as their own module_path.
    assert "np" not in modules
    assert "pd" not in modules
    assert "sio" not in modules
    assert "plt" not in modules
    assert "Image" not in modules
    assert "cPickle" not in modules
    # Canonical forms must be present instead.
    assert "numpy" in modules
    assert "pandas" in modules
    assert "scipy.io" in modules
    assert "matplotlib.pyplot" in modules
    assert "PIL.Image" in modules


def test_receiver_agnostic_rules_are_skipped():
    # (None, "savefig") in call_rules has no module path to import.
    targets = list(iter_io_bypass_targets())
    assert not any(t.attr == "savefig" for t in targets)


def test_sqlite3_connect_present_with_io015():
    targets = list(iter_io_bypass_targets())
    match = [t for t in targets if t.module_path == "sqlite3" and t.attr == "connect"]
    assert len(match) == 1
    assert match[0].rule_id == "STX-IO015"


def test_severity_is_passed_through_unfiltered():
    targets = list(iter_io_bypass_targets())
    severities = {t.severity for t in targets}
    # Both warning (default IO/PA rules) and info (PA003) must survive —
    # this module does not filter by severity, callers decide policy.
    assert "warning" in severities
    assert "info" in severities
