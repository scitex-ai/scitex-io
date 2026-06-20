#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shell + symbolic-link helpers for scitex-io save().

Extracted from ``_save.py`` (which had grown past the module line limit) so
that file stays a focused save orchestrator. ``sh`` is the small subprocess
wrapper used to run ``ln``/``rm``; ``_symlink`` / ``_symlink_to`` create the
convenience links that ``save(..., symlink_from_cwd=...)`` / ``symlink_to=...``
request. ``_save`` re-imports all three, so existing references keep working.

No import cycle: this module imports only ``.._utils`` and ``scitex_logging``,
never ``.._save``.
"""

import os as _os
import subprocess
from pathlib import Path

from scitex_logging import getLogger as _getLogger

from .._utils import clean

logger = _getLogger(__name__)


def sh(command, *args, **kwargs):
    """Run ``command`` (a list of argv tokens) and return success boolean.

    Bug fix: previously this used ``shell=True`` with a list, which on
    POSIX runs only ``command[0]`` and silently discards the rest —
    ``sh(["ln", "-sfr", src, dst])`` was effectively just ``sh -c ln``.
    Switch to ``shell=False`` so the argv list is passed as-is.
    """
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0


def _symlink(spath, spath_cwd, symlink_from_cwd, verbose, spath_final=None):
    """Create a symbolic link from the current working directory.

    Uses ``spath_final`` (the path normalised through ``clean()``) as
    the link source when supplied; falls back to the raw ``spath`` for
    backward compatibility with callers that don't yet pass it.

    scitex-io#55: when ``spath`` contained ``./`` segments (the common
    case for ``save(obj, "./x.csv", symlink_from_cwd=True)``), the
    ``ln -sfr`` relative-target computation could collapse to the same
    basename in the same dir, producing a ``./x.csv -> x.csv``
    self-loop. We now:

    1. Prefer the cleaned ``spath_final`` as the link source.
    2. Compute the relative target ourselves and bail out (logging) if
       it would equal ``basename(spath_cwd)`` in ``dirname(spath_cwd)``.
    """
    if symlink_from_cwd and (spath != spath_cwd):
        target = spath_final if spath_final is not None else spath
        _os.makedirs(_os.path.dirname(spath_cwd), exist_ok=True)
        rel_target = _os.path.relpath(target, _os.path.dirname(spath_cwd))
        if rel_target == _os.path.basename(spath_cwd):
            # Defensive guard — refuse to create a self-loop. This
            # should be unreachable now that spath_cwd uses normpath
            # (not clean→resolve) upstream, but is kept as a belt-and-
            # suspenders for any caller that passes already-resolved
            # paths.
            logger.error(
                f"_symlink would self-loop {spath_cwd} -> {rel_target}; "
                "skipping link creation (scitex-io#55)."
            )
            return
        sh(["rm", "-f", f"{spath_cwd}"], verbose=False)
        sh(["ln", "-sfr", f"{target}", f"{spath_cwd}"], verbose=False)
        if verbose:
            logger.success(f"(Symlinked to: {spath_cwd})")


def _symlink_to(spath_final, symlink_to, verbose):
    """Create a symbolic link at the specified path pointing to the saved file."""
    if symlink_to:
        if isinstance(symlink_to, Path):
            symlink_to = str(symlink_to)
        symlink_to = clean(symlink_to)
        _os.makedirs(_os.path.dirname(symlink_to), exist_ok=True)
        sh(["rm", "-f", f"{symlink_to}"], verbose=False)
        sh(["ln", "-sfr", f"{spath_final}", f"{symlink_to}"], verbose=False)
        if verbose:
            logger.success(f"(Symlinked to: {symlink_to})")


__all__ = ["sh", "_symlink", "_symlink_to"]

# EOF
