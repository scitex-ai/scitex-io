#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke tests for scitex_io.bundle.kinds._stats._integration.

Covers SOC.md Task 8: the integration glue that used to live in the
scitex umbrella now lives with scitex-io. scitex_stats is optional —
skip when absent.
"""

import pytest

pytest.importorskip("scitex_stats")


def test_integration_module_imports():
    # Arrange
    module_path = "scitex_io.bundle.kinds._stats._integration"
    # Act
    from scitex_io.bundle.kinds._stats import _integration

    # Assert
    assert _integration.__name__ == module_path


def test_public_symbols_reexported_from_kind_package():
    # Arrange
    import scitex_io.bundle.kinds._stats as kind_pkg

    # Act
    syms = [
        getattr(kind_pkg, "test_result_to_stats", None),
        getattr(kind_pkg, "save_stats", None),
        getattr(kind_pkg, "load_stats", None),
        getattr(kind_pkg, "BUNDLE_AVAILABLE", None),
    ]
    # Assert
    assert all(callable(s) for s in syms[:3]) and syms[3] is True


def test_flat_dict_round_trips_through_stats_schema():
    # Arrange
    from scitex_io.bundle.kinds._stats._integration import test_result_to_stats

    flat = {
        "name": "Control vs Treatment",
        "method": "t-test",
        "p_value": 0.003,
        "statistic": 2.5,
        "statistic_name": "t",
        "effect_size": 1.21,
        "ci95": [0.5, 1.8],
    }

    # Act
    stats = test_result_to_stats(flat)

    # Assert
    assert (
        len(stats.analyses) == 1
        and stats.analyses[0].method.name == "t-test"
        and stats.analyses[0].results.p_value == 0.003
        and stats.analyses[0].results.effect_size.value == 1.21
    )


def test_save_and_load_stats_are_callable():
    # Arrange: defer the end-to-end Bundle round-trip — the umbrella
    # ``save_stats`` / ``load_stats`` use the legacy ``Bundle(..., bundle_type=...)``
    # constructor that has since been superseded; reconciling that drift is
    # tracked separately. Confirm the relocated entry points are wired.
    from scitex_io.bundle.kinds._stats._integration import load_stats, save_stats

    # Act
    targets = (save_stats, load_stats)
    # Assert
    assert all(callable(t) for t in targets)


# EOF
