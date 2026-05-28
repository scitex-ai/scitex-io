#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``scitex_io.bundle`` — generic bundle plumbing.

Format-agnostic bundle primitives: types (``BundleType``, extensions,
error classes) and shared dataclasses (``Spec``, ``DataInfo``, ``SizeMM``,
``BBox``, …). Each domain package (figrecipe for figures/plots,
scitex_stats for statistics) layers its own kind handlers on top via
``scitex_io._optional_providers``.

This is the new home for what historically lived under
``scitex.io.bundle._types`` and ``scitex.io.bundle._dataclasses`` in the
umbrella. The umbrella now thin-re-exposes ``scitex_io.bundle.*`` so
``scitex.io.bundle.{BundleType, Spec, …}`` keeps working for any
external caller.
"""

from ._dataclasses import (  # noqa: F401
    DATA_INFO_VERSION,
    Axes,
    BBox,
    ColumnDef,
    DataFormat,
    DataInfo,
    DataSource,
    ShapeParams,
    SizeMM,
    Spec,
    SpecRefs,
    TextContent,
)
from ._types import (  # noqa: F401
    DIR_EXTENSIONS,
    EXTENSIONS,
    FIGURE,
    PLOT,
    STATS,
    BundleError,
    BundleNotFoundError,
    BundleType,
    BundleValidationError,
    NestedBundleNotFoundError,
)

__all__ = [
    # Types
    "BundleType",
    "BundleError",
    "BundleValidationError",
    "BundleNotFoundError",
    "NestedBundleNotFoundError",
    "EXTENSIONS",
    "DIR_EXTENSIONS",
    "FIGURE",
    "PLOT",
    "STATS",
    # Dataclasses
    "BBox",
    "SizeMM",
    "Axes",
    "Spec",
    "SpecRefs",
    "TextContent",
    "ShapeParams",
    "DATA_INFO_VERSION",
    "DataSource",
    "DataFormat",
    "DataInfo",
    "ColumnDef",
]
