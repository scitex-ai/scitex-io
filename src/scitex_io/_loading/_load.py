#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-11 05:54:51 (ywatanabe)"
# File: /home/ywatanabe/proj/SciTeX-Code/src/scitex/io/_load.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import contextvars
import glob
from pathlib import Path
from typing import Any, Union

import scitex_logging as slogging

from .._registry import get_loader  # noqa: F401
from ._load_cache import (
    cache_data,
    get_cached_data,
    load_npy_cached,
)

log = slogging.getLogger(__name__)


def load(
    lpath: Union[str, Path],
    ext: str = None,
    show: bool = False,
    verbose: bool = False,
    cache: bool = True,
    **kwargs,
) -> Any:
    """Public wrapper around :func:`_load_impl` that fires post-load hooks.

    Every file that is actually read fires exactly one post-load hook:
    a single-file load fires here; a glob load fires once per matched
    file (the per-file recursion re-enters ``load``) and never for the
    pattern itself. Hooks receive the file's realpath.
    """
    result = _load_impl(
        lpath, ext=ext, show=show, verbose=verbose, cache=cache, **kwargs
    )
    if not _is_glob(lpath):
        from .._observers import fire_post_load

        fire_post_load(Path(lpath), result, {"glob": _GLOB_PATTERN.get()})
        # Identity registry so ``save(..., derived_from=[result])`` can name
        # this file by handing back the object (see _derived_from).
        from .._derived_from import register_loaded

        register_loaded(result, os.path.realpath(str(lpath)))
    return result


_GLOB_PATTERN: contextvars.ContextVar = contextvars.ContextVar(
    "scitex_io_glob_pattern", default=None
)


def _is_glob(lpath) -> bool:
    """Glob iff it has glob metacharacters AND is not an existing literal path.

    A literal file named ``a[1].csv`` must load as itself (and fire its
    hook) rather than be expanded as a character class matching nothing.
    """
    s = str(lpath)
    return any(c in s for c in "*?[") and not os.path.lexists(s)


def _load_impl(
    lpath: Union[str, Path],
    ext: str = None,
    show: bool = False,
    verbose: bool = False,
    cache: bool = True,
    **kwargs,
) -> Any:
    """
    Load data from various file formats.

    This function supports loading data from multiple file formats with optional caching.

    Parameters
    ----------
    lpath : Union[str, Path]
        The path to the file to be loaded. Can be a string or pathlib.Path object.
    ext : str, optional
        File extension to use for loading. If None, automatically detects from filename.
        Useful for files without extensions (e.g., UUID-named files).
        Examples: 'pdf', 'json', 'csv'
    show : bool, optional
        If True, display additional information during loading. Default is False.
    verbose : bool, optional
        If True, print verbose output during loading. Default is False.
    cache : bool, optional
        If True, enable caching for faster repeated loads. Default is True.
    **kwargs : dict
        Additional keyword arguments to be passed to the specific loading function.

    Returns
    -------
    object
        The loaded data object, which can be of various types depending on the input file format.

    Raises
    ------
    ValueError
        If the file extension is not supported.
    FileNotFoundError
        If the specified file does not exist.

    Supported Extensions
    -------------------
    - Data formats: .csv, .tsv, .xls, .xlsx, .xlsm, .xlsb, .json, .yaml, .yml
    - Scientific: .npy, .npz, .mat, .hdf5, .con
    - ML/DL: .pth, .pt, .cbm, .joblib, .pkl
    - Documents: .txt, .log, .event, .md, .docx, .pdf, .xml
    - Images: .jpg, .png, .tiff, .tif
    - EEG data: .vhdr, .vmrk, .edf, .bdf, .gdf, .cnt, .egi, .eeg, .set
    - Database: .db

    Examples
    --------
    >>> data = load('data.csv')
    >>> image = load('image.png')
    >>> model = load('model.pth')
    >>> # Load file without extension (e.g., UUID PDF)
    >>> pdf = load('f2694ccb-1b6f-4994-add8-5111fd4d52f1', ext='pdf')
    """

    # Don't use clean_path as it breaks relative paths like ./file.txt
    # lpath = clean_path(lpath)

    # Convert Path objects to strings for consistency
    if isinstance(lpath, Path):
        lpath = str(lpath)
        if verbose:
            log.debug(f"[DEBUG] After Path conversion: {lpath}")

    # Check if it's a glob pattern
    if _is_glob(lpath):
        # Handle glob pattern
        matched_files = sorted(glob.glob(lpath))
        if not matched_files:
            raise FileNotFoundError(f"No files found matching pattern: {lpath}")
        # Load all matched files; each re-enters load() and fires its own
        # post-load hook, tagged with the originating pattern.
        results = []
        token = _GLOB_PATTERN.set(lpath)
        try:
            for file_path in matched_files:
                results.append(
                    load(
                        file_path,
                        ext=ext,
                        show=show,
                        verbose=verbose,
                        cache=cache,
                        **kwargs,
                    )
                )
        finally:
            _GLOB_PATTERN.reset(token)
        return results

    # Handle broken symlinks - os.path.exists() returns False for broken symlinks
    if not os.path.exists(lpath):
        if os.path.islink(lpath):
            # For symlinks, resolve the target path relative to symlink's directory
            symlink_dir = os.path.dirname(os.path.abspath(lpath))
            target = os.readlink(lpath)
            resolved_target = os.path.join(symlink_dir, target)
            resolved_target = os.path.abspath(resolved_target)

            if os.path.exists(resolved_target):
                lpath = resolved_target
            else:
                raise FileNotFoundError(f"Symlink target not found: {resolved_target}")
        else:
            # Try general path resolution
            try:
                resolved_path = os.path.realpath(lpath)
                if os.path.exists(resolved_path):
                    lpath = resolved_path
                else:
                    raise FileNotFoundError(f"File not found: {lpath}")
            except Exception:
                raise FileNotFoundError(f"File not found: {lpath}")

    # Try to get from cache first
    if cache:
        cached_data = get_cached_data(lpath)
        if cached_data is not None:
            if verbose:
                log.info(f"[Cache HIT] Loaded from cache: {lpath}")
            return cached_data

    # Determine extension: use explicit ext parameter or detect from filename
    compound_ext = None
    if ext is not None:
        detected_ext = ext.lstrip(".")
    else:
        # Compound extensions contributed by optional providers (e.g.
        # figrecipe's .fig.zip / .plt.zip) take precedence over the bare
        # last-segment extension.
        from .._optional_providers import OPTIONAL_COMPOUND_EXTS

        _lpath_lower = lpath.lower()
        for _compound in OPTIONAL_COMPOUND_EXTS:
            if _lpath_lower.endswith(_compound):
                compound_ext = _compound
                break
        detected_ext = lpath.split(".")[-1] if "." in lpath else ""

    # Special handling for numpy files with caching
    if cache and detected_ext in ["npy", "npz"]:
        return load_npy_cached(lpath, **kwargs)

    # Registry lookup (normalized with dot). Compound exts win.
    if compound_ext is not None:
        loader = get_loader(compound_ext)
    else:
        loader = get_loader(f".{detected_ext}" if detected_ext else "")
    if loader is None:
        raise ValueError(
            f"No load handler registered for '.{detected_ext}'.\n"
            f"scitex-io has a pluggable extension registry — register a loader "
            f"for this format, then retry. For example:\n\n"
            f"    from scitex_io import register_loader\n\n"
            f"    @register_loader('.{detected_ext}')\n"
            f"    def _loader(path, **kwargs):\n"
            f"        # import/install whatever runtime this format needs, e.g.\n"
            f"        #   import keras; return keras.models.load_model(path)\n"
            f"        return obj\n\n"
            f"    obj = load(path)   # now dispatches to your loader\n\n"
            f"Inspect built-ins via scitex_io.list_formats(); register_saver() is "
            f"the save-side twin. Direct form: "
            f"register_loader('.{detected_ext}', your_fn)."
        )

    try:
        result = loader(lpath, **kwargs)

        # Cache the result if caching is enabled
        if cache:
            cache_data(lpath, result)
            if verbose:
                log.info(f"[Cache STORED] Cached data for: {lpath}")

        return result
    except (ValueError, FileNotFoundError) as e:
        raise ValueError(f"Error loading file {lpath}: {str(e)}")


# EOF
