#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load handler submodules for ``scitex_io.load``.

Each ``_load_modules._<format>`` submodule defines a ``_load_<format>``
callable. They are no longer eagerly swept at package import time — the
old directory-scanning loop that ``importlib.import_module``'d every
``.py`` here was the root cause of the eager fan-out incident
(2026-06-01, libgthread on minimal containers): merely touching
``_load_modules`` pulled PIL, pymupdf, pdfminer, h5py, scipy, plotly,
etc. even for a JSON-only ``save``.

Format handlers are now registered explicitly in
``scitex_io._builtin_handlers._LAZY_LOADERS`` as
``(module_path, attr_name)`` tuples and only imported when the matching
extension is actually used (see ``_registry.get_loader``).

A handful of public names that the old directory-scan exposed at this
level (``load_markdown``, ``load_pdf``, ``load_bibtex``,
``load_yaml_as_an_optuna_dict``, ``load_study_rdb``, ``H5Explorer``,
``ZarrExplorer``, ``SQLite3``, ``DotDict``, …) remain reachable via
PEP 562 ``__getattr__`` — they resolve to the underlying submodule
attribute on first access so existing call sites
``from scitex_io._load_modules import load_markdown`` keep working
without triggering an eager fan-out.
"""

from __future__ import annotations

import importlib as _importlib

# Public name → (submodule_path, attr_in_submodule). Only names the
# old auto-scan would have surfaced (i.e. names that don't start with
# ``_`` in their defining module) are listed here.
_LAZY_NAMES: dict[str, tuple[str, str]] = {
    "DotDict": ("scitex_io._load_modules._pdf_utils", "DotDict"),
    "load_pdf": ("scitex_io._load_modules._pdf", "load_pdf"),
    "load_bibtex": ("scitex_io._load_modules._bibtex", "load_bibtex"),
    "SQLite3": ("scitex_io._load_modules._sqlite3", "SQLite3"),
    "load_yaml_as_an_optuna_dict": (
        "scitex_io._load_modules._optuna",
        "load_yaml_as_an_optuna_dict",
    ),
    "load_study_rdb": (
        "scitex_io._load_modules._optuna",
        "load_study_rdb",
    ),
    "load_markdown": (
        "scitex_io._load_modules._markdown",
        "load_markdown",
    ),
    "H5Explorer": ("scitex_io._load_modules._H5Explorer", "H5Explorer"),
    "explore_h5": ("scitex_io._load_modules._H5Explorer", "explore_h5"),
    "has_h5_key": ("scitex_io._load_modules._H5Explorer", "has_h5_key"),
    "ZarrExplorer": (
        "scitex_io._load_modules._ZarrExplorer",
        "ZarrExplorer",
    ),
    "explore_zarr": (
        "scitex_io._load_modules._ZarrExplorer",
        "explore_zarr",
    ),
    "has_zarr_key": (
        "scitex_io._load_modules._ZarrExplorer",
        "has_zarr_key",
    ),
}


def __getattr__(name: str):
    """Resolve a back-compat load-module attribute on first access."""
    spec = _LAZY_NAMES.get(name)
    if spec is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )
    module_path, attr_name = spec
    module = _importlib.import_module(module_path)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(_LAZY_NAMES) | set(globals()))


# EOF
