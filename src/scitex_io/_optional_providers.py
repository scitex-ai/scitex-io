#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Optional format providers from sibling scitex ecosystem packages.

scitex-io stays useful on its own, but when a companion package is
installed it can contribute extra formats through the same registry the
built-in handlers use. This keeps the synergy *opt-in*: ``import
scitex_io`` never hard-depends on the companion, and a missing companion
degrades to the normal "no handler registered" error rather than an
``ImportError`` at import time.

Each provider is gated by ``scitex_dev.try_import_optional`` so a missing
package is a no-op (the companion's formats simply stay unregistered).

Currently wired:

- **figrecipe** (``[figrecipe]`` extra) → ``.fig.zip`` / ``.plt.zip``
  multi-panel and single-plot figure bundles. ``scitex_io.save(fig,
  "panel.plt.zip")`` / ``scitex_io.load("panel.plt.zip")`` round-trip a
  reproducible figure recipe + data.
- **scitex_stats** (``[stats]`` extra) → ``.stats.zip`` statistics
  bundles (spec + supplementary data + optional markdown report).
  ``scitex_io.save(stats_dict, "results.stats.zip")`` /
  ``scitex_io.load("results.stats.zip")``.
"""

from __future__ import annotations

from scitex_dev import try_import_optional

from ._registry import register_loader, register_saver

# Compound extensions contributed by optional providers. ``_save`` /
# ``_load`` consult this so a path like ``foo.plt.zip`` dispatches on the
# full ``.plt.zip`` key rather than the bare ``.zip`` ``splitext`` yields.
OPTIONAL_COMPOUND_EXTS: tuple[str, ...] = (".fig.zip", ".plt.zip", ".stats.zip")


def _import_figrecipe():
    """Return the figrecipe module, or ``None`` when it is not installed."""
    return try_import_optional("figrecipe", extra="figrecipe", pkg="scitex-io")


def _register_figrecipe(importer=_import_figrecipe) -> bool:
    """Register figrecipe bundle formats if figrecipe is installed.

    Parameters
    ----------
    importer : callable, optional
        Returns the figrecipe module or ``None``. Injectable so callers
        can substitute a real-but-absent importer in tests without
        patching production internals. Defaults to the gated
        ``try_import_optional`` import.

    Returns
    -------
    bool
        ``True`` when handlers were registered, ``False`` when figrecipe
        is absent (graceful no-op).
    """
    figrecipe = importer()
    if figrecipe is None:
        return False

    def _save_fig_bundle(obj, path, **kwargs):
        # figrecipe.save_bundle handles both .fig.zip (multi-panel) and
        # .plt.zip (single-plot) by inspecting the figure/path.
        verbose = kwargs.pop("verbose", False)
        return figrecipe.save_bundle(obj, path, verbose=verbose, **kwargs)

    def _load_fig_bundle(path, **kwargs):
        # figrecipe.load reproduces a Figure/axes from a bundle or recipe.
        return figrecipe.load(path, **kwargs)

    for _ext in (".fig.zip", ".plt.zip"):
        register_saver(_ext, _save_fig_bundle, builtin=True)
        register_loader(_ext, _load_fig_bundle, builtin=True)

    return True


def _import_scitex_stats():
    """Return the scitex_stats module, or ``None`` when it is not installed."""
    return try_import_optional("scitex_stats", extra="stats", pkg="scitex-io")


def _register_scitex_stats(importer=_import_scitex_stats) -> bool:
    """Register scitex_stats ``.stats.zip`` bundles if scitex_stats is installed.

    Parameters
    ----------
    importer : callable, optional
        Returns the scitex_stats module or ``None``. Injectable so callers
        can substitute a real-but-absent importer in tests without
        patching production internals.

    Returns
    -------
    bool
        ``True`` when handlers were registered, ``False`` when scitex_stats
        is absent (graceful no-op).
    """
    scitex_stats = importer()
    if scitex_stats is None:
        return False

    # ``scitex_stats.__init__`` does not auto-import the ``io`` subpackage;
    # bind the bundle entry points eagerly here so the registry callbacks
    # never have to do attribute walks on every call.
    from scitex_stats.io import (  # type: ignore[import-not-found]
        load_stats_bundle,
        save_stats_bundle,
    )

    def _save_stats_bundle(obj, path, **kwargs):
        # scitex_stats.io.save_stats_bundle takes (data: dict, path).
        return save_stats_bundle(obj, path)

    def _load_stats_bundle(path, **kwargs):
        return load_stats_bundle(path)

    register_saver(".stats.zip", _save_stats_bundle, builtin=True)
    register_loader(".stats.zip", _load_stats_bundle, builtin=True)

    return True


def _import_scitex_db():
    """Return the scitex_db module, or ``None`` when it is not installed."""
    return try_import_optional("scitex_db", extra="db", pkg="scitex-io")


def _register_scitex_db(importer=_import_scitex_db) -> bool:
    """Register the ``.db`` loader if scitex-db is installed.

    DB loading is delegated to scitex-db's ``SQLite3`` wrapper — the
    full class with mixins (``get_rows``, ``load_array``,
    ``save_array``, etc.), not the primitive sqlite3.Connection
    fallback that used to live in ``_load_modules/_sqlite3.py``. The
    silent-fallback antipattern (returning a raw Connection wrapped in
    a stub) was removed during the scitex-db standardization; if
    scitex-db is NOT installed, ``stx.io.load("foo.db")`` raises a
    clear ``ValueError("No load handler registered for '.db'. …")``
    via the standard registry error path, which prompts users to
    ``pip install scitex-io[db]``.

    Parameters
    ----------
    importer : callable, optional
        Returns the scitex_db module or ``None``. Injectable so callers
        can substitute a real-but-absent importer in tests without
        patching production internals.

    Returns
    -------
    bool
        ``True`` when the ``.db`` handler was registered, ``False``
        when scitex-db is absent (graceful no-op — the registry stays
        empty for ``.db`` so the standard "no handler" error fires).
    """
    scitex_db = importer()
    if scitex_db is None:
        return False

    def _load_db(path, **kwargs):
        # scitex_db.SQLite3 forwards **kwargs into sqlite3.connect via
        # the wrapper — e.g. mode='ro' / timeout=5.0 from a future
        # scitex-db release. Callers write
        # ``stx.io.load("foo.db", mode='ro')`` and the kwargs flow
        # through unchanged.
        return scitex_db.SQLite3(path, **kwargs)

    register_loader(".db", _load_db, builtin=True)
    return True


# Provider registry: name → callable returning bool(registered?). Add new
# ecosystem providers here; each must be independently gated.
_PROVIDERS = (
    _register_figrecipe,
    _register_scitex_stats,
    _register_scitex_db,
)


def register_optional_providers() -> None:
    """Run every optional provider once. Idempotent and failure-tolerant."""
    for _provider in _PROVIDERS:
        try:
            _provider()
        except Exception:
            # A misbehaving optional provider must never break import or
            # core I/O — skip it silently, like a missing dependency.
            pass
