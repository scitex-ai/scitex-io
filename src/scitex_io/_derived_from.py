#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Per-output declared inputs for ``save(..., derived_from=[...])``.

An observer that records a run's inputs and outputs (scitex-clew) can only
say "this output came from the run that read these files". A writer that
KNOWS which inputs an output was computed from can declare it, so the
observer's minimal back-trace keeps those and drops the run's other inputs.

``derived_from`` accepts file paths and objects returned by
:func:`scitex_io.load`. An object is resolved to the file it was loaded
from through an identity registry filled by ``load()``:

* keyed by ``id(obj)`` and guarded by a weak reference, so an entry dies
  with its object and a recycled ``id`` can never resolve to a stale path;
* only weak-referenceable objects are registered (DataFrame, ndarray, most
  class instances). ``dict`` / ``list`` / ``str`` / ``int`` cannot be held
  weakly, and keying them by ``id`` alone could resolve to the wrong file
  after garbage collection, so they are never resolved -- pass the path;
* an object loaded from two different files is ambiguous and refused.

Nothing is ever inferred. ``save`` declares inputs ONLY when the caller
passes ``derived_from``; without it the payload carries no declaration and
the observer keeps every input of the run. The obvious inference -- "the
saved object is itself a loaded object, so it derives from that file" --
is deliberately NOT made: ``df = load(a); df["y"] = load(b)["y"];
save(df, out)`` mutates the object in place, and declaring ``[a]`` would
silently drop ``b`` from the back-trace. A missing edge is worse than an
undeclared one, so the declaration stays explicit.
"""

from __future__ import annotations

import os
import weakref
from typing import Any, Dict, List, Optional, Tuple

# id(obj) -> (weakref to obj, frozenset of realpaths it was loaded from)
_LOADED: Dict[int, Tuple["weakref.ref", frozenset]] = {}


def _forget(key: int, ref: "weakref.ref") -> None:
    entry = _LOADED.get(key)
    if entry is not None and entry[0] is ref:
        del _LOADED[key]


def register_loaded(obj: Any, realpath: str) -> bool:
    """Remember that ``obj`` was returned by loading ``realpath``.

    Returns True when ``obj`` is now resolvable, False when it cannot be
    held weakly (and therefore is never resolved).
    """
    key = id(obj)
    entry = _LOADED.get(key)
    if entry is not None and entry[0]() is obj:
        _LOADED[key] = (entry[0], entry[1] | {realpath})
        return True
    try:
        ref = weakref.ref(obj, lambda r, k=key: _forget(k, r))
    except TypeError:
        return False
    _LOADED[key] = (ref, frozenset({realpath}))
    return True


def loaded_from(obj: Any) -> Optional[frozenset]:
    """Realpaths ``obj`` was loaded from, or None if it is not a loaded object."""
    entry = _LOADED.get(id(obj))
    if entry is None or entry[0]() is not obj:
        return None
    return entry[1]


def _resolve_one(item: Any) -> str:
    if isinstance(item, (str, os.PathLike)):
        real = os.path.realpath(os.path.abspath(os.fspath(item)))
        if not os.path.exists(real):
            raise FileNotFoundError(
                f"derived_from names a file that does not exist: {item!r} "
                f"(resolved to {real})"
            )
        return real
    sources = loaded_from(item)
    if sources is None:
        raise TypeError(
            f"derived_from item of type {type(item).__name__} is not an object "
            "returned by scitex_io.load (or cannot be weakly referenced, e.g. "
            "dict/list/str/int), so its source file is unknown. Pass the file "
            "path instead."
        )
    if len(sources) != 1:
        raise ValueError(
            f"derived_from item of type {type(item).__name__} was loaded from "
            f"several files {sorted(sources)}; pass the intended path instead."
        )
    return next(iter(sources))


def resolve_derived_from(derived_from: Any) -> Optional[List[str]]:
    """Normalise a ``derived_from`` declaration to existing realpaths.

    ``None`` stays ``None`` (undeclared). A single path is accepted as a
    one-element list. An empty list is a valid declaration ("derived from
    no file"). Raises on anything that cannot be resolved exactly.
    """
    if derived_from is None:
        return None
    if isinstance(derived_from, (str, os.PathLike)):
        items = [derived_from]
    elif isinstance(derived_from, (list, tuple)):
        items = list(derived_from)
    else:
        raise TypeError(
            "derived_from must be a path or a list/tuple of paths and loaded "
            f"objects, got {type(derived_from).__name__}"
        )
    resolved: List[str] = []
    for item in items:
        real = _resolve_one(item)
        if real not in resolved:
            resolved.append(real)
    return resolved


__all__ = ["loaded_from", "register_loaded", "resolve_derived_from"]

# EOF
