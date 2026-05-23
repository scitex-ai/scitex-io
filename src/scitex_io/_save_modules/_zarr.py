#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-07-11 15:44:00 (ywatanabe)"
# File: /ssh:sp:/home/ywatanabe/proj/scitex_repo/src/scitex/io/_save_modules/_zarr.py
# ----------------------------------------
import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
# src/scitex/io/_save_modules/_zarr.py
from typing import Any, Optional

import numpy as np
import zarr

# Zarr v3 deprecated direct numcodecs codecs in `Group.create_array`;
# use zarr's modern codec classes instead.
from zarr.codecs import GzipCodec, ZstdCodec  # noqa: E402


def _save_zarr(
    obj: Any,
    spath: str,
    key: Optional[str] = None,
    compressor="zstd",
    chunks=True,
    store_type="auto",
    consolidate_metadata=False,
    **kwargs,
):
    """
    Save object to Zarr format with automatic chunking and compression.

    Parameters:
    -----------
    obj : Any
        Object to save (dict, array, etc.)
    spath : str
        Path to Zarr store (.zarr extension or .zarr.zip)
    key : str, optional
        Key/group path within Zarr store
    compressor : str
        Compression algorithm ('zstd', 'lz4', 'gzip')
    chunks : bool or tuple
        Chunking strategy
    store_type : str
        'auto' (detect from extension), 'directory', or 'zip'
    consolidate_metadata : bool
        Consolidate metadata to reduce file count (directory stores only)
    """
    # Convert to dict if needed
    if not isinstance(obj, dict):
        obj = {"data": obj}

    # Determine store type
    if store_type == "auto":
        if spath.endswith(".zip") or spath.endswith(".zarr.zip"):
            store_type = "zip"
        else:
            store_type = "directory"

    # Create appropriate store
    if store_type == "zip":
        # Single file ZIP store. Zarr v3 moved this to zarr.storage.
        from zarr.storage import ZipStore

        store = ZipStore(spath, mode="w")
        root = zarr.open(store, mode="w")
    else:
        # Directory store
        # Remove file if it exists (tempfile creates files, but zarr needs directories)
        if os.path.exists(spath) and not os.path.isdir(spath):
            os.remove(spath)

        # Open or create Zarr store
        try:
            root = zarr.open(spath, mode="a")
        except:
            root = zarr.open(spath, mode="w")

    # Handle compressor configuration — zarr v3 accepts a list of
    # zarr.codecs.* instances on `create_array(..., compressors=[...])`.
    # We map our friendly string names; unknown names fall back to zstd.
    # lz4 has no native zarr v3 codec class — alias to zstd.
    if isinstance(compressor, str):
        compressor_map = {
            "zstd": [ZstdCodec(level=3)],
            "lz4": [ZstdCodec(level=1)],
            "gzip": [GzipCodec(level=5)],
        }
        compressor = compressor_map.get(compressor.lower(), [ZstdCodec(level=3)])

    # Navigate to target group
    if key:
        # Create nested groups as needed
        parts = [p for p in key.split("/") if p]
        current_group = root

        for part in parts[:-1]:
            if part not in current_group:
                current_group = current_group.create_group(part)
            else:
                current_group = current_group[part]

        final_key = parts[-1] if parts else ""
        if final_key:
            if final_key in current_group:
                del current_group[final_key]  # Override
            target_group = current_group.create_group(final_key)
        else:
            target_group = current_group
    else:
        target_group = root

    # Save datasets. Zarr v3 deprecated `Group.create_dataset` in favour
    # of `Group.create_array`. Use create_array with explicit shape/
    # dtype derived from the input array — that's the new contract.
    def _create(group, name, data, **kw):
        return group.create_array(name, shape=data.shape, dtype=data.dtype, **kw)

    for dataset_name, data in obj.items():
        if isinstance(data, str):
            # String data — no compression.
            arr = np.array(data)
            ds = _create(target_group, dataset_name, arr, compressors=None)
            ds[...] = arr
        elif isinstance(data, (int, float, bool)):
            # Scalar — wrap in 0-d array.
            arr = np.array(data)
            ds = _create(target_group, dataset_name, arr)
            ds[...] = arr
        else:
            # Array data
            data_array = np.asarray(data)

            if data_array.dtype == np.object_:
                # Complex objects — pickle them.
                import pickle

                pickled_data = pickle.dumps(data)
                arr = np.frombuffer(pickled_data, dtype=np.uint8)
                ds = _create(
                    target_group,
                    dataset_name,
                    arr,
                    compressors=compressor,
                )
                ds[...] = arr
                ds.attrs["_type"] = "pickled"
            else:
                # Regular array data. Zarr v3 wants `chunks` either as
                # a concrete tuple or the literal "auto" — convert
                # legacy `chunks=True` to "auto".
                z_chunks = "auto" if chunks is True else chunks
                ds = _create(
                    target_group,
                    dataset_name,
                    data_array,
                    chunks=z_chunks,
                    compressors=compressor,
                    **kwargs,
                )
                ds[...] = data_array

    # Close ZIP store if needed
    if store_type == "zip":
        store.close()

    # Consolidate metadata if requested (directory stores only)
    if store_type == "directory" and consolidate_metadata:
        try:
            zarr.consolidate_metadata(spath)
            print(
                f"✅ Saved to Zarr (consolidated): {spath}" + (f"/{key}" if key else "")
            )
        except:
            print(f"✅ Saved to Zarr: {spath}" + (f"/{key}" if key else ""))
    else:
        print(f"✅ Saved to Zarr ({store_type}): {spath}" + (f"/{key}" if key else ""))


# EOF
