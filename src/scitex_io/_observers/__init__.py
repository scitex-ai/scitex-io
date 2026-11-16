#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Neutral post-save / post-load hook registry for scitex-io.

Public extension API. Observer packages (scitex-clew, future
notification or audit observers) register callbacks here on their own
import; scitex-io itself never names any observer.

Per SOC.md R6: producer packages don't know observer packages. The
arrow runs observer → producer. scitex-io owns this registry; observers
self-register.

Provenance contract
-------------------
* A post-save hook fires once for EVERY file a save writes — the primary
  file and each sidecar (figure CSV/YAML/legend exports, recipe files) —
  with ``path`` = the file's realpath (what must be hashed). ``kwargs``
  carries the caller's save kwargs plus ``track`` and a ``provenance``
  dict::

      {"role": "primary" | "sidecar",
       "realpath": "/abs/real/file",        # == str(path)
       "requested": "/abs/path/as/resolved/by/save",
       "primary": "/abs/real/primary",      # sidecars point at their parent
       "symlinks": ["/abs/link", ...],      # links created to this file
       "in_scope": bool, "scope": name|None}

  Sidecar hooks receive ``obj=None`` (the object belongs to the primary).
* A post-load hook fires once per loaded file, including each file of a
  glob load, with ``path`` = realpath. A hook that accepts a third
  positional parameter also receives ``info``:
  ``{"requested", "realpath", "symlink", "glob", "in_scope", "scope"}``.
* A hook that raises NEVER fails silently: the failure is counted in
  :func:`observer_failures` and WARNed once per kind (with the exception);
  ``SCITEX_IO_STRICT_PROVENANCE=1`` raises :class:`ProvenanceError` instead.

Usage from an observer
----------------------

>>> from scitex_io import register_post_save_hook
>>> def on_save(path, obj, kwargs):
...     ...
>>> register_post_save_hook(on_save)
"""

from __future__ import annotations

import inspect
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import scitex_logging as slogging

from ._failures import (
    STRICT_ENV,
    ProvenanceError,
    ProvenanceScope,
    current_scope,
    note_unscoped,
    observer_failures,
    provenance_scope,
    report_failure,
    reset_observer_failures,
    strict_provenance,
)

logger = slogging.getLogger(__name__)


PostSaveHook = Callable[[Path, Any, dict], None]
"""Signature: ``(saved_path, obj, kwargs) -> None``."""

PostLoadHook = Callable[..., None]
"""Signature: ``(loaded_path, result)`` or ``(loaded_path, result, info)``."""


_post_save_hooks: List[PostSaveHook] = []
_post_load_hooks: List[PostLoadHook] = []
# Keyed by the hook object itself (not id(): ids of collected callables
# are reused, which would hand a cached arity to an unrelated hook).
_accepts_info_cache: Dict[Callable, bool] = {}


def register_post_save_hook(fn: PostSaveHook) -> None:
    """Register a function to run after every file a ``scitex_io.save`` writes.

    Hooks fire in registration order. A raising hook does not break the
    host's I/O, but it is never silent: see :func:`observer_failures`.
    """
    _post_save_hooks.append(fn)


def register_post_load_hook(fn: PostLoadHook) -> None:
    """Register a function to run after every file ``scitex_io.load`` reads."""
    _post_load_hooks.append(fn)


def _arity_accepts_info(fn: Callable) -> bool:
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError):
        return False
    positional = [
        p for p in params if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    var = any(p.kind == p.VAR_POSITIONAL for p in params)
    return var or len(positional) >= 3


def _accepts_info(fn: Callable) -> bool:
    """True if a post-load hook takes the optional third ``info`` argument."""
    try:
        cached = _accepts_info_cache.get(fn)
    except TypeError:  # unhashable callable object: no caching
        return _arity_accepts_info(fn)
    if cached is None:
        cached = _accepts_info_cache[fn] = _arity_accepts_info(fn)
    return cached


def _scope_fields() -> Dict[str, Any]:
    scope = current_scope()
    return {"in_scope": scope is not None, "scope": scope.name if scope else None}


def fire_post_save(path: Path, obj: Any, kwargs: dict) -> None:
    """Internal: invoke registered post-save hooks for ONE file.

    Never raises, except in strict mode (:class:`ProvenanceError`).
    """
    from scitex_io import _ensure_observers_activated

    _ensure_observers_activated()
    # Diagnosability (auto-provenance incident, 2026-07-04): log the FIRING
    # instance's fingerprint so a single DEBUG smoke pinpoints a dead hook.
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "fire_post_save: %d hook(s) for %s; _post_save_hooks id=%d module=%s",
            len(_post_save_hooks),
            path,
            id(_post_save_hooks),
            __file__,
        )
    for fn in list(_post_save_hooks):
        try:
            fn(path, obj, kwargs)
        except Exception as e:  # noqa: BLE001 — counted + warned, not swallowed
            report_failure("post_save", fn, path, e)


def fire_post_save_capture(capture, obj: Any, kwargs: dict) -> List[Path]:
    """Internal: fire post-save hooks for every file ``capture`` saw written.

    Returns the realpaths reported (primary first).
    """
    from scitex_io import _ensure_observers_activated

    _ensure_observers_activated()
    primary_real = os.path.realpath(capture.primary)
    if not os.path.exists(primary_real):
        report_failure(
            "missing_output",
            None,
            capture.primary,
            FileNotFoundError(f"save() returned but {capture.primary} does not exist"),
        )
        return []
    sidecars = capture.sidecars()
    if capture.scan_error is not None:
        # Sidecars may have been written but cannot be enumerated.
        report_failure("sidecar_scan", None, capture.parent, capture.scan_error)
    scope = _scope_fields()
    if _post_save_hooks and not scope["in_scope"]:
        note_unscoped("save", primary_real)
    reported: List[Path] = []
    for real, role in [(primary_real, "primary")] + [(s, "sidecar") for s in sidecars]:
        payload = {
            **kwargs,
            "provenance": {
                "role": role,
                "realpath": real,
                "requested": capture.primary if role == "primary" else real,
                "primary": primary_real,
                "symlinks": capture.symlinks_to(real),
                **scope,
            },
        }
        fire_post_save(Path(real), obj if role == "primary" else None, payload)
        reported.append(Path(real))
    capture.mark_reported({str(p) for p in reported})
    return reported


def fire_post_load(path: Path, result: Any, info: Optional[dict] = None) -> None:
    """Internal: invoke registered post-load hooks for ONE file.

    ``path`` is passed to hooks as its realpath. Never raises, except in
    strict mode (:class:`ProvenanceError`).
    """
    from scitex_io import _ensure_observers_activated

    _ensure_observers_activated()
    requested = str(path)
    real = os.path.realpath(requested)
    scope = _scope_fields()
    full_info = {
        "requested": requested,
        "realpath": real,
        "symlink": os.path.islink(requested),
        "glob": None,
        **scope,
    }
    if info:
        full_info.update(info)
    if _post_load_hooks and not scope["in_scope"]:
        note_unscoped("load", real)
    real_path = Path(real)
    for fn in list(_post_load_hooks):
        try:
            if _accepts_info(fn):
                fn(real_path, result, dict(full_info))
            else:
                fn(real_path, result)
        except Exception as e:  # noqa: BLE001 — counted + warned, not swallowed
            report_failure("post_load", fn, real_path, e)


__all__ = [
    "PostSaveHook",
    "PostLoadHook",
    "ProvenanceError",
    "ProvenanceScope",
    "STRICT_ENV",
    "register_post_save_hook",
    "register_post_load_hook",
    "fire_post_save",
    "fire_post_save_capture",
    "fire_post_load",
    "observer_failures",
    "reset_observer_failures",
    "provenance_scope",
    "current_scope",
    "strict_provenance",
]
