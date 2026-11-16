#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capture EVERY file a single ``scitex_io.save`` call writes.

A save rarely writes only the file it was asked for: image saves export
``<stem>.csv`` / ``<stem>_for_sigmaplot.csv`` data sidecars and
``<stem>_<ax>_legend.<ext>`` legends; figrecipe ``RecordingFigure``
saves write a ``<stem>.yaml`` recipe and per-panel data; ``symlink_from_cwd``
/ ``symlink_to`` plant links. Before this module only the primary path
reached the post-save hook, so every sidecar was invisible to provenance.

Two complementary mechanisms, both driven by :class:`WriteCapture`:

1. **Explicit notes** — scitex-io's own sidecar writers (``_save`` dispatch,
   symlink helpers) call :func:`note_written` / :func:`note_symlink`.
2. **Filesystem diff** — for writers scitex-io does not control (figrecipe,
   third-party savers), the primary's directory is snapshotted before the
   handler and compared afterwards. Only entries sharing the primary's stem
   (``<stem>``, ``<stem>.*``, ``<stem>_*``, ``<stem>-*``; directories with
   such names are walked) are considered, which keeps the scan cheap and
   confined to that save's sidecars.

Nested public saves (a handler that itself calls ``scitex_io.save``) fire
their own hooks; their files are excluded from the outer capture so no
file is reported twice.
"""

from __future__ import annotations

import contextvars
import os
from typing import Dict, List, Optional, Set, Tuple

_active: contextvars.ContextVar[Optional["WriteCapture"]] = contextvars.ContextVar(
    "scitex_io_write_capture", default=None
)

_Sig = Tuple[int, int, int]


def _sig(st: os.stat_result) -> _Sig:
    return (st.st_ino, st.st_mtime_ns, st.st_size)


class WriteCapture:
    """Context manager recording the files written while it is active."""

    def __init__(self, primary: str) -> None:
        self.primary = os.path.abspath(primary)
        self.parent = os.path.dirname(self.primary)
        self.stem = os.path.splitext(os.path.basename(self.primary))[0]
        self.noted: List[str] = []
        self.links: Dict[str, str] = {}  # link path -> target realpath
        self.reported: Set[str] = set()  # realpaths reported by nested saves
        self.scan_error: Optional[BaseException] = None
        self._before: Dict[str, _Sig] = {}
        self._token = None
        self._parent_capture: Optional[WriteCapture] = None

    # -- filesystem snapshot -------------------------------------------------
    def _matches(self, name: str) -> bool:
        s = self.stem
        return name == s or name[: len(s) + 1] in (s + ".", s + "_", s + "-")

    def _scan(self) -> Dict[str, _Sig]:
        found: Dict[str, _Sig] = {}
        if not os.path.isdir(self.parent):
            return found
        primary_real = os.path.realpath(self.primary)
        with os.scandir(self.parent) as it:
            for entry in it:
                if not self._matches(entry.name):
                    continue
                path = entry.path
                if os.path.realpath(path) == primary_real:
                    continue  # primary is reported on its own
                if entry.is_symlink():
                    continue  # links are recorded explicitly, never hashed
                if entry.is_file():
                    found[path] = _sig(entry.stat())
                elif entry.is_dir():
                    for root, _dirs, files in os.walk(path):
                        for fname in files:
                            fp = os.path.join(root, fname)
                            if not os.path.islink(fp):
                                found[fp] = _sig(os.stat(fp))
        return found

    # -- context protocol ----------------------------------------------------
    def __enter__(self) -> "WriteCapture":
        try:
            self._before = self._scan()
        except OSError as exc:
            self.scan_error = exc
        self._parent_capture = _active.get()
        self._token = _active.set(self)
        return self

    def __exit__(self, *exc_info) -> None:
        _active.reset(self._token)

    # -- results -------------------------------------------------------------
    def sidecars(self) -> List[str]:
        """Realpaths of files written besides the primary, sorted, deduped."""
        candidates: List[str] = list(self.noted)
        if self.scan_error is None:
            try:
                after = self._scan()
            except OSError as exc:
                self.scan_error = exc
                after = {}
            candidates += [p for p, s in after.items() if self._before.get(p) != s]
        primary_real = os.path.realpath(self.primary)
        out: List[str] = []
        seen: Set[str] = set()
        for path in candidates:
            real = os.path.realpath(path)
            if real == primary_real or real in seen or real in self.reported:
                continue
            if not os.path.isfile(real):
                continue
            seen.add(real)
            out.append(real)
        return sorted(out)

    def symlinks_to(self, realpath: str) -> List[str]:
        """Link paths (as created) whose target resolves to ``realpath``."""
        return sorted(link for link, tgt in self.links.items() if tgt == realpath)

    def mark_reported(self, realpaths) -> None:
        """Tell the enclosing capture (if any) these files were reported."""
        if self._parent_capture is not None:
            self._parent_capture.reported.update(realpaths)


def capture_writes(primary: str) -> WriteCapture:
    return WriteCapture(primary)


def note_written(path) -> None:
    """Record that the active save wrote ``path`` (no-op outside a save)."""
    cap = _active.get()
    if cap is not None:
        cap.noted.append(os.path.abspath(str(path)))


def note_symlink(link) -> None:
    """Record a symlink created by the active save (no-op outside a save)."""
    cap = _active.get()
    if cap is None:
        return
    link = os.path.abspath(str(link))
    if os.path.islink(link):
        cap.links[link] = os.path.realpath(link)


__all__ = ["WriteCapture", "capture_writes", "note_written", "note_symlink"]

# EOF
