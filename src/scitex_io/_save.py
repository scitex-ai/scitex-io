#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-29 07:21:17 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-io/src/scitex_io/_save.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = "./src/scitex_io/_save.py"
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

__FILE__ = __file__


"""
1. Functionality:
   - Provides utilities for saving various data types to different file formats.
2. Input:
   - Objects to be saved (e.g., NumPy arrays, PyTorch tensors, Pandas DataFrames, etc.)
   - File path or name where the object should be saved
3. Output:
   - Saved files in various formats (e.g., CSV, NPY, PKL, JOBLIB, PNG, HTML, TIFF, MP4, YAML, JSON, HDF5, PTH, MAT, CBM)
4. Prerequisites:
   - Python 3.x
   - Required libraries: numpy, pandas, torch, matplotlib, plotly, h5py, joblib, PIL, ruamel.yaml
"""

"""Imports"""
import inspect
import os as _os
from pathlib import Path
from typing import Any, Union

from scitex_logging import getLogger as _getLogger

from ._image_csv_handler import handle_image_with_csv  # noqa: F401
from ._path_modules._symlink import _symlink, _symlink_to, sh  # noqa: F401
from ._registry import get_saver  # noqa: F401
from ._utils import clean, clean_path, color_text, getsize, readable_bytes

logger = _getLogger(__name__)


# Module-level latch for the once-per-process notebook-path warning.
_NOTEBOOK_PATH_WARNED = False


def _warn_notebook_path_unresolved_once(fallback_sdir: str) -> None:
    """Emit a one-time hint when notebook-name detection fails.

    Triggered when ``scitex_io.save`` runs inside a notebook but
    ``get_notebook_info_simple()`` couldn't recover the notebook stem.
    Falling back to ``<cwd>/notebook_out/`` is correct but surprising
    — explain the canonical convention and how to opt in.

    Silenced for the rest of the process by:
      - ``SCITEX_IO_QUIET_NOTEBOOK_WARN=1`` env var, OR
      - the latch (only the first call ever emits).
    """
    global _NOTEBOOK_PATH_WARNED
    if _NOTEBOOK_PATH_WARNED:
        return
    if _os.environ.get("SCITEX_IO_QUIET_NOTEBOOK_WARN"):
        _NOTEBOOK_PATH_WARNED = True
        return
    _NOTEBOOK_PATH_WARNED = True
    msg = (
        "scitex_io: notebook path could not be auto-detected; saving to "
        f"{fallback_sdir!r} instead of <notebook_dir>/<stem>_out/.\n"
        "  Canonical convention: <dir>/<stem>.ipynb -> sio.save(obj, 'name.ext') "
        "-> <dir>/<stem>_out/name.ext\n"
        "  Fix by setting SCITEX_NOTEBOOK_PATH before running, e.g.:\n"
        "    SCITEX_NOTEBOOK_PATH=demo.ipynb jupyter nbconvert --execute --inplace demo.ipynb\n"
        "  Silence this hint with SCITEX_IO_QUIET_NOTEBOOK_WARN=1.\n"
        "  Or pass an absolute path to bypass routing: sio.save(obj, '/abs/path.ext').\n"
        "  (This message prints at most once per process.)"
    )
    print(msg, file=__import__("sys").stderr, flush=True)


def save(
    obj: Any,
    specified_path: Union[str, Path],
    makedirs: bool = True,
    verbose: bool = True,
    symlink_from_cwd: bool = False,
    symlink_to: Union[str, Path] = None,
    dry_run: bool = False,
    no_csv: bool = False,
    use_caller_path: bool = True,
    env_detector=None,
    **kwargs,
) -> None:
    """Save ``obj`` by extension; ``specified_path`` is caller-anchored.

    The file format is selected from ``specified_path``'s extension via
    the plugin registry — `.csv`, `.npy`, `.pkl`, `.yaml`, `.png`,
    `.h5`, ... 30+ formats are built in; custom extensions can be added
    with ``register_saver``.

    Path resolution rules (when ``specified_path`` is relative):

    - Called from a script ``/path/to/analysis.py`` →
      ``/path/to/analysis_out/<specified_path>``.
    - Called from a notebook ``/path/to/exp.ipynb`` →
      ``/path/to/exp_out/<specified_path>``.
    - Called from ``python -i`` / IPython / interactive REPL →
      ``$SCITEX_DIR/io/runtime/cache/<specified_path>`` (default
      ``~/.scitex/io/runtime/cache/``). Honours the canonical scitex
      local-state convention; see scitex-dev skills/general
      ``01_ecosystem_06_local-state-directories.md``.
    - Absolute path → used as-is, no routing.

    Intermediate directories are created automatically — callers do
    not need ``os.makedirs()`` / ``Path.mkdir()``.

    Parameters
    ----------
    obj : Any
        The object to be saved.
    specified_path : Union[str, Path]
        The filename or relative path under which to save ``obj``. May
        contain subdirectories (``"sub/dir/file.csv"``); intermediates
        are auto-created. Absolute paths bypass routing.
    makedirs : bool, optional
        Create parent directories on demand. Default ``True``.
    verbose : bool, optional
        Print a one-line success message. Default ``True``.
    symlink_from_cwd : bool, optional
        Drop a symlink at ``./<specified_path>`` pointing into the
        auto-routed location. Default ``False``.
    symlink_to : Union[str, Path], optional
        Plant a symlink at this custom path pointing to the saved file.
    dry_run : bool, optional
        Print the resolved path without writing. Default ``False``.
    no_csv : bool, optional
        Skip the auto-CSV sidecar for figure saves. Default ``False``.
    use_caller_path : bool, optional
        Resolve the anchor from the calling script, not the immediate
        caller — needed when ``save`` is wrapped by a library. Default
        ``False``.
    **kwargs
        Passed through to the per-format handler.

    Returns
    -------
    Path or None
        Path to saved file on success, ``None``/``False`` on error.
    """
    try:
        # ``track`` is a scitex-io / observer concept, NOT a format-handler
        # argument. Pop it before any dispatch so it never reaches the
        # per-format handlers (_save_yaml/_save_pickle take no extra
        # kwargs and would raise on an unexpected ``track=``). It is handed
        # back to the post-save hook below so clew can gate tracking on it.
        track = kwargs.pop("track", True)

        if isinstance(specified_path, Path):
            specified_path = str(specified_path)

        ########################################
        # DO NOT MODIFY THIS SECTION
        ########################################
        spath, sfname = None, None

        # f-expression handling - safely parse f-strings
        if specified_path.startswith('f"') or specified_path.startswith("f'"):
            path_content = specified_path[2:-1]
            frame = inspect.currentframe().f_back
            try:
                import re

                variables = re.findall(r"\{([^}]+)\}", path_content)
                format_dict = {}
                for var in variables:
                    if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", var):
                        if var in frame.f_locals:
                            format_dict[var] = frame.f_locals[var]
                        elif var in frame.f_globals:
                            format_dict[var] = frame.f_globals[var]
                    else:
                        raise ValueError(f"Invalid variable name in f-string: {var}")
                specified_path = path_content.format(**format_dict)
            finally:
                del frame

        if specified_path.startswith("/"):
            spath = specified_path
        else:
            from ._utils import detect_environment, get_notebook_info_simple

            if env_detector is None:
                env_detector = detect_environment
            env_type = env_detector()

            if env_type == "jupyter":
                # Defensive: get_notebook_info_simple was historically a stub
                # that returned a dict — unpacking it as a 2-tuple iterated
                # the dict keys, producing `notebook_name='path'`,
                # `notebook_dir='name'`, and every notebook saved to
                # `<cwd>/name/path_out/`. Guard against any non-tuple shape.
                info = get_notebook_info_simple()
                if isinstance(info, tuple) and len(info) == 2:
                    notebook_name, notebook_dir = info
                else:
                    notebook_name, notebook_dir = None, None
                if notebook_name:
                    notebook_base = _os.path.splitext(notebook_name)[0]
                    sdir = _os.path.join(
                        notebook_dir or _os.getcwd(), f"{notebook_base}_out"
                    )
                else:
                    sdir = _os.path.join(_os.getcwd(), "notebook_out")
                    _warn_notebook_path_unresolved_once(sdir)
                spath = _os.path.join(sdir, specified_path)

            elif env_type == "script":
                # use_caller_path defaults to True so a save under
                # `@stx.session` (or any other scitex wrapper) walks past
                # the scitex frames in inspect.stack() to the real user
                # script. Direct (unwrapped) callers also work: no scitex
                # frames are present so the walk falls through to
                # frame[1] = the user script.
                #
                # We detect scitex frames by MODULE NAME (any
                # ``scitex_*`` package), NOT by directory prefix —
                # because scitex_io and scitex_dev may live in different
                # site-packages locations (PYTHONPATH overlay, editable
                # install of one but not the other, etc.) and a parent-
                # path comparison would silently miss the wrapper frame.
                # 2026-06-13 operator dogfood: a script saved via
                # ``stx.io.save`` landed inside
                # ``scitex_dev/_core/decorators_out/`` because the
                # parent-path scan didn't match scitex_dev's path → the
                # walker treated the wrapper frame as the user script.
                if use_caller_path:
                    script_path = None
                    for frame_info in inspect.stack()[1:]:
                        mod_name = frame_info.frame.f_globals.get("__name__", "") or ""
                        if not (
                            mod_name == "scitex"
                            or mod_name.startswith("scitex.")
                            or mod_name.startswith("scitex_")
                        ):
                            script_path = _os.path.abspath(frame_info.filename)
                            break
                    if script_path is None:
                        script_path = inspect.stack()[1].filename
                else:
                    script_path = inspect.stack()[1].filename

                sdir = clean_path(_os.path.splitext(script_path)[0] + "_out")
                spath = _os.path.join(sdir, specified_path)

            elif env_type in ("ipython", "interactive"):
                # Interactive sessions (IPython terminal REPL / bare
                # `python` / `python -i` / `python -c`) have no script
                # path to anchor `_out/` to, so route writes into the
                # canonical scitex local-state cache:
                #   $SCITEX_DIR/io/runtime/cache/  (default ~/.scitex)
                # See scitex-dev skills/general/
                #   01_ecosystem_06_local-state-directories.md
                _scitex_dir = _os.environ.get(
                    "SCITEX_DIR",
                    _os.path.join(_os.path.expanduser("~"), ".scitex"),
                )
                sdir = _os.path.join(_scitex_dir, "io", "runtime", "cache")
                _os.makedirs(sdir, exist_ok=True)
                spath = _os.path.join(sdir, specified_path)

            else:
                # Fail fast, fail loud: NO silent `<cwd>/output/` fallback.
                # An unrecognised env_type means detect_environment() (or
                # a caller-supplied env_detector) returned something
                # outside the documented vocabulary; guessing an output
                # path here is exactly the quiet-wrong-place bug this
                # branch used to cause. Operator directive 2026-06-13:
                # "no else pattern accepted" — raise with a clear
                # diagnostic + the documented vocabulary so the caller
                # can fix detect_environment / their env_detector
                # contract.
                raise ValueError(
                    "scitex.io.save: unrecognised execution environment "
                    f"{env_type!r}. Expected one of "
                    "'jupyter' (Jupyter kernel), "
                    "'ipython' (IPython terminal REPL), "
                    "'script' (a `.py` run), or "
                    "'interactive' (bare `python` / `-i` / `-c`). "
                    "See scitex_io._utils.detect_environment for the "
                    "canonical contract. Refusing to guess an output "
                    "directory."
                )

        spath_final = clean(spath)
        ########################################

        spath_cwd = _os.getcwd() + "/" + specified_path
        # scitex-io#55: spath_cwd is the LITERAL location of the cwd
        # anchor symlink we're about to (re)create — it must NOT be
        # collapsed to whatever the existing symlink currently points
        # to. ``clean()`` did ``Path.resolve()`` here, which on a second
        # save() call followed call-1's symlink, silently shifted the
        # anchor onto the target file, and made the subsequent rm
        # delete the just-written artefact. Use ``normpath`` so the
        # anchor stays where the caller asked for it.
        spath_cwd = _os.path.normpath(spath_cwd)
        # Defensive cleanup: if a previous (pre-fix) run left a broken
        # or self-looping symlink at the anchor, remove it now so the
        # downstream ``rm -f`` / ``ln -sfr`` aren't forced to interact
        # with a path that ``Path.resolve()`` would refuse to follow.
        if _os.path.islink(spath_cwd):
            try:
                _os.stat(spath_cwd)  # follow → raises on loop/broken
            except OSError:
                _os.unlink(spath_cwd)

        should_skip_deletion = spath_final.endswith(".csv") or (
            (spath_final.endswith(".hdf5") or spath_final.endswith(".h5"))
            and "key" in kwargs
        )

        if not should_skip_deletion:
            for path in [spath_final, spath_cwd]:
                sh(["rm", "-f", f"{path}"], verbose=False)

        if dry_run:
            try:
                rel_path = _os.path.relpath(spath, _os.getcwd())
            except ValueError:
                rel_path = spath
            if verbose:
                print()
                logger.success(
                    color_text(f"(dry run) Saved to: ./{rel_path}", "yellow")
                )
            return

        if makedirs:
            _os.makedirs(_os.path.dirname(spath_final), exist_ok=True)

        _save(
            obj,
            spath_final,
            verbose=verbose,
            symlink_from_cwd=symlink_from_cwd,
            symlink_to=symlink_to,
            dry_run=dry_run,
            no_csv=no_csv,
            **kwargs,
        )

        _symlink(spath, spath_cwd, symlink_from_cwd, verbose, spath_final=spath_final)
        _symlink_to(spath_final, symlink_to, verbose)
        saved_path = Path(spath)
        # Notify any registered observers (clew, audit, …). See _hooks.
        # Observers SELF-REGISTER on their own import — scitex_io never
        # names them. Hooks never raise (best-effort fan-out).
        from ._observers import fire_post_save

        # Re-attach ``track`` so observers (clew) can honour it. It was
        # popped above to keep it out of the format handlers.
        fire_post_save(saved_path, obj, {**kwargs, "track": track})
        return saved_path

    except Exception as e:
        # Fail loud, fail early. Previously this branch logged the error
        # and returned False, which let callers proceed as though the
        # file had been written — downstream code then exploded much
        # later (or, worse, kept running with stale/missing data and
        # silently produced wrong results).
        #
        # Concrete real-world incident (paper-scitex-clew TRANSLATION
        # _TEMPLATE rollout, 2026-06-01): on a WSL2 Ubuntu 22.04
        # minimal container without libglib2 installed, every
        # scitex_io.save() call raised
        # `libgthread-2.0.so.0: cannot open shared object file` deep in
        # an optional handler import. The old `return False` swallowed
        # the ImportError, the agent's stage 1 logged "saved metrics.csv
        # with 8 rows", and stage 2 then crashed with FileNotFoundError
        # — three stages later than the actual fault. With the raise
        # below the ImportError surfaces at the save call site, with
        # the spath / specified_path debug trail intact.
        logger.error(
            f"scitex_io.save failed for {specified_path!r}: {e}\n"
            f"  Initial script_path = {inspect.stack()[1].filename}\n"
            f"  Final spath = {spath}\n"
            f"  specified_path type = {type(specified_path)}"
        )
        raise


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
    """Dispatch save to the appropriate handler based on file extension."""
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
        handler = get_saver(ext)
        if handler is None:
            raise ValueError(
                f"No save handler registered for '{ext}'. "
                f"Use register_saver('{ext}', your_fn) to add one."
            )
        handler(obj, spath, **kwargs)

    if verbose:
        if _os.path.exists(spath):
            file_size = readable_bytes(getsize(spath))
            try:
                rel_path = _os.path.relpath(spath, _os.getcwd())
            except ValueError:
                rel_path = spath
            print()
            logger.success(f"Saved to: ./{rel_path} ({file_size})")


# EOF
