#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the scitex_stats branch of ``scitex_io._optional_providers``.

Two behaviours are contracted, parallel to the figrecipe branch:

- **scitex_stats present** → ``.stats.zip`` dispatches through the registry
  and ``save`` / ``load`` round-trip a stats bundle.
- **scitex_stats absent** → ``.stats.zip`` stays unregistered and
  ``_register_scitex_stats`` reports ``False`` rather than raising.
"""

import pytest

import scitex_io
from scitex_io import _optional_providers
from scitex_io._registry import get_loader, get_saver

scitex_stats = pytest.importorskip("scitex_stats", reason="scitex_stats optional extra")


@pytest.fixture(autouse=True)
def _ensure_registered():
    # Arrange: trigger _ensure_builtin_handlers_registered (idempotent).
    scitex_io.list_formats()
    yield


@pytest.fixture
def stats_payload():
    # Arrange: a minimal spec that survives the round-trip with no
    # supplementary data file.
    return {
        "spec": {
            "schema": "scitex.stats.stats",
            "version": "1.0.0",
            "comparisons": [{"p_value": 0.04}],
        }
    }


class TestScitexStatsPresent:
    def test_stats_zip_is_a_declared_compound_ext(self):
        # Arrange
        exts = _optional_providers.OPTIONAL_COMPOUND_EXTS
        # Act
        # Assert
        assert ".stats.zip" in exts

    def test_saver_registered_for_stats_zip(self):
        # Arrange
        # Act
        saver = get_saver(".stats.zip")
        # Assert
        assert callable(saver)

    def test_loader_registered_for_stats_zip(self):
        # Arrange
        # Act
        loader = get_loader(".stats.zip")
        # Assert
        assert callable(loader)

    def test_register_scitex_stats_returns_true_when_present(self):
        # Arrange
        # Act
        registered = _optional_providers._register_scitex_stats()
        # Assert
        assert registered is True

    def test_save_writes_stats_zip_bundle(self, stats_payload, tmp_path):
        # Arrange
        target = tmp_path / "results.stats.zip"
        # Act
        scitex_io.save(stats_payload, str(target), verbose=False)
        # Assert
        assert target.exists()

    def test_load_round_trips_stats_zip_spec(self, stats_payload, tmp_path):
        # Arrange
        target = tmp_path / "results.stats.zip"
        scitex_io.save(stats_payload, str(target), verbose=False)
        # Act
        loaded = scitex_io.load(str(target), cache=False)
        # Assert
        assert loaded["spec"] == stats_payload["spec"]


class TestGracefulAbsent:
    """scitex_stats absent is simulated with a real importer that returns None."""

    def test_register_scitex_stats_returns_false_when_importer_yields_none(self):
        # Arrange
        def absent_importer():
            return None

        # Act
        registered = _optional_providers._register_scitex_stats(
            importer=absent_importer
        )
        # Assert
        assert registered is False
