#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-11 23:54:07 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex_repo/src/scitex/io/_load_configs.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = "./src/scitex/io/_load_configs.py"
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

from pathlib import Path
from typing import Optional, Union

from .._glob import glob
from .._utils import DotDict
from ._load import load


def _normalize_to_upper(d, file=None, path="CONFIG"):
    """Normalize every string key in a config tree to UPPER_CASE.

    Walks a (possibly nested) dict/DotDict in place and renames every
    string key to its ``str.upper()`` form so the loaded config is
    case-stable regardless of how filenames and YAML keys were written.
    Non-string keys (ints, etc.) are left untouched. Lookups on the
    resulting :class:`~scitex_io._utils.DotDict` are case-insensitive
    for string keys, so a YAML mapping written ``{"seizure": "red"}``
    (stored as ``{"SEIZURE": "red"}``) can still be read with the
    lowercase key the author wrote.

    Collision fail-loud
    -------------------
    If two keys *inside one mapping* fold to the same UPPER form (e.g.
    literally both ``"seizure"`` and ``"SEIZURE"``, or a ``MODEL.yaml``
    next to a ``model.yaml`` whose stems collide), this raises a loud
    :class:`ValueError` naming the source file, the mapping path, and
    both offending keys. The collision is detected here, at load time —
    never silently merged, dropped, or deferred to a lookup-time
    surprise.

    Parameters
    ----------
    d : dict | DotDict
        Mapping to normalise in place.
    file : str | None
        Source YAML stem for error messages. ``None`` at the top level,
        where the keys are themselves filename stems; in that case a
        collision message names the config directory rather than a file.
    path : str
        Dotted mapping path used in error messages (e.g.
        ``CONFIG.SEIZURE.STR2COLOR``).
    """
    if not isinstance(d, (dict, DotDict)):
        return d

    by_upper: dict[str, list[str]] = {}
    for k in list(d.keys()):
        if isinstance(k, str):
            by_upper.setdefault(k.upper(), []).append(k)

    # Track the original (pre-normalisation) string key behind each UPPER
    # form so the recursion can name children by the stem the author
    # actually wrote (``m.yaml`` → file 'm', not the folded 'M').
    upper_to_original: dict[str, str] = {}
    for upper, variants in by_upper.items():
        if len(variants) > 1:
            where = f"file {file!r}" if file is not None else "the config directory"
            a, b = variants[0], variants[1]
            raise ValueError(
                f"load_configs: case collision in {where} at mapping "
                f"{path!r}: keys {a!r} and {b!r} both normalise to "
                f"{upper!r}. Rename one of them so the loaded config has "
                f"unambiguous UPPER_CASE keys."
            )
        (only,) = variants
        upper_to_original[upper] = only
        if only != upper:
            d[upper] = d.pop(only)

    for k, v in list(d.items()):
        if isinstance(v, (dict, DotDict)):
            # At the top level, each key is a filename stem; descend with
            # the ORIGINAL stem (what the author named the file) as the
            # source-file context for nested collisions.
            child_file = upper_to_original.get(k, k) if file is None else file
            _normalize_to_upper(v, file=child_file, path=f"{path}.{k}")
    return d


def load_configs(
    IS_DEBUG=None,
    show=False,
    verbose=False,
    config_dir: Optional[Union[str, Path]] = None,
):
    """Load and merge every YAML under ``config_dir`` into one ``DotDict``.

    Filename stems become top-level keys; YAML keys become nested
    attributes. Every string key (filename stem and every nested key)
    is normalised to UPPER_CASE at load time so the in-memory tree is
    case-stable regardless of source casing — ``model.yaml`` with
    ``hidden_dim: 256`` lands at ``CONFIG.MODEL.HIDDEN_DIM``. Lookups on
    the returned ``DotDict`` are case-insensitive for string keys, so
    ``CONFIG.SEIZURE.STR2COLOR["seizure"]`` resolves the stored
    ``"SEIZURE"`` entry — no surprise ``KeyError`` for the lowercase key
    the author wrote (non-string keys are matched exactly).

    If two keys inside one mapping fold to the same UPPER form (e.g.
    ``MODEL.yaml`` next to ``model.yaml``, or ``HIDDEN_DIM`` next to
    ``hidden_dim``, or ``"seizure"`` next to ``"SEIZURE"`` in one
    string-mapping), a loud ``ValueError`` is raised at load time naming
    the source file, the mapping path, and both offending keys. The
    collision is never silently merged or dropped.

    Debug mode promotes any ``DEBUG_<KEY>`` sibling over its non-debug
    counterpart, so a single ``IS_DEBUG.yaml`` flips the whole project
    between production and debug values. Equivalent triggers:
    ``IS_DEBUG.yaml`` with ``IS_DEBUG: true``, the ``IS_DEBUG=True``
    kwarg, or running under ``CI=True``.

    Parameters
    ----------
    IS_DEBUG : bool, optional
        Force debug mode. If ``None`` (default), inferred from
        ``IS_DEBUG.yaml`` inside ``config_dir`` or from the ``CI``
        env var.
    show : bool
        Echo the ``DEBUG_<KEY> -> <KEY>`` substitutions to stdout.
    verbose : bool
        Print detailed information.
    config_dir : Union[str, Path], optional
        Directory containing the YAML files. Defaults to ``"./config"``.

    Returns
    -------
    DotDict
        Merged configuration tree with UPPER_CASE keys throughout.

    Raises
    ------
    ValueError
        If two keys inside one mapping fold to the same UPPER form
        (a case collision). Raised at load time, naming the file, the
        mapping path, and both offending keys.

    Examples
    --------
    >>> CONFIG = load_configs()                       # ./config/*.yaml
    >>> CONFIG.MODEL.HIDDEN_DIM                       # 256
    >>> CONFIG = load_configs(IS_DEBUG=True)
    >>> CONFIG.MODEL.HIDDEN_DIM                       # 32 (DEBUG_ promoted)
    """

    def apply_debug_values(config, IS_DEBUG):
        """Apply debug values if IS_DEBUG is True."""
        if not IS_DEBUG or not isinstance(config, (dict, DotDict)):
            return config

        for key, value in list(config.items()):
            # YAML mapping keys can be non-string (ints, etc.) — e.g.
            # SEIZURE.yaml's INT2STR / INT2COLOR carry literal integer
            # event-code keys. `str.startswith` would raise
            # `AttributeError: 'int' object has no attribute 'startswith'`
            # on those, the outer try in `load_configs` would swallow it
            # as `Error loading configs: ...` and return an empty
            # DotDict — and the user sees the cryptic downstream
            # `'DotDict' object has no attribute 'PAC'`. Only the
            # `DEBUG_<key>` / `debug_<key>` promotion rule applies to
            # strings; non-string keys are silently recursed into when
            # they nest another mapping but never pattern-matched.
            is_debug_prefixed = (
                isinstance(key, str)
                and key.startswith(("DEBUG_", "debug_"))
            )
            if is_debug_prefixed:
                dk_wo_debug_prefix = key.split("_", 1)[1]
                config[dk_wo_debug_prefix] = value
                if show or verbose:
                    print(f"{key} -> {dk_wo_debug_prefix}")
            elif isinstance(value, (dict, DotDict)):
                config[key] = apply_debug_values(value, IS_DEBUG)
        return config

    try:
        # Handle config directory parameter
        if config_dir is None:
            config_dir = "./config"
        elif isinstance(config_dir, Path):
            config_dir = str(config_dir)

        # Set debug mode
        debug_config_path = f"{config_dir}/IS_DEBUG.yaml"
        IS_DEBUG = (
            IS_DEBUG
            or os.getenv("CI") == "True"
            or (
                os.path.exists(debug_config_path)
                and load(debug_config_path).get("IS_DEBUG")
            )
        )

        # Load and merge configs (namespaced by filename)
        CONFIGS = {}

        # Load from main config directory
        config_pattern = f"{config_dir}/*.yaml"
        for lpath in glob(config_pattern):
            if config := load(lpath):
                filename = Path(lpath).stem
                CONFIGS[filename] = apply_debug_values(config, IS_DEBUG)

        # Load from categories subdirectory if it exists
        categories_dir = f"{config_dir}/categories"
        if os.path.exists(categories_dir):
            categories_pattern = f"{categories_dir}/*.yaml"
            for lpath in glob(categories_pattern):
                if config := load(lpath):
                    filename = Path(lpath).stem
                    CONFIGS[filename] = apply_debug_values(config, IS_DEBUG)

        # Normalise every filename-level key (from YAML stem) and every
        # nested string key to UPPER_CASE so the loaded config is
        # case-stable regardless of source casing. A case collision
        # (e.g. MODEL.yaml + model.yaml, HIDDEN_DIM + hidden_dim,
        # "seizure" + "SEIZURE") raises a loud ValueError here.
        _normalize_to_upper(CONFIGS)

        return DotDict(CONFIGS)

    except ValueError:
        # Case collisions are user config errors — fail loud, never
        # swallow into the empty-DotDict fallback below.
        raise
    except Exception as e:
        print(f"Error loading configs: {e}")
        return DotDict({})


# EOF
