#!/usr/bin/env python3
# File: ./src/scitex_io/_notebook.py
"""Which notebook is this Jupyter kernel executing?

``scitex_io.save("x.json")`` called in a notebook ``/path/to/a.ipynb`` writes
``/path/to/a_out/x.json``. That needs the notebook's path, which a kernel does
not know directly: ``sys.argv`` is the kernel's own command line
(``ipykernel_launcher -f <connection file> ...``), never the notebook.

:func:`resolve_notebook` tries, first match wins (the winner is returned as
``"source"``):

``env``            ``$SCITEX_NOTEBOOK_PATH`` (explicit; relative paths are
                   resolved against the kernel's cwd)
``vscode``         ``__vsc_ipynb_file__`` in the user namespace (VS Code)
``jupyter``        ``__session__`` in the user namespace / ``$JPY_SESSION_NAME``
                   (set for kernels a Jupyter server starts)
``parent-cmdline`` a ``*.ipynb`` argument of the process that launched the
                   kernel (``$JPY_PARENT_PID``, else the parent pid), resolved
                   against THAT process's cwd: ``jupyter nbconvert --execute``,
                   ``papermill``, ``jupyter execute``, nbclient scripts.
                   ACCEPTED ONLY when that notebook's code cells contain the
                   cell being executed — the launcher may name a notebook it is
                   not running
``jupyter-server`` ``scitex_context.get_notebook_path()`` (asks a running
                   Jupyter server which notebook owns this kernel)

KEEP IN SYNC: scitex-session resolves the notebook for ``@session`` with the
same rule (``scitex_session._lifecycle._notebook.resolve_notebook``) so that
``save()`` and the session agree on ``<notebook>_out/``. Both repositories run
the byte-identical conformance file ``tests/**/conformance/notebook-path-
vectors.json``; a change to this rule must update BOTH implementations and
that file IN BOTH REPOSITORIES in the same change.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from scitex_logging import getLogger

logger = getLogger(__name__)

#: Explicit notebook path (shared with scitex-session).
NOTEBOOK_PATH_ENV = "SCITEX_NOTEBOOK_PATH"


def ipython_shell() -> Any:
    """The running IPython shell, or ``None`` outside IPython."""
    ipython = sys.modules.get("IPython")
    get_ipython = getattr(ipython, "get_ipython", None)
    if get_ipython is None:
        return None
    try:
        return get_ipython()
    except Exception:  # noqa: BLE001 - an unusable IPython is "not IPython"
        return None


def current_cell_source(shell: Any = None) -> Optional[str]:
    """Raw source of the cell being executed (IPython stores it first)."""
    shell = ipython_shell() if shell is None else shell
    manager = getattr(shell, "history_manager", None)
    raw = getattr(manager, "input_hist_raw", None)
    if not raw or len(raw) < 2:  # index 0 is a placeholder ("")
        return None
    return str(raw[-1])


def _normalise(source: str) -> str:
    return source.replace("\r\n", "\n").replace("\r", "\n")


def notebook_code_cells(path: os.PathLike) -> List[str]:
    """Sources of the notebook's code cells, in order (nbformat 4, or 3)."""
    with open(path, encoding="utf-8") as fh:
        nb = json.load(fh)
    cells = nb.get("cells")
    if cells is None:  # nbformat 3: cells live in worksheets, source in "input"
        cells = [c for ws in nb.get("worksheets") or [] for c in ws.get("cells") or []]
    sources = []
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        src = cell.get("source", cell.get("input", ""))
        if isinstance(src, list):
            src = "".join(src)
        sources.append(_normalise(str(src)))
    return sources


def _contains_cell(path: str, cell: Optional[str]) -> bool:
    if cell is None:
        return False
    want = _normalise(cell).strip()
    try:
        return any(src.strip() == want for src in notebook_code_cells(path))
    except (OSError, ValueError, AttributeError):
        return False


def _existing_ipynb(value: Any, base: Optional[str] = None) -> Optional[str]:
    if not isinstance(value, str) or not value.endswith(".ipynb"):
        return None
    path = value if os.path.isabs(value) or base is None else os.path.join(base, value)
    path = os.path.realpath(os.path.abspath(path))
    return path if os.path.isfile(path) else None


def _parent_pid(environ: Dict[str, str]) -> Optional[int]:
    raw = environ.get("JPY_PARENT_PID", "")
    if raw.isdigit():
        return int(raw)
    ppid = os.getppid()
    return ppid if ppid > 1 else None


def parent_command_line(pid: int) -> Optional[tuple]:
    """``(argv, cwd)`` of process ``pid``, or ``None`` when unreadable.

    Linux ``/proc``; elsewhere psutil when it is installed.
    """
    proc = Path("/proc") / str(pid)
    if proc.is_dir():
        try:
            argv = (proc / "cmdline").read_bytes().split(b"\0")
            cwd = os.readlink(proc / "cwd")
        except OSError:
            return None
        return [os.fsdecode(a) for a in argv if a], cwd
    try:
        import psutil  # optional
    except ImportError:
        return None
    try:
        parent = psutil.Process(pid)
        return parent.cmdline(), parent.cwd()
    except Exception:  # noqa: BLE001 - gone / access denied: nothing to read
        return None


def resolve_notebook(
    shell: Any = None, environ: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Locate the notebook this kernel is executing (see module docstring).

    Returns ``{"path": str, "source": str}`` (``path`` is a realpath), or
    ``{"path": None, "reason": str}`` when no source names it.
    """
    environ = os.environ if environ is None else environ
    shell = ipython_shell() if shell is None else shell
    tried: List[str] = []

    explicit = environ.get(NOTEBOOK_PATH_ENV, "").strip()
    if explicit:
        path = _existing_ipynb(explicit, os.getcwd())
        if path is not None:
            return {"path": path, "source": "env"}
        logger.warning(
            "scitex-io: $%s=%r is not an existing .ipynb file; ignoring it",
            NOTEBOOK_PATH_ENV,
            explicit,
        )
        tried.append(f"${NOTEBOOK_PATH_ENV} {explicit!r} is not an existing .ipynb")

    user_ns = getattr(shell, "user_ns", None) or {}
    path = _existing_ipynb(user_ns.get("__vsc_ipynb_file__"))
    if path is not None:
        return {"path": path, "source": "vscode"}
    for value in (user_ns.get("__session__"), environ.get("JPY_SESSION_NAME")):
        # absolute (Jupyter Server 2) or relative to the server root; the
        # kernel runs in the notebook's directory, so try its name there too
        path = _existing_ipynb(value, os.getcwd())
        if path is None and isinstance(value, str):
            path = _existing_ipynb(os.path.basename(value), os.getcwd())
        if path is not None:
            return {"path": path, "source": "jupyter"}

    pid = _parent_pid(environ)
    parent = parent_command_line(pid) if pid is not None else None
    if parent is not None:
        argv, cwd = parent
        candidates = [p for p in (_existing_ipynb(a, cwd) for a in argv[1:]) if p]
        cell = current_cell_source(shell)
        for candidate in candidates:
            if _contains_cell(candidate, cell):
                return {"path": candidate, "source": "parent-cmdline"}
        if candidates:
            tried.append(
                f"the launching process names {candidates} but none of them "
                "contains the cell being executed"
            )
        else:
            tried.append("the launching process names no .ipynb file")
    else:
        tried.append("the launching process's command line is not readable")

    try:
        from scitex_context import get_notebook_path

        path = _existing_ipynb(get_notebook_path())
    except Exception as exc:  # noqa: BLE001 - recorded in the reason below
        path = None
        tried.append(f"Jupyter server query failed ({type(exc).__name__}: {exc})")
    if path is not None:
        return {"path": path, "source": "jupyter-server"}
    return {"path": None, "reason": "; ".join(tried) or "no notebook source"}


# EOF
