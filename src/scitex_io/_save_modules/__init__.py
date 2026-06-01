#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save handler submodules for ``scitex_io.save``.

Each ``_save_modules._<format>`` submodule defines a ``save_<format>`` /
``_save_<format>`` callable. The eager re-exports that used to live at
the top of this module triggered transitive imports of PIL, pyarrow,
h5py, scipy, plotly, bibtexparser, etc. on every ``import scitex_io`` —
fixed by switching to per-extension lazy registration (see
``scitex_io._builtin_handlers._LAZY_SAVERS``).

The handful of public names previously exposed here (``save_image``,
``save_csv``, …) are still resolvable for backward compatibility via
PEP 562 ``__getattr__`` — they import on first access. Code that needs
a specific handler should prefer the explicit submodule import
(``from scitex_io._save_modules._image import save_image``) to avoid the
attribute-resolution detour entirely.
"""

from __future__ import annotations

import importlib as _importlib
import warnings as _warnings

# Public-name → (submodule_path, attr_in_submodule). Kept in sync with
# ``_builtin_handlers._SAVER_ATTRS`` and the historic ``__all__`` so that
# ``from scitex_io._save_modules import save_image`` still works without
# importing every other handler.
_LAZY_NAMES: dict[str, tuple[str, str]] = {
    "save_csv": ("scitex_io._save_modules._csv", "_save_csv"),
    "save_excel": ("scitex_io._save_modules._excel", "save_excel"),
    "save_npy": ("scitex_io._save_modules._numpy", "_save_npy"),
    "save_npz": ("scitex_io._save_modules._numpy", "_save_npz"),
    "save_pickle": ("scitex_io._save_modules._pickle", "_save_pickle"),
    "save_pickle_compressed": (
        "scitex_io._save_modules._pickle",
        "_save_pickle_gz",
    ),
    "save_joblib": ("scitex_io._save_modules._joblib", "_save_joblib"),
    "save_torch": ("scitex_io._save_modules._torch", "_save_torch"),
    "save_json": ("scitex_io._save_modules._json", "_save_json"),
    "save_yaml": ("scitex_io._save_modules._yaml", "_save_yaml"),
    "save_hdf5": ("scitex_io._save_modules._hdf5", "_save_hdf5"),
    "save_matlab": ("scitex_io._save_modules._matlab", "_save_matlab"),
    "save_catboost": ("scitex_io._save_modules._catboost", "_save_catboost"),
    "save_text": ("scitex_io._save_modules._text", "_save_text"),
    "save_tex": ("scitex_io._save_modules._tex", "save_tex"),
    "save_html": ("scitex_io._save_modules._html", "save_html"),
    "save_image": ("scitex_io._save_modules._image", "save_image"),
    "save_mp4": ("scitex_io._save_modules._mp4", "_mk_mp4"),
    "save_zarr": ("scitex_io._save_modules._zarr", "_save_zarr"),
    "save_bibtex": ("scitex_io._save_modules._bibtex", "save_bibtex"),
    "save_listed_dfs_as_csv": (
        "scitex_io._save_modules._listed_dfs_as_csv",
        "_save_listed_dfs_as_csv",
    ),
    "save_listed_scalars_as_csv": (
        "scitex_io._save_modules._listed_scalars_as_csv",
        "_save_listed_scalars_as_csv",
    ),
    "save_optuna_study_as_csv_and_pngs": (
        "scitex_io._save_modules._optuna_study_as_csv_and_pngs",
        "save_optuna_study_as_csv_and_pngs",
    ),
}

__all__ = list(_LAZY_NAMES)


def __getattr__(name: str):
    """Resolve a save-handler attribute on first access (PEP 562).

    Missing optional dependencies are surfaced as ``None`` with an
    ``ImportWarning`` — the same shape the historic eager
    ``try_import_optional`` block produced, just deferred to first use.
    """
    spec = _LAZY_NAMES.get(name)
    if spec is None:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        )
    module_path, attr_name = spec
    try:
        module = _importlib.import_module(module_path)
        value = getattr(module, attr_name, None)
        if value is None:
            raise ImportError(
                f"module {module_path!r} has no attribute {attr_name!r}"
            )
    except Exception as exc:
        _warnings.warn(
            f"scitex_io: {name} not available "
            f"(missing optional dependency: {exc})",
            ImportWarning,
            stacklevel=2,
        )
        value = None
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(_LAZY_NAMES) | set(globals()))


# EOF
