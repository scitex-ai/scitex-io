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


def _is_self_link(target, link_path):
    """True when a symlink at ``link_path`` -> ``target`` would point at itself.

    Compares the two paths lexically via ``abspath`` (NOT ``realpath`` /
    ``Path.resolve``): the link may already be a broken or self-looping
    symlink, and resolving it would follow that loop and raise. The
    reported corruption (neurovista, scitex 2.30.1) is exactly the case
    where the saved file IS the cwd-relative location, so ``target`` and
    ``link_path`` denote the same absolute path — that is what we refuse.
    """
    return _os.path.abspath(target) == _os.path.abspath(link_path)


def _symlink(spath, spath_cwd, symlink_from_cwd, verbose, spath_final=None):
    """Create a symbolic link from the current working directory.

    Uses ``spath_final`` (the path normalised through ``clean()``) as
    the link source when supplied; falls back to the raw ``spath`` for
    backward compatibility with callers that don't yet pass it.

    scitex-io#55 / neurovista 2026-06-27: when the save target already
    resolves under the cwd (the common case for
    ``save(obj, "./output/.../x.png", symlink_from_cwd=True)``), the link
    source and the link path are the SAME file, and ``ln -sfr`` collapses
    the relative target to the file's own basename — an ``x.png -> x.png``
    self-loop that overwrites the real artefact and crashes any reader
    doing ``Path.resolve()``. We refuse such a link (before any ``rm``)
    so the saved file survives untouched.
    """
    if symlink_from_cwd and (spath != spath_cwd):
        target = spath_final if spath_final is not None else spath
        if _is_self_link(target, spath_cwd):
            logger.warning(
                f"_symlink: refusing self-pointing link at {spath_cwd} "
                f"(target resolves to the link itself); keeping the real "
                f"file (scitex-io#55 / neurovista 2026-06-27)."
            )
            return
        _os.makedirs(_os.path.dirname(spath_cwd), exist_ok=True)
        sh(["rm", "-f", f"{spath_cwd}"], verbose=False)
        sh(["ln", "-sfr", f"{target}", f"{spath_cwd}"], verbose=False)
        if verbose:
            logger.success(f"(Symlinked to: {spath_cwd})")


def _symlink_to(spath_final, symlink_to, verbose):
    """Create a symbolic link at the specified path pointing to the saved file.

    Same self-loop guard as ``_symlink``: if ``symlink_to`` denotes the
    very file that was just saved, refuse the link (before any ``rm``) so
    the real artefact is not replaced by an ``x -> x`` self-loop.
    """
    if symlink_to:
        if isinstance(symlink_to, Path):
            symlink_to = str(symlink_to)
        symlink_to = clean(symlink_to)
        if _is_self_link(spath_final, symlink_to):
            logger.warning(
                f"_symlink_to: refusing self-pointing link at {symlink_to} "
                f"(target resolves to the link itself); keeping the real "
                f"file (scitex-io#55 / neurovista 2026-06-27)."
            )
            return
        _os.makedirs(_os.path.dirname(symlink_to), exist_ok=True)
        sh(["rm", "-f", f"{symlink_to}"], verbose=False)
        sh(["ln", "-sfr", f"{spath_final}", f"{symlink_to}"], verbose=False)
        if verbose:
            logger.success(f"(Symlinked to: {symlink_to})")


__all__ = ["sh", "_symlink", "_symlink_to", "_is_self_link"]

# EOF
