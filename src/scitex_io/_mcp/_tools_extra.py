#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Additional MCP tools for scitex-io — Python API ↔ MCP parity (§6).

Imported at the bottom of `server.py` so the `@mcp.tool()` decorators
register against the `FastMCP` instance defined there.
"""

import json
import os
from typing import Any, Dict, Optional

from .server import mcp


@mcp.tool()
def io_glob(
    expression: str, parse: bool = False, ensure_one: bool = False
) -> Dict[str, Any]:
    """Glob filesystem paths with natural sort and optional placeholder parsing. Drop-in upgrade for `glob.glob`/`pathlib.Path.glob` that returns natsort-ordered hits and (with `parse=True`) extracts `{name}` placeholders from each match. Use whenever the user asks to "find files matching", "list files", or wants templated path discovery.

    Parameters
    ----------
    expression : str
        Glob expression (may contain `{placeholder}` segments when `parse=True`).
    parse : bool
        If True, return `(paths, parsed)` with each parsed dict matched to its path.
    ensure_one : bool
        If True, raise unless exactly one match is found.
    """
    from scitex_io import glob

    try:
        return {
            "success": True,
            "result": glob(expression, parse=parse, ensure_one=ensure_one),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_parse_glob(expression: str, ensure_one: bool = False) -> Dict[str, Any]:
    """Parse `{placeholder}` values out of every glob match. Like `io_glob(parse=True)` but returns only the parsed-fields list. Use when the user wants the *values* embedded in matching paths, not the paths themselves.

    Parameters
    ----------
    expression : str
        Glob expression with `{placeholder}` segments.
    ensure_one : bool
        If True, raise unless exactly one match is found.
    """
    from scitex_io import parse_glob

    try:
        return {
            "success": True,
            "parsed": parse_glob(expression, ensure_one=ensure_one),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_get_loader(ext: str) -> Dict[str, Any]:
    """Look up the registered loader for a file extension. Use when the user asks "is .ext supported?" or wants to know which function will handle a given file type. Returns the function's qualified name (or null if no handler is registered).

    Parameters
    ----------
    ext : str
        File extension including dot (e.g. `.parquet`).
    """
    from scitex_io import get_loader

    fn = get_loader(ext)
    return {
        "success": True,
        "ext": ext,
        "loader": f"{fn.__module__}.{fn.__qualname__}" if fn is not None else None,
    }


@mcp.tool()
def io_get_saver(ext: str) -> Dict[str, Any]:
    """Look up the registered saver for a file extension. Mirrors `io_get_loader`. Use to verify whether `io_save(obj, 'foo.ext')` will succeed for a given extension.

    Parameters
    ----------
    ext : str
        File extension including dot (e.g. `.parquet`).
    """
    from scitex_io import get_saver

    fn = get_saver(ext)
    return {
        "success": True,
        "ext": ext,
        "saver": f"{fn.__module__}.{fn.__qualname__}" if fn is not None else None,
    }


@mcp.tool()
def io_read_metadata(image_path: str) -> Dict[str, Any]:
    """Read provenance metadata embedded in an image (PNG/JPEG) by `io_save(fig, …)`. Use when the user asks "where did this figure come from?", "what script produced this PNG?", or wants to inspect figure provenance.

    Parameters
    ----------
    image_path : str
        Path to an image file.
    """
    from scitex_io import read_metadata

    try:
        return {"success": True, "metadata": read_metadata(image_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_has_metadata(image_path: str) -> Dict[str, Any]:
    """Check whether an image file contains scitex-io provenance metadata. Quick yes/no for `io_read_metadata`.

    Parameters
    ----------
    image_path : str
        Path to an image file.
    """
    from scitex_io import has_metadata

    try:
        return {"success": True, "has_metadata": has_metadata(image_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_embed_metadata(image_path: str, metadata_json: str) -> Dict[str, Any]:
    """Embed JSON metadata into an existing image file. Use to backfill provenance into a figure that wasn't saved through `io_save`.

    Parameters
    ----------
    image_path : str
        Path to an image file.
    metadata_json : str
        JSON-encoded metadata dict.
    """
    from scitex_io import embed_metadata

    try:
        embed_metadata(image_path, json.loads(metadata_json))
        return {"success": True, "path": os.path.abspath(image_path)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_get_cache_info() -> Dict[str, Any]:
    """Report current load-cache state (entries, hits, misses, size). Use when the user asks "is caching on?", "how big is the cache?", or wants to debug repeated-load performance."""
    from scitex_io import get_cache_info

    return {"success": True, **get_cache_info()}


@mcp.tool()
def io_clear_load_cache() -> Dict[str, Any]:
    """Drop every entry from the load cache. Use when the user asks to "clear the cache", "force fresh reads", or after files change on disk."""
    from scitex_io import clear_load_cache

    clear_load_cache()
    return {"success": True}


@mcp.tool()
def io_configure_cache(
    enabled: Optional[bool] = None,
    max_size: Optional[int] = None,
    verbose: Optional[bool] = None,
) -> Dict[str, Any]:
    """Enable/disable the load cache or change its capacity. Use when the user asks to "turn off caching", "increase cache size", or wants to tune cache behavior.

    Parameters
    ----------
    enabled : bool, optional
        Toggle caching on/off.
    max_size : int, optional
        Max number of cached objects.
    verbose : bool, optional
        Toggle cache hit/miss logging.
    """
    from scitex_io import configure_cache

    configure_cache(enabled=enabled, max_size=max_size, verbose=verbose)
    return {"success": True}


@mcp.tool()
def io_explore_h5(filepath: str) -> Dict[str, Any]:
    """Print the group/dataset tree of an HDF5 file. Use when the user asks to "explore", "inspect", "show structure of", or "preview" an `.h5/.hdf5` file. Returns success status; the tree is printed to stdout.

    Parameters
    ----------
    filepath : str
        Path to an HDF5 file.
    """
    from scitex_io import explore_h5

    try:
        explore_h5(filepath)
        return {"success": True, "path": os.path.abspath(filepath)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_explore_zarr(storepath: str) -> Dict[str, Any]:
    """Print the group/array tree of a Zarr store. HDF5-equivalent for `.zarr` directories.

    Parameters
    ----------
    storepath : str
        Path to a Zarr store directory.
    """
    from scitex_io import explore_zarr

    try:
        explore_zarr(storepath)
        return {"success": True, "path": os.path.abspath(storepath)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_has_h5_key(h5_path: str, key: str) -> Dict[str, Any]:
    """Check whether an HDF5 file contains a given dataset/group key. Cheaper than opening the whole file.

    Parameters
    ----------
    h5_path : str
        Path to an HDF5 file.
    key : str
        Dataset or group key (slash-delimited).
    """
    from scitex_io import has_h5_key

    try:
        return {"success": True, "has_key": bool(has_h5_key(h5_path, key))}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_has_zarr_key(zarr_path: str, key: str) -> Dict[str, Any]:
    """Check whether a Zarr store contains a given key. Zarr equivalent of `io_has_h5_key`.

    Parameters
    ----------
    zarr_path : str
        Path to a Zarr store directory.
    key : str
        Array or group key.
    """
    from scitex_io import has_zarr_key

    try:
        return {"success": True, "has_key": bool(has_zarr_key(zarr_path, key))}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def io_json2md(json_str: str, level: int = 1) -> Dict[str, Any]:
    """Convert a JSON object/array into Markdown headings + bullet lists. Use when the user asks to "format this JSON as markdown", "render config as docs", or wants a human-readable view of nested data.

    Parameters
    ----------
    json_str : str
        JSON-encoded object.
    level : int
        Starting heading level (1-6).
    """
    from scitex_io import json2md

    try:
        return {"success": True, "markdown": json2md(json.loads(json_str), level=level)}
    except Exception as e:
        return {"success": False, "error": str(e)}
