#!/usr/bin/env python3
"""Notebook resolution for ``save()`` in Jupyter kernels (issue #197).

Two layers, both real (no mocks):

1. Conformance vectors -- ``conformance/notebook-path-vectors.json`` and its
   runner are byte-identical in scitex-session, whose suite runs the same
   vectors against ITS resolver. Each case runs in a real IPython shell with a
   real launcher process (``/proc/<pid>/cmdline``).
2. Headless kernels -- real notebooks executed by real kernels through
   nbclient / ``jupyter nbconvert`` / papermill; the test checks where
   ``scitex_io.save("x.json")`` actually wrote.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CONFORMANCE = Path(__file__).resolve().parent / "conformance"
VECTORS = CONFORMANCE / "notebook-path-vectors.json"
RUNNER = CONFORMANCE / "run_notebook_vectors.py"
CASES = json.loads(VECTORS.read_text())["cases"]
SRC = Path(__file__).resolve().parents[2] / "src"

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="the launcher's command line is read from /proc",
)


def _child_env(scratch: Path, **extra):
    """Environment for child processes: this one minus notebook signals.

    Temporary and Jupyter runtime files go under ``scratch`` (the test's own
    tmp dir). jupyter_client writes each kernel's connection file into
    ``$TMPDIR`` (or the runtime dir) and then sets the STICKY BIT on that
    directory; pointed at the suite's shared ``$TMPDIR`` it changes a
    directory the test does not own (the release driver refuses to clean up
    a scratch root whose mode changed from 700 to 1700).
    """
    env = dict(os.environ)
    for key in ("SCITEX_NOTEBOOK_PATH", "JPY_SESSION_NAME", "JPY_PARENT_PID"):
        env.pop(key, None)
    own_tmp = scratch / "child-tmp"
    own_tmp.mkdir(parents=True, exist_ok=True)
    env["TMPDIR"] = str(own_tmp)
    env["JUPYTER_RUNTIME_DIR"] = str(own_tmp / "jupyter-runtime")
    env["PYTHONPATH"] = os.pathsep.join(
        p for p in (str(SRC), env.get("PYTHONPATH", "")) if p
    )
    env.update(extra)
    return env


# ---------------------------------------------------------------------------
# 1. Conformance vectors (shared with scitex-session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def vector_results(tmp_path_factory):
    pytest.importorskip("IPython")
    parent = tmp_path_factory.mktemp("nbvec")
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            str(VECTORS),
            "scitex_io._notebook:resolve_notebook",
            str(parent),
        ],
        capture_output=True,
        text=True,
        env=_child_env(parent),
        cwd=str(parent),
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"vector runner failed:\n{proc.stderr[-4000:]}")
    results = json.loads(proc.stdout.strip().splitlines()[-1])
    return {r["id"]: r for r in results}


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_notebook_path_vector_resolves_as_specified(case, vector_results):
    # Arrange
    expect = {"path": case["expect"]["path"], "source": case["expect"].get("source")}
    # Act
    got = vector_results[case["id"]]
    # Assert
    assert {"path": got["path"], "source": got["source"]} == expect


# ---------------------------------------------------------------------------
# 2. Real headless kernels
# ---------------------------------------------------------------------------

SAVE_CELL = (
    "import scitex_io\n"
    "saved = scitex_io.save({'ok': 1}, 'x.json', verbose=False)\n"
    "print('SAVED', saved)"
)

#: Where the save landed, when it landed next to the notebook.
NEXT_TO_NOTEBOOK = {
    "<nb>_out/x.json": {"ok": 1},
    "<cwd>/notebook_out exists": False,
    "<nbdir>/notebook_out exists": False,
}


def _make_notebook(path: Path, cells=(SAVE_CELL,)):
    nbformat = pytest.importorskip("nbformat")
    nb = nbformat.v4.new_notebook()
    nb.cells = [nbformat.v4.new_code_cell(src) for src in cells]
    nb.metadata["kernelspec"] = {
        "name": "python3",
        "display_name": "Python 3",
        "language": "python",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(path))


def _stream_text(nb_path: Path) -> str:
    nb = json.loads(nb_path.read_text())
    texts = []
    for cell in nb["cells"]:
        for out in cell.get("outputs", []):
            text = out.get("text", "")
            texts.append("".join(text) if isinstance(text, list) else text)
    return "".join(texts)


def _where_saved(nb: Path, work: Path) -> dict:
    target = nb.parent / f"{nb.stem}_out" / "x.json"
    return {
        "<nb>_out/x.json": json.loads(target.read_text()) if target.is_file() else None,
        "<cwd>/notebook_out exists": (work / "notebook_out").exists(),
        "<nbdir>/notebook_out exists": (nb.parent / "notebook_out").exists(),
    }


def _run(cmd, work: Path, **env) -> None:
    proc = subprocess.run(
        cmd,
        cwd=str(work),
        env=_child_env(work.parent, **env),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[:3]} failed:\n{proc.stderr[-4000:]}")


@pytest.fixture
def layout(tmp_path):
    """``<tmp>/proj/nbdir/e.ipynb`` launched from ``<tmp>/work``.

    The kernel runs in ``work`` (an unrelated directory), so the pre-#197
    result -- ``<cwd>/notebook_out/x.json`` -- is distinguishable.
    """
    pytest.importorskip("nbclient")
    pytest.importorskip("ipykernel")
    work = tmp_path / "work"
    work.mkdir()
    nb = tmp_path / "proj" / "nbdir" / "e.ipynb"
    _make_notebook(nb)
    return work, nb


NBCLIENT_DRIVER = """
import sys, nbformat
from nbclient import NotebookClient
nb_path, out_path, kernel_cwd = sys.argv[1:4]
nb = nbformat.read(nb_path, as_version=4)
NotebookClient(nb, timeout=120, resources={"metadata": {"path": kernel_cwd}}).execute()
nbformat.write(nb, out_path)
"""


def test_nbclient_script_saves_to_notebook_out_dir(layout):
    # Arrange -- a script runs the notebook via nbclient (path on its argv)
    work, nb = layout
    cmd = [
        sys.executable,
        "-c",
        NBCLIENT_DRIVER,
        os.path.relpath(nb, work),
        str(work / "executed.ipynb"),
        str(work),
    ]
    # Act
    _run(cmd, work)
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


def test_nbconvert_execute_saves_to_notebook_out_dir(layout):
    # Arrange -- notebook given relative to the launcher's cwd, as users type it
    pytest.importorskip("nbconvert")
    work, nb = layout
    cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        os.path.relpath(nb, work),
        "--output-dir",
        str(work),
    ]
    # Act
    _run(cmd, work)
    # Assert -- nbconvert runs the kernel in the notebook's directory
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


def test_papermill_saves_to_notebook_out_dir(layout):
    # Arrange -- the kernel runs in an unrelated --cwd
    pytest.importorskip("papermill")
    work, nb = layout
    cmd = [
        sys.executable,
        "-m",
        "papermill",
        os.path.relpath(nb, work),
        str(work / "run.ipynb"),
        "--cwd",
        str(work),
        "-k",
        "python3",
    ]
    # Act
    _run(cmd, work)
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


# This driver gets the notebook path from an environment variable, so the
# launcher's command line names no notebook: only the source under test (or
# nothing) can resolve it.
ENV_DRIVER = """
import os, nbformat
from nbclient import NotebookClient
nb = nbformat.read(os.environ["NBTEST_NOTEBOOK"], as_version=4)
NotebookClient(nb, timeout=120, resources={"metadata": {"path": os.environ["NBTEST_CWD"]}}).execute()
nbformat.write(nb, os.environ["NBTEST_OUT"])
"""


def _run_env_driver(nb: Path, work: Path, **env) -> Path:
    out = work / "executed.ipynb"
    _run(
        [sys.executable, "-c", ENV_DRIVER],
        work,
        NBTEST_NOTEBOOK=str(nb),
        NBTEST_OUT=str(out),
        NBTEST_CWD=str(work),
        **env,
    )
    return out


def test_jupyter_session_name_env_saves_to_notebook_out_dir(layout):
    # Arrange -- what a Jupyter server sets for the kernels it starts
    work, nb = layout
    # Act
    _run_env_driver(nb, work, JPY_SESSION_NAME=str(nb))
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


def test_scitex_notebook_path_env_saves_to_notebook_out_dir(layout):
    # Arrange
    work, nb = layout
    # Act
    _run_env_driver(nb, work, SCITEX_NOTEBOOK_PATH=str(nb))
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


def test_vscode_variable_saves_to_notebook_out_dir(tmp_path):
    # Arrange -- VS Code injects __vsc_ipynb_file__ into the user namespace
    pytest.importorskip("nbclient")
    pytest.importorskip("ipykernel")
    work = tmp_path / "work"
    work.mkdir()
    nb = tmp_path / "proj" / "nbdir" / "e.ipynb"
    _make_notebook(nb, cells=(f"__vsc_ipynb_file__ = {str(nb)!r}", SAVE_CELL))
    # Act
    _run_env_driver(nb, work)
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


@pytest.fixture
def unresolved_run(layout):
    """A headless run in which nothing names the notebook."""
    work, nb = layout
    out = _run_env_driver(nb, work)
    return work, nb, out


def test_unresolvable_notebook_falls_back_to_cwd_notebook_out(unresolved_run):
    # Arrange
    work, nb, _out = unresolved_run
    # Act
    saved = {
        "<cwd>/notebook_out/x.json": (work / "notebook_out" / "x.json").is_file(),
        "<nb>_out exists": (nb.parent / f"{nb.stem}_out").exists(),
    }
    # Assert
    assert saved == {"<cwd>/notebook_out/x.json": True, "<nb>_out exists": False}


def test_unresolvable_notebook_warns_with_reason_and_fix(unresolved_run):
    # Arrange
    _work, _nb, out = unresolved_run
    # Act
    text = _stream_text(out)
    found = [
        m
        for m in (
            "notebook path could not be auto-detected",
            "Sources tried: ",
            "SCITEX_NOTEBOOK_PATH",
        )
        if m in text
    ]
    # Assert
    assert len(found) == 3, text


def _same_env_jupyter():
    jupyter = shutil.which("jupyter")
    if jupyter is None:
        return None
    if Path(jupyter).absolute().parent != Path(sys.executable).absolute().parent:
        return None
    return jupyter


@pytest.mark.skipif(_same_env_jupyter() is None, reason="no jupyter CLI here")
def test_jupyter_execute_cli_saves_to_notebook_out_dir(layout):
    # Arrange
    work, nb = layout
    cmd = [_same_env_jupyter(), "execute", os.path.relpath(nb, work)]
    # Act
    _run(cmd, work)
    # Assert
    assert _where_saved(nb, work) == NEXT_TO_NOTEBOOK


def test_headless_kernel_leaves_suite_tmpdir_mode_unchanged(layout):
    # Arrange -- jupyter_client sets the sticky bit on the directory holding
    # a kernel's connection file; that must never be the suite's own $TMPDIR
    import tempfile

    work, nb = layout
    suite_tmp = tempfile.gettempdir()
    before = os.stat(suite_tmp).st_mode
    # Act
    _run(
        [
            sys.executable,
            "-m",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            str(nb),
            "--output-dir",
            str(work),
        ],
        work,
    )
    # Assert
    assert os.stat(suite_tmp).st_mode == before
