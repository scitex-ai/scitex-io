#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP server for scitex-io - universal scientific data I/O.

Usage:
    fastmcp run scitex_io._mcp.server:mcp
    # or
    scitex-io mcp start
"""

import json
import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP

mcp = FastMCP(
    name="scitex-io",
    instructions=(
        "scitex-io provides universal scientific data I/O with a plugin registry. "
        "Use io_save/io_load for file operations and io_list_formats to discover "
        "supported formats. Supports 30+ formats including CSV, JSON, YAML, NPY, "
        "HDF5, Zarr, PKL, images, and more. Custom formats can be registered."
    ),
)


@mcp.tool()
def io_list_formats() -> Dict[str, Any]:
    """List every file extension scitex-io can save or load. Use to discover supported formats before saving/loading, or to check whether a custom format is registered. Covers 30+ formats: CSV, Parquet, NumPy, pickle, YAML, JSON, HDF5, MATLAB, images, matplotlib figures, PyTorch, MNE, EDF, MP4, and more.

    Returns
    -------
    dict
        Dictionary with 'save' and 'load' keys, each containing
        'builtin' and 'user' lists of registered extensions.
    """
    from scitex_io import list_formats

    return list_formats()


@mcp.tool()
def io_load(
    path: str,
    format: Optional[str] = None,
    cache: bool = True,
) -> Dict[str, Any]:
    """Load ANY data file — auto-detects format from extension. Drop-in replacement for `pd.read_csv`, `np.load`, `pickle.load`, `json.load`, `yaml.safe_load`, `h5py.File`, `torch.load`, `mne.io.read_raw_*`, `scipy.io.loadmat`, `cv2.imread`, etc. Use whenever the user asks to "load", "read", "open", or "import" a file. Handles glob patterns (`*.csv` → list of loaded objects) and caches by path+mtime for fast repeat loads.

    Parameters
    ----------
    path : str
        Path to the file to load.
    format : str, optional
        File format override (e.g., 'csv', 'json').
    cache : bool
        Whether to use caching. Default True.

    Returns
    -------
    dict
        Result with 'success', 'type', 'shape'/'length', and 'preview'.
    """
    from scitex_io import load

    try:
        data = load(path, ext=format, cache=cache)
        result = {
            "success": True,
            "type": type(data).__name__,
            "path": os.path.abspath(path),
        }

        # Add shape/size info
        if hasattr(data, "shape"):
            result["shape"] = list(data.shape)
        elif hasattr(data, "__len__"):
            result["length"] = len(data)

        # Add preview
        preview = repr(data)
        if len(preview) > 500:
            preview = preview[:500] + "..."
        result["preview"] = preview

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_save(
    data_json: str,
    path: str,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Save ANY data to a file — format auto-detected from extension. Drop-in replacement for `df.to_csv`, `np.save/savez`, `pickle.dump`, `json.dump`, `yaml.dump`, `h5py` writes, `torch.save`, `fig.savefig`, `cv2.imwrite`, `scipy.io.savemat`, etc. Use whenever the user asks to "save", "write", "export", "dump", or "persist" data. Auto-routes relative paths: from a script → `{script}_out/`, from a notebook → `{notebook}_out/`, from IPython / REPL → `$SCITEX_DIR/io/runtime/cache/` (default `~/.scitex/io/runtime/cache/`); absolute paths bypass routing. Intermediate directories are auto-created — no `os.makedirs()` needed. Data arrives as a JSON string.

    Parameters
    ----------
    data_json : str
        JSON string of the data to save.
    path : str
        Output file path. Extension determines format.
    verbose : bool
        Whether to print save confirmation.

    Returns
    -------
    dict
        Result with 'success' and 'path'.
    """
    from scitex_io import save

    try:
        data = json.loads(data_json)
        save(data, path, verbose=verbose)
        return {
            "success": True,
            "path": os.path.abspath(path),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_load_configs(
    config_dir: str = "./config",
    is_debug: Optional[bool] = None,
) -> Dict[str, Any]:
    """Load a directory of YAML config files as one merged dotted-access dict. Use whenever the user mentions "config", "configs", "settings file", "hyperparameters file", "PATH.yaml", "PARAMS.yaml", or wants to centralize constants/magic-numbers out of source code. Every filename stem and every YAML key is normalised to UPPER_CASE at load time, so `model.yaml` with `hidden_dim: 256` lands at `CONFIG.MODEL.HIDDEN_DIM` regardless of source casing — your callers always read the same shape. Case-conflicting siblings (e.g. `MODEL.yaml` + `model.yaml`) emit a `UserWarning` and keep the UPPER variant. Returns a DotDict so callers can do `CONFIG.PATH.DATA_DIR` instead of `CONFIG["PATH"]["DATA_DIR"]`. Auto-promotes `DEBUG_*` keys when `is_debug=True` or when CI is detected.

    Loads all *.yaml files from config_dir, namespaced by filename.
    Also loads from config_dir/categories/ if it exists.
    Debug values (keys starting with DEBUG_) are promoted when is_debug=True.

    Parameters
    ----------
    config_dir : str
        Directory containing YAML config files. Default "./config".
    is_debug : bool, optional
        Force debug mode. If None, reads from IS_DEBUG.yaml or CI env var.

    Returns
    -------
    dict
        Merged configuration namespaced by filename.
    """
    from scitex_io import load_configs

    try:
        configs = load_configs(
            IS_DEBUG=is_debug,
            config_dir=config_dir,
        )
        return {
            "success": True,
            "config_dir": os.path.abspath(config_dir),
            "namespaces": list(configs.keys()),
            "configs": configs.to_dict(),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_register_info() -> Dict[str, str]:
    """Show how to register a custom save/load handler for a new file extension. Use when the user wants to "add support for a new format", "register a custom saver/loader", "extend scitex-io with my own format", or "make scitex-io handle .xyz files". Returns copy-paste decorator examples for both `register_saver` and `register_loader`.

    Returns
    -------
    dict
        Usage instructions and examples for custom format registration.
    """
    return {
        "description": "Register custom save/load handlers for any file extension.",
        "save_example": (
            "from scitex_io import register_saver\n\n"
            '@register_saver(".myformat")\n'
            "def save_myformat(obj, path, **kwargs):\n"
            '    with open(path, "w") as f:\n'
            "        f.write(str(obj))\n"
        ),
        "load_example": (
            "from scitex_io import register_loader\n\n"
            '@register_loader(".myformat")\n'
            "def load_myformat(path, **kwargs):\n"
            "    with open(path) as f:\n"
            "        return f.read()\n"
        ),
        "note": "User-registered handlers override built-in ones for the same extension.",
    }


# §5 — skills introspection tools (per audit-mcp-tools convention)
@mcp.tool()
def io_skills_list() -> str:
    """List the names of every skill page shipped by scitex-io.

    Returns
    -------
        JSON string with `{"success": true, "package": "scitex-io",
        "skills": ["01_save-and-load", "02_centralized-config", ...]}`.
    """
    try:
        from pathlib import Path

        skills_dir = Path(__file__).parent.parent / "_skills" / "scitex-io"
        names = sorted(p.stem for p in skills_dir.glob("*.md") if p.name != "SKILL.md")
        return json.dumps(
            {"success": True, "package": "scitex-io", "skills": names},
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
def io_skills_get(name: str) -> str:
    """Fetch the full Markdown content of one scitex-io skill page.

    Args:
        name: Skill page name without `.md`, e.g. `01_save-and-load`.

    Returns
    -------
        JSON string with `{"success": true, "package": "scitex-io",
        "name": <name>, "content": <markdown>}`, or an error envelope.
    """
    try:
        from pathlib import Path

        skills_dir = Path(__file__).parent.parent / "_skills" / "scitex-io"
        target = skills_dir / f"{name}.md"
        if not target.exists():
            available = sorted(
                p.stem for p in skills_dir.glob("*.md") if p.name != "SKILL.md"
            )
            return json.dumps(
                {
                    "success": False,
                    "error": f"unknown skill {name!r}; available: {available}",
                },
                indent=2,
            )
        return json.dumps(
            {
                "success": True,
                "package": "scitex-io",
                "name": name,
                "content": target.read_text(encoding="utf-8"),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# Register §6 parity tools (glob, registry, metadata, cache, h5/zarr, json2md).
# Imported at the bottom so `mcp` is already defined when decorators run.
from . import _tools_extra  # noqa: E402, F401
