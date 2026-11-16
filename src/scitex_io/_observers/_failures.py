#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Loud accounting of provenance loss in the observer fan-out.

Every place where scitex-io would otherwise lose provenance silently — an
observer hook that raises, a sidecar scan that fails, a save whose output
is missing afterwards — goes through :func:`report_failure`:

* the failure is COUNTED (per process and per active provenance scope),
* the first failure of each kind is logged at WARNING with the exception
  (subsequent identical ones at DEBUG, but still counted),
* with ``SCITEX_IO_STRICT_PROVENANCE=1`` a :class:`ProvenanceError` is
  raised instead of warning.

The counters are public through :func:`observer_failures` so that
``@stx.session`` / scitex-clew can write them into run metadata: a run
whose provenance record is incomplete must say so.
"""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, List, Optional

import scitex_logging as slogging

logger = slogging.getLogger(__name__)

STRICT_ENV = "SCITEX_IO_STRICT_PROVENANCE"

_TRUTHY = {"1", "true", "yes", "on"}


class ProvenanceError(RuntimeError):
    """Raised in strict mode when provenance for an I/O event was lost."""


def strict_provenance() -> bool:
    """True when ``SCITEX_IO_STRICT_PROVENANCE`` is set to a truthy value."""
    return os.environ.get(STRICT_ENV, "").strip().lower() in _TRUTHY


class _Counter:
    """Failure tally: totals, per-kind counts and one record per signature."""

    def __init__(self) -> None:
        self.total = 0
        self.by_kind: Dict[str, int] = {}
        self.events: Dict[tuple, Dict[str, Any]] = {}
        self.unscoped_saves = 0
        self.unscoped_loads = 0

    def add(self, key: tuple, kind: str, hook: str, path: str, exc: BaseException):
        self.total += 1
        self.by_kind[kind] = self.by_kind.get(kind, 0) + 1
        event = self.events.get(key)
        if event is None:
            self.events[key] = {
                "kind": kind,
                "hook": hook,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "first_path": path,
                "count": 1,
            }
        else:
            event["count"] += 1

    def snapshot(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "by_kind": dict(self.by_kind),
            "events": [dict(e) for e in self.events.values()],
            "unscoped_saves": self.unscoped_saves,
            "unscoped_loads": self.unscoped_loads,
        }


_lock = threading.RLock()
_process = _Counter()
_warned: set = set()
_scopes: List["ProvenanceScope"] = []
_unscoped_noted = False


class ProvenanceScope:
    """A named recording window (e.g. one ``@stx.session`` run).

    Opened via :func:`scitex_io.provenance_scope`. While a scope is active,
    hook payloads carry ``in_scope=True`` and failures are tallied on the
    scope as well as on the process.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._counter = _Counter()

    def failures(self) -> Dict[str, Any]:
        """Failure tally for this scope only (same shape as the process one)."""
        with _lock:
            snap = self._counter.snapshot()
        snap["scope"] = self.name
        snap["strict"] = strict_provenance()
        return snap

    def __enter__(self) -> "ProvenanceScope":
        with _lock:
            _scopes.append(self)
        return self

    def __exit__(self, *exc) -> None:
        with _lock:
            if self in _scopes:
                _scopes.remove(self)


def provenance_scope(name: str) -> ProvenanceScope:
    """Context manager marking a recording window (a session/run).

    >>> with scitex_io.provenance_scope("2026Y-11M-16D-run") as scope:
    ...     scitex_io.save(df, "/abs/out.csv")
    >>> scope.failures()["total"]
    0
    """
    return ProvenanceScope(str(name))


def current_scope() -> Optional[ProvenanceScope]:
    """Innermost active :class:`ProvenanceScope`, or ``None``."""
    with _lock:
        return _scopes[-1] if _scopes else None


def observer_failures() -> Dict[str, Any]:
    """Process-wide tally of lost provenance events.

    Returns a dict: ``total`` (int), ``by_kind`` ({kind: count}; kinds are
    ``post_save``, ``post_load``, ``sidecar_scan``, ``missing_output``),
    ``events`` (one record per distinct ``(kind, hook, error_type)`` with
    ``count``, ``error`` and ``first_path``), ``unscoped_saves`` /
    ``unscoped_loads`` (I/O events that observers saw while no
    :func:`provenance_scope` was active), ``scope`` (innermost active
    scope's name or ``None``) and ``strict`` (bool).
    """
    with _lock:
        snap = _process.snapshot()
        scope = _scopes[-1] if _scopes else None
    snap["scope"] = scope.name if scope is not None else None
    snap["strict"] = strict_provenance()
    return snap


def reset_observer_failures() -> None:
    """Zero the process-wide tally and re-arm the once-per-kind warnings."""
    global _process, _unscoped_noted
    with _lock:
        _process = _Counter()
        _warned.clear()
        _unscoped_noted = False


def _hook_name(hook: Any) -> str:
    if hook is None:
        return "scitex_io"
    module = getattr(hook, "__module__", None) or "?"
    qual = getattr(hook, "__qualname__", None) or repr(hook)
    return f"{module}.{qual}"


def report_failure(kind: str, hook: Any, path: Any, exc: BaseException) -> None:
    """Count a provenance loss; WARN once per kind, or raise in strict mode."""
    name = _hook_name(hook)
    key = (kind, name, type(exc).__name__)
    spath = str(path)
    with _lock:
        _process.add(key, kind, name, spath, exc)
        for scope in _scopes:
            scope._counter.add(key, kind, name, spath, exc)
        first = key not in _warned
        _warned.add(key)
    msg = (
        f"scitex_io provenance LOST [{kind}] for {spath}: "
        f"{name} raised {type(exc).__name__}: {exc}"
    )
    if strict_provenance():
        raise ProvenanceError(msg) from exc
    if first:
        logger.warning(
            "%s\n  Further failures of this kind are counted (not re-warned); "
            "inspect scitex_io.observer_failures(). Set %s=1 to raise instead.",
            msg,
            STRICT_ENV,
            exc_info=exc,
        )
    else:
        logger.debug(msg)


def note_unscoped(event: str, path: Any) -> None:
    """Count an observed I/O event that happened outside any scope.

    Out-of-scope I/O is legitimate (library use, notebooks), so this is a
    one-time INFO plus a counter rather than a warning; the payload's
    ``in_scope=False`` lets observers decide.
    """
    global _unscoped_noted
    with _lock:
        if event == "save":
            _process.unscoped_saves += 1
        else:
            _process.unscoped_loads += 1
        first = not _unscoped_noted
        _unscoped_noted = True
    if first:
        logger.info(
            "scitex_io provenance: %s of %s happened outside any provenance "
            "scope (no @stx.session / scitex_io.provenance_scope active); "
            "observers were notified with in_scope=False. Counted in "
            "scitex_io.observer_failures()['unscoped_%ss'].",
            event,
            path,
            event,
        )


__all__ = [
    "ProvenanceError",
    "ProvenanceScope",
    "STRICT_ENV",
    "current_scope",
    "note_unscoped",
    "observer_failures",
    "provenance_scope",
    "report_failure",
    "reset_observer_failures",
    "strict_provenance",
]

# EOF
