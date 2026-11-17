#!/usr/bin/env python3
"""Run notebook-path-vectors.json against a resolver in a REAL IPython shell.

BYTE-IDENTICAL in scitex-io and scitex-session (see the vectors' "about").
Not a test module: the repository's test calls it in a fresh interpreter so the
IPython singleton it creates never leaks into the rest of the suite.

Usage::

    python run_notebook_vectors.py VECTORS.json MODULE:FUNCTION SANDBOX_PARENT

``MODULE:FUNCTION`` is ``resolve_notebook(shell=..., environ=...)`` returning
``{"path": ..., "source": ...}``. Prints one JSON list on stdout:
``[{"id", "path" (relative to the case sandbox, or null), "source"}]``.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import tempfile

from IPython.core.interactiveshell import InteractiveShell

_NS_KEYS = ("__vsc_ipynb_file__", "__session__")
_LAUNCHER = "import time; time.sleep(300)"


def _sub(value, sandbox):
    return value.replace("{S}", sandbox) if isinstance(value, str) else value


def _write_notebook(path, cells, probe):
    nb_cells = []
    for cell in cells:
        if isinstance(cell, str):
            cell = {"cell_type": "code", "source": probe if cell == "PROBE" else cell}
        entry = {
            "cell_type": cell["cell_type"],
            "metadata": {},
            "source": cell["source"],
        }
        if entry["cell_type"] == "code":
            entry.update(execution_count=None, outputs=[])
        nb_cells.append(entry)
    nb = {"cells": nb_cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(nb, fh)


def _run_case(case, resolve, shell, probe, parent):
    sandbox = os.path.realpath(tempfile.mkdtemp(prefix="nbvec-", dir=parent))
    for rel, cells in (case.get("notebooks") or {}).items():
        _write_notebook(os.path.join(sandbox, rel), cells, probe)
    for rel in case.get("files") or []:
        path = os.path.join(sandbox, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").close()
    launcher = case.get("launcher") or {"argv": [], "cwd": "."}
    proc = subprocess.Popen(
        [sys.executable, "-c", _LAUNCHER, *launcher["argv"]],
        cwd=os.path.join(sandbox, launcher.get("cwd", ".")),
    )
    try:
        environ = {k: _sub(v, sandbox) for k, v in (case.get("env") or {}).items()}
        environ["JPY_PARENT_PID"] = str(proc.pid)
        os.chdir(os.path.join(sandbox, case.get("cwd", ".")))
        for key in _NS_KEYS:
            shell.user_ns.pop(key, None)
        for key, value in (case.get("user_ns") or {}).items():
            shell.user_ns[key] = _sub(value, sandbox)
        shell.user_ns["__vector_resolve__"] = lambda: resolve(
            shell=shell, environ=environ
        )
        result = shell.run_cell(probe, store_history=True)
        result.raise_error()
        out = shell.user_ns.pop("__vector_result__")
    finally:
        proc.kill()
        proc.wait()
    path = out.get("path")
    return {
        "id": case["id"],
        "path": os.path.relpath(path, sandbox) if path else None,
        "source": out.get("source"),
    }


def main(argv):
    vectors_path, target, parent = argv[1:4]
    with open(vectors_path, encoding="utf-8") as fh:
        vectors = json.load(fh)
    module, func = target.split(":")
    resolve = getattr(importlib.import_module(module), func)
    shell = InteractiveShell.instance()
    probe = vectors["probe_cell"]
    results = [
        _run_case(case, resolve, shell, probe, parent) for case in vectors["cases"]
    ]
    sys.stdout.write(json.dumps(results) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
