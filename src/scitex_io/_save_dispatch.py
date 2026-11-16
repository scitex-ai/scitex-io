#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save handler dispatch for scitex-io.

Resolves, preflights and executes the per-extension save handler. Split out
of ``_save.py`` so that file stays a focused ``save()`` orchestrator; the
names here are re-exported from ``_save`` so existing imports keep working.
"""

from __future__ import annotations

import os as _os
from types import FunctionType as _FunctionType

from scitex_logging import getLogger as _getLogger

from ._image_csv_handler import handle_image_with_csv
from ._path_modules._symlink import _symlink, _symlink_to
from ._registry import get_saver
from ._utils import getsize, readable_bytes

logger = _getLogger(__name__)

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif", ".svg", ".pdf"}


def _save(
    obj,
    spath,
    verbose=True,
    symlink_from_cwd=False,
    dry_run=False,
    no_csv=False,
    symlink_to=None,
    **kwargs,
):
    """Dispatch save to the appropriate handler based on file extension.

    Also used for sidecar writes (a figure's CSV export): the written path
    is noted on the enclosing public save's write capture so it receives
    its own post-save hook.
    """
    from ._observers._capture import note_written

    handler = _resolve_save_handler(spath)
    # The image wrapper historically returns before imports on a direct dry run.
    if handler is not handle_image_with_csv or not dry_run:
        _preflight_save_handler(handler, spath, kwargs)
    _execute_save_handler(
        handler,
        obj,
        spath,
        verbose=verbose,
        symlink_from_cwd=symlink_from_cwd,
        dry_run=dry_run,
        no_csv=no_csv,
        symlink_to=symlink_to,
        **kwargs,
    )
    if not dry_run:
        note_written(spath)


def _resolve_save_handler(spath):
    """Resolve the actual dispatcher callable without serializing or writing."""
    ext = _os.path.splitext(spath)[1].lower()

    # Special case: compound extension .pkl.gz
    if spath.endswith(".pkl.gz"):
        ext = ".pkl.gz"

    # Compound extensions contributed by optional providers (e.g.
    # figrecipe's .fig.zip / .plt.zip) — match the full suffix so they
    # dispatch on their own handler instead of the bare ".zip".
    from ._optional_providers import OPTIONAL_COMPOUND_EXTS

    _spath_lower = spath.lower()
    for _compound in OPTIONAL_COMPOUND_EXTS:
        if _spath_lower.endswith(_compound):
            ext = _compound
            break

    if ext in _IMAGE_EXTS:
        return handle_image_with_csv
    handler = get_saver(ext)
    if handler is None:
        raise ValueError(
            f"No save handler registered for '{ext}'.\n"
            f"scitex-io has a pluggable extension registry — register a saver "
            f"for this format, then retry. For example:\n\n"
            f"    from scitex_io import register_saver\n\n"
            f"    @register_saver('{ext}')\n"
            f"    def _saver(obj, path, **kwargs):\n"
            f"        # serialize obj however this format needs, e.g.\n"
            f"        #   obj.save(path)   # many objects self-serialize\n"
            f"        ...\n\n"
            f"    save(obj, path)   # now dispatches to your saver\n\n"
            f"Inspect built-ins via scitex_io.list_formats(); register_loader() "
            f"is the load-side twin. Direct form: "
            f"register_saver('{ext}', your_fn)."
        )
    return handler


def _preflight_save_handler(handler, spath, kwargs):
    """Check only the genuinely selected builtin; custom savers stay independent."""
    # A resolved registry callable keeps its real globals even if a caller
    # later removes the module-cache entry. Do not import unrelated builtins.
    namespace = handler.__globals__ if isinstance(handler, _FunctionType) else {}
    if namespace.get(
        "__name__"
    ) == __package__ + "._save_modules._hdf5" and handler is namespace.get(
        "_save_hdf5"
    ):
        namespace["_require_hdf5_save"]()
    if namespace.get(
        "__name__"
    ) == __package__ + "._save_modules._zarr" and handler is namespace.get(
        "_save_zarr"
    ):
        namespace["_require_zarr_save"](
            spath, kwargs.get("compressor", "zstd"), kwargs.get("store_type", "auto")
        )
    if handler is handle_image_with_csv:
        from ._image_csv_handler import _get_save_image

        _get_save_image()  # resolve imports only; never render as a readiness check


def _execute_save_handler(
    handler,
    /,
    obj,
    spath,
    verbose=True,
    symlink_from_cwd=False,
    dry_run=False,
    no_csv=False,
    symlink_to=None,
    **kwargs,
):
    """Execute the already-selected callable, retaining wrapper/output semantics."""
    if handler is handle_image_with_csv:
        handle_image_with_csv(
            obj,
            spath,
            no_csv=no_csv,
            symlink_from_cwd=symlink_from_cwd,
            symlink_to=symlink_to,
            dry_run=dry_run,
            _save_fn=_save,
            _symlink_fn=_symlink,
            _symlink_to_fn=_symlink_to,
            **kwargs,
        )
    else:
        handler(obj, spath, **kwargs)

    if verbose:
        if _os.path.exists(spath):
            file_size = readable_bytes(getsize(spath))
            try:
                rel_path = _os.path.relpath(spath, _os.getcwd())
            except ValueError:
                rel_path = spath
            logger.success(f"Saved to: ./{rel_path} ({file_size})")


# EOF
