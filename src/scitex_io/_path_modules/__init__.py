#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Path / filesystem helpers for scitex-io.

Topical home for the small, dependency-light filesystem utilities that
support ``save()`` and path resolution:

- ``_path`` — path discovery / manipulation (``split_fpath``, ``touch``,
  ``find``, ``find_latest``, ``find_the_git_root_dir``).
- ``_symlink`` — shell + symbolic-link helpers (``sh``, ``_symlink``,
  ``_symlink_to``) used by ``save(..., symlink_from_cwd=...)``.
- ``_mv_to_tmp`` — move-aside helper for the listed-CSV savers.

Grouped here (PS-108b) to keep ``src/scitex_io/`` navigable. The public
attribute surface is unchanged: ``scitex_io.path`` / ``scitex_io.mv_to_tmp``
still resolve through the lazy map in ``scitex_io/__init__.py`` exactly as
before; internal callers import the concrete submodules directly.
"""

from __future__ import annotations

from ._mv_to_tmp import _mv_to_tmp
from ._path import (
    find,
    find_latest,
    find_the_git_root_dir,
    split_fpath,
    touch,
)
from ._symlink import _symlink, _symlink_to, sh

__all__ = [
    "find",
    "find_latest",
    "find_the_git_root_dir",
    "split_fpath",
    "touch",
    "sh",
    "_symlink",
    "_symlink_to",
    "_mv_to_tmp",
]
