#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stats kind — re-export of scitex_stats._dataclasses (optional).

A stats bundle contains statistical test results (payload/stats.json).
The schema dataclasses are owned by the scitex_stats standalone; this
module is a re-export so the dispatcher's
``scitex_io.bundle.kinds._stats.Stats`` import path keeps working.

scitex_stats is an OPTIONAL ecosystem provider. Without it, the stats
kind is unavailable, but every other bundle kind (figure, plot, image,
text, shape, table) continues to work.
"""

try:
    from scitex_stats._dataclasses import (  # noqa: F401  # type: ignore[import-not-found]
        STATS_VERSION,
        Analysis,
        DataRef,
        EffectSize,
        Position,
        PositionMode,
        StatDisplay,
        StatMethod,
        StatPositioning,
        StatResult,
        Stats,
        StatStyling,
        SymbolStyle,
        UnitType,
    )

    _STATS_AVAILABLE = True
except ImportError:  # noqa: PERF203
    _STATS_AVAILABLE = False

    # Stubs raised when stats functionality is touched without
    # scitex_stats installed. Importing this module is always safe.
    class _StatsUnavailable:
        """Sentinel raised on attribute access when scitex_stats is missing."""

        def __getattr__(self, name):
            raise ImportError(
                "scitex_stats is not installed; install it to use stats bundles"
            )

    _stub = _StatsUnavailable()
    STATS_VERSION = "0.0.0"  # type: ignore[assignment]
    Analysis = _stub  # type: ignore[assignment]
    DataRef = _stub  # type: ignore[assignment]
    EffectSize = _stub  # type: ignore[assignment]
    Position = _stub  # type: ignore[assignment]
    PositionMode = _stub  # type: ignore[assignment]
    StatDisplay = _stub  # type: ignore[assignment]
    StatMethod = _stub  # type: ignore[assignment]
    StatPositioning = _stub  # type: ignore[assignment]
    StatResult = _stub  # type: ignore[assignment]
    Stats = _stub  # type: ignore[assignment]
    StatStyling = _stub  # type: ignore[assignment]
    SymbolStyle = _stub  # type: ignore[assignment]
    UnitType = _stub  # type: ignore[assignment]

from ._integration import (  # noqa: E402, F401
    BUNDLE_AVAILABLE,
    load_stats,
    save_stats,
    test_result_to_stats,
)

__all__ = [
    "STATS_VERSION",
    "Stats",
    "PositionMode",
    "UnitType",
    "SymbolStyle",
    "Position",
    "StatStyling",
    "StatPositioning",
    "DataRef",
    "EffectSize",
    "StatMethod",
    "StatResult",
    "StatDisplay",
    "Analysis",
    # Integration helpers (require optional scitex_stats at call time)
    "BUNDLE_AVAILABLE",
    "test_result_to_stats",
    "save_stats",
    "load_stats",
]
