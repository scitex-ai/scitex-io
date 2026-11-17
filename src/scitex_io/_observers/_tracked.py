#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make the public ``save_*`` convenience helpers fire the post-save hook.

``scitex_io.save`` notifies post-save observers (scitex-clew) for every
file it writes. The convenience helpers exported next to it —
``scitex_io.save_text``, ``save_image``, ``save_mp4``,
``save_listed_dfs_as_csv``, ``save_listed_scalars_as_csv`` and every
``scitex_io._save_modules.save_<fmt>`` name — used to resolve to the RAW
per-format handlers, which write the file and return without telling any
observer. A script under ``@stx.session`` that wrote ``REPORT.md`` with
``stx.io.save_text(...)`` therefore produced a file the provenance store
never recorded as an output (paper-scitex-clew E1, 2026-11-17: strace saw
the write, clew did not; capture recall 4/5).

:func:`tracked_save_helper` wraps a raw handler so a public call:

* writes exactly where the raw handler always wrote (the path is NOT
  caller-anchored like ``save()``: relative paths stay relative to the
  current working directory, absolute paths are used as-is);
* captures every file written (primary + same-stem sidecars) via the same
  :class:`~scitex_io._observers._capture.WriteCapture` that ``save()`` uses;
* fires the post-save hook once per written file with its realpath — for
  relative and absolute paths alike;
* honours ``track=`` and ``derived_from=`` exactly like ``save()``.

The raw handlers stay unwrapped inside ``save()``'s own dispatch (the
registry points at the submodule functions directly), so a ``save()`` call
still fires once per file. A wrapped helper invoked from inside an active
``save()`` that targets the same primary (e.g. registered as a custom
saver) defers to the outer capture instead of firing twice.
"""

from __future__ import annotations

import functools
import inspect
import os
from typing import Any, Callable

__all__ = ["tracked_save_helper"]


def _target_path(sig: inspect.Signature, args: tuple, kwargs: dict) -> str:
    """Return the destination path argument (the handler's 2nd parameter)."""
    bound = sig.bind_partial(*args, **kwargs)
    params = list(sig.parameters)
    if len(params) < 2 or params[1] not in bound.arguments:
        raise TypeError(
            "scitex_io save helper called without a destination path "
            f"(expected parameter {params[1] if len(params) > 1 else 'path'!r})"
        )
    return os.fspath(bound.arguments[params[1]])


def tracked_save_helper(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a raw ``(obj, path, ...)`` save handler so it notifies observers."""
    if getattr(fn, "__scitex_io_tracked__", False):
        return fn
    sig = inspect.signature(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        from scitex_io._derived_from import resolve_derived_from

        from . import fire_post_save_capture
        from ._capture import _active, capture_writes

        # Observer-only kwargs never reach the raw handler (it would raise
        # on them); a bad ``derived_from`` fails BEFORE anything is written.
        track = kwargs.pop("track", True)
        derived_from = resolve_derived_from(kwargs.pop("derived_from", None))

        target = os.path.abspath(_target_path(sig, args, kwargs))

        outer = _active.get()
        if outer is not None and os.path.realpath(outer.primary) == os.path.realpath(
            target
        ):
            # Already inside save() for this very file: it reports it.
            return fn(*args, **kwargs)

        with capture_writes(target) as capture:
            result = fn(*args, **kwargs)

        try:
            from scitex_io._loading._load_cache import invalidate

            invalidate(target)
        except Exception:  # pragma: no cover — cache eviction is best-effort
            pass

        hook_kwargs = {"track": track}
        if derived_from is not None:
            hook_kwargs["derived_from"] = derived_from
        fire_post_save_capture(capture, args[0] if args else None, hook_kwargs)
        return result

    wrapper.__scitex_io_tracked__ = True
    return wrapper


# EOF
