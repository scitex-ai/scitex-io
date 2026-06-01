#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Format handler registry for scitex-io.

Two-tier registry: built-in handlers (lower priority) and user-registered
handlers (higher priority). Users and upstream packages (e.g., scitex with
.pltz/.figz/.statsz) register custom handlers via the same API.

Per-extension lazy resolution
-----------------------------
Built-in handlers may be registered as a ``(module_path, attr_name)`` tuple
instead of an already-imported callable. The first ``get_saver`` /
``get_loader`` lookup for that extension calls
:func:`importlib.import_module` on the named module, fetches the attribute,
and memoises the resolved callable in place — so subsequent lookups are an
ordinary dict get. A failed lazy import emits an ``ImportWarning`` (once
per extension) and the entry is replaced with ``None`` so we don't retry on
every call.

This keeps ``import scitex_io`` cheap: importing a JSON-only save never
pulls PIL, pymupdf, pyarrow, h5py, scipy, plotly, etc. Each format module
is loaded only when its extension is actually used.

Example
-------
>>> from scitex_io import register_saver, register_loader, save, load
>>>
>>> @register_saver(".custom")
... def save_custom(obj, path, **kw):
...     with open(path, "w") as f:
...         f.write(str(obj))
>>>
>>> @register_loader(".custom")
... def load_custom(path, **kw):
...     with open(path) as f:
...         return f.read()
>>>
>>> save("hello", "/tmp/test.custom")
>>> load("/tmp/test.custom")
'hello'
"""

from __future__ import annotations

import importlib as _importlib
import warnings as _warnings
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Entries in the builtin registries may be either an already-resolved
# callable or a ``(module_path, attr_name)`` tuple that the registry
# resolves on first lookup (and memoises in place).
_LazySpec = Tuple[str, str]
_BuiltinEntry = Union[Callable, _LazySpec, None]

# Two-tier registries
_builtin_savers: Dict[str, _BuiltinEntry] = {}
_builtin_loaders: Dict[str, _BuiltinEntry] = {}
_user_savers: Dict[str, Callable] = {}
_user_loaders: Dict[str, Callable] = {}


def _normalize_ext(ext: str) -> str:
    """Normalize extension to include leading dot."""
    ext = ext.strip()
    if ext and not ext.startswith("."):
        ext = "." + ext
    return ext.lower()


def _is_lazy_spec(entry: Any) -> bool:
    """Return True when ``entry`` is a ``(module_path, attr_name)`` lazy spec."""
    return (
        isinstance(entry, tuple)
        and len(entry) == 2
        and isinstance(entry[0], str)
        and isinstance(entry[1], str)
    )


def _resolve_lazy(
    registry: Dict[str, _BuiltinEntry],
    ext: str,
    kind: str,
) -> Optional[Callable]:
    """Resolve a lazy registry entry and memoise the result.

    On import failure the entry is replaced with ``None`` (so we don't
    re-try every call) and an ``ImportWarning`` is emitted once.
    """
    entry = registry.get(ext)
    if entry is None:
        return None
    if not _is_lazy_spec(entry):
        return entry  # already resolved
    module_path, attr_name = entry  # type: ignore[misc]
    try:
        module = _importlib.import_module(module_path)
        fn = getattr(module, attr_name, None)
        if fn is None:
            raise ImportError(
                f"module {module_path!r} has no attribute {attr_name!r}"
            )
    except Exception as exc:  # ImportError or missing attribute
        registry[ext] = None
        _warnings.warn(
            f"scitex_io: {kind} for '{ext}' not registered "
            f"(missing optional dependency: {exc})",
            ImportWarning,
            stacklevel=3,
        )
        return None
    registry[ext] = fn  # memoise the resolved callable
    return fn


def _register_builtin_lazy(
    registry: Dict[str, _BuiltinEntry],
    ext: str,
    module_path: str,
    attr_name: str,
) -> None:
    """Register a builtin handler as a lazy ``(module_path, attr_name)`` spec."""
    registry[_normalize_ext(ext)] = (module_path, attr_name)


def register_saver(ext: str, fn: Callable = None, *, builtin: bool = False):
    """Register a save handler for a file extension.

    Can be used as a decorator or called directly::

        @register_saver(".json")
        def my_json_saver(obj, path, **kwargs): ...

        register_saver(".json", my_json_saver)

    Parameters
    ----------
    ext : str
        File extension (e.g., ".json", "json" — dot is optional).
    fn : Callable, optional
        Handler function ``(obj, path, **kwargs) -> None``.
        If None, returns a decorator.
    builtin : bool
        If True, registers as built-in (lower priority).
        User registrations always override built-ins.
    """
    ext = _normalize_ext(ext)
    registry = _builtin_savers if builtin else _user_savers

    if fn is not None:
        registry[ext] = fn
        return fn

    def decorator(func):
        registry[ext] = func
        return func

    return decorator


def register_loader(ext: str, fn: Callable = None, *, builtin: bool = False):
    """Register a load handler for a file extension.

    Same API as :func:`register_saver`.

    Parameters
    ----------
    ext : str
        File extension (e.g., ".json", "json" — dot is optional).
    fn : Callable, optional
        Handler function ``(path, **kwargs) -> Any``.
    builtin : bool
        If True, registers as built-in (lower priority).
    """
    ext = _normalize_ext(ext)
    registry = _builtin_loaders if builtin else _user_loaders

    if fn is not None:
        registry[ext] = fn
        return fn

    def decorator(func):
        registry[ext] = func
        return func

    return decorator


def get_saver(ext: str) -> Optional[Callable]:
    """Look up a save handler. User overrides take priority.

    Lazy builtin specs (``(module_path, attr_name)`` tuples) are resolved
    on first access and memoised in place.
    """
    ext = _normalize_ext(ext)
    fn = _user_savers.get(ext)
    if fn is not None:
        return fn
    return _resolve_lazy(_builtin_savers, ext, "saver")


def get_loader(ext: str) -> Optional[Callable]:
    """Look up a load handler. User overrides take priority.

    Lazy builtin specs (``(module_path, attr_name)`` tuples) are resolved
    on first access and memoised in place.
    """
    ext = _normalize_ext(ext)
    fn = _user_loaders.get(ext)
    if fn is not None:
        return fn
    return _resolve_lazy(_builtin_loaders, ext, "loader")


def list_formats() -> Dict[str, Dict[str, List[str]]]:
    """List all registered formats.

    Returns
    -------
    dict
        A dict with keys ``"save"`` and ``"load"``, each containing
        ``"builtin"`` and ``"user"`` format lists.

    Notes
    -----
    Builtin entries are listed regardless of whether they have been
    lazy-resolved yet — registration is what counts.
    """
    return {
        "save": {
            "builtin": sorted(_builtin_savers.keys()),
            "user": sorted(_user_savers.keys()),
        },
        "load": {
            "builtin": sorted(_builtin_loaders.keys()),
            "user": sorted(_user_loaders.keys()),
        },
    }


def unregister_saver(ext: str) -> bool:
    """Remove a user-registered saver. Returns True if found."""
    ext = _normalize_ext(ext)
    return _user_savers.pop(ext, None) is not None


def unregister_loader(ext: str) -> bool:
    """Remove a user-registered loader. Returns True if found."""
    ext = _normalize_ext(ext)
    return _user_loaders.pop(ext, None) is not None
