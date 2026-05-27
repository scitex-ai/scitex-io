#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scitex-io — Universal scientific data I/O with plugin registry.

Functionalities
---------------
- `save(obj, "path.ext")` / `load("path.ext")` — extension-dispatched
  one-call I/O for 30+ formats (CSV, Parquet, Feather, NumPy,
  pickle, YAML, JSON, HDF5, Zarr, MATLAB, images, matplotlib figures,
  PyTorch, MNE, EDF, video).
- `register_saver(".ext")` / `register_loader(".ext")` — plugin hooks
  for user-defined formats; dispatch lookup follows the same registry.
- `load_configs()` — collect every `<project-root>/config/*.yaml` into
  a single ``DotDict`` with ``UPPER_CASE`` normalisation + ``DEBUG_`` overrides.
- `glob` / `parse_glob` — natural-sorted globbing with `{placeholder}`
  parsing; `cache` / `reload` / `flush` — load-cache management.

IO
--
- Reads: any registered extension; `./config/*.yaml`; `$SCITEX_DIR`
  cache; figure metadata (PNG tEXt, JPEG EXIF, SVG XML, PDF XMP).
- Writes: relative paths resolve under `{caller}_out/` (script /
  notebook) or `$SCITEX_DIR/io/runtime/cache/` (REPL); absolute paths
  pass through unchanged.

Dependencies
------------
- Hard: `tqdm`, `PyYAML`, `ruamel.yaml`, `mne`, `numpy`, `pandas`,
  `click`, `rich`, `natsort`, `scitex-dev`, `scitex-logging`.
- Optional (`[scientific]`): `scipy`, `h5py`, `zarr>=3`, `numcodecs`,
  `matplotlib`. (`[mcp]`): `fastmcp`.

Register custom handlers::

    from scitex_io import register_saver, register_loader

    @register_saver(".myformat")
    def save_myformat(obj, path, **kw): ...

    @register_loader(".myformat")
    def load_myformat(path, **kw): ...

Top-level imports are PEP 562 lazy — `import scitex_io` is cheap.
Public symbols load on first attribute access. See
`_skills/general/03_interface_01_python-api/04_lazy-imports-and-optional-deps.md`.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
try:
    from importlib.metadata import PackageNotFoundError
    from importlib.metadata import version as _v

    try:
        __version__ = _v("scitex-io")
    except PackageNotFoundError:
        __version__ = "0.0.0+local"
    del _v, PackageNotFoundError
except ImportError:  # pragma: no cover — only on ancient Pythons
    __version__ = "0.0.0+local"


# ---------------------------------------------------------------------------
# PEP 562 lazy attribute map: public-name → submodule (relative).
# Keep the LHS == the public symbol, the RHS == the submodule that defines it.
# ---------------------------------------------------------------------------
_LAZY_ATTRS: dict[str, str] = {
    # Registry API
    "register_saver": "._registry",
    "register_loader": "._registry",
    "get_saver": "._registry",
    "get_loader": "._registry",
    "list_formats": "._registry",
    "unregister_saver": "._registry",
    "unregister_loader": "._registry",
    # Core I/O
    "save": "._save",
    "load": "._loading",
    "load_configs": "._loading",
    "glob": "._glob",
    "parse_glob": "._glob",
    "reload": "._reload",
    "flush": "._flush",
    "cache": "._cache",
    # Cache control
    "configure_cache": "._loading",
    "get_cache_info": "._loading",
    "clear_load_cache": "._loading",  # aliased below
    # Dict utilities
    "DotDict": "._utils",
}

# Optional public names that may not be importable. Resolve once, lazily.
_OPTIONAL_ATTRS: dict[str, tuple[str, str]] = {
    # name: (relative_module, attr_name_in_module)
    "H5Explorer": ("._load_modules._H5Explorer", "H5Explorer"),
    "explore_h5": ("._load_modules._H5Explorer", "explore_h5"),
    "has_h5_key": ("._load_modules._H5Explorer", "has_h5_key"),
    "ZarrExplorer": ("._load_modules._ZarrExplorer", "ZarrExplorer"),
    "explore_zarr": ("._load_modules._ZarrExplorer", "explore_zarr"),
    "has_zarr_key": ("._load_modules._ZarrExplorer", "has_zarr_key"),
    "save_image": ("._save_modules", "save_image"),
    "save_text": ("._save_modules", "save_text"),
    "save_mp4": ("._save_modules", "save_mp4"),
    "save_listed_dfs_as_csv": ("._save_modules", "save_listed_dfs_as_csv"),
    "save_listed_scalars_as_csv": ("._save_modules", "save_listed_scalars_as_csv"),
    "save_optuna_study_as_csv_and_pngs": (
        "._save_modules",
        "save_optuna_study_as_csv_and_pngs",
    ),
    "path": ("._path", "path"),
    "mv_to_tmp": ("._mv_to_tmp", "mv_to_tmp"),
    "json2md": ("._json2md", "json2md"),
    "migrate_h5_to_zarr": ("utils", "migrate_h5_to_zarr"),
    "migrate_h5_to_zarr_batch": ("utils", "migrate_h5_to_zarr_batch"),
    "embed_metadata": ("._metadata", "embed_metadata"),
    "read_metadata": ("._metadata", "read_metadata"),
    "has_metadata": ("._metadata", "has_metadata"),
}


def _load_lazy_attr(name: str):
    """Resolve a `_LAZY_ATTRS` name and cache it."""
    from importlib import import_module

    mod_name = _LAZY_ATTRS.get(name)
    if mod_name is None:
        return None
    mod = import_module(mod_name, __name__)
    # Special-case alias: clear_load_cache = clear_cache
    if name == "clear_load_cache":
        attr = getattr(mod, "clear_cache")
    else:
        attr = getattr(mod, name)
    # Optionally wrap with @supports_return_as for the documented core APIs.
    if name in {"save", "load", "load_configs", "list_formats"}:
        try:
            from scitex_dev import supports_return_as as _wrap

            attr = _wrap(attr)
        except ImportError:
            pass
    globals()[name] = attr
    return attr


def _load_optional_attr(name: str):
    """Resolve an `_OPTIONAL_ATTRS` name and cache it (None on failure)."""
    from importlib import import_module

    spec = _OPTIONAL_ATTRS.get(name)
    if spec is None:
        return None
    mod_name, attr_name = spec
    try:
        mod = import_module(mod_name, __name__)
        attr = getattr(mod, attr_name, None)
    except ImportError:
        attr = None
    globals()[name] = attr
    return attr


def _ensure_builtin_handlers_registered() -> None:
    """Trigger built-in handler registration (idempotent)."""
    if globals().get("_BUILTINS_REGISTERED"):
        return
    from importlib import import_module

    import_module("._builtin_handlers", __name__)
    # Optional ecosystem providers (e.g. figrecipe) contribute extra
    # formats when their package is installed — a no-op otherwise.
    from ._optional_providers import register_optional_providers

    register_optional_providers()
    globals()["_BUILTINS_REGISTERED"] = True


def __getattr__(name: str):
    """PEP 562 lazy-loader: import on first access, cache, return."""
    # Built-in handlers must be registered before any registry-facing call.
    if name in _LAZY_ATTRS or name in _OPTIONAL_ATTRS:
        _ensure_builtin_handlers_registered()
    if name in _LAZY_ATTRS:
        return _load_lazy_attr(name)
    if name in _OPTIONAL_ATTRS:
        return _load_optional_attr(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(_LAZY_ATTRS) | set(_OPTIONAL_ATTRS) | set(globals()))


__all__ = [
    "__version__",
    *_LAZY_ATTRS.keys(),
    *_OPTIONAL_ATTRS.keys(),
]
