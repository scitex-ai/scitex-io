#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Internal helpers for HDF5 to Zarr migration.

Migrated to zarr v3 API:
- ``Group.create_array`` instead of deprecated ``Group.create_dataset``
- ``compressors=[codec]`` instead of ``compressor=codec``
- ``zarr.codecs.ZstdCodec/GzipCodec`` instead of raw numcodecs codecs
"""

import warnings
from typing import Any, Optional, Tuple, Union

import h5py
import numpy as np
import zarr

# zarr v3: BytesBytesCodec instances live in ``zarr.codecs``.
from zarr.codecs import GzipCodec, ZstdCodec

from ._compat import SciTeXIOError, warn_data_loss


def get_zarr_compressor(
    compressor: Optional[Union[str, Any]] = "zstd",
) -> Optional[Any]:
    """Get a zarr v3 compressor list (or None) from a friendly name.

    Returns a *list* of zarr v3 ``BytesBytesCodec`` instances, which is what
    ``Group.create_array(..., compressors=...)`` expects, or ``None`` for
    "no compression", or the input itself if a custom codec object is
    already provided.
    """
    if compressor is None:
        return None

    if not isinstance(compressor, str):
        # Already a codec instance or list — pass through.
        return compressor

    # lz4/blosc have no native zarr v3 codec class — alias to zstd.
    compressor_map = {
        "zstd": [ZstdCodec(level=3)],
        "lz4": [ZstdCodec(level=1)],
        "gzip": [GzipCodec(level=5)],
        "blosc": [ZstdCodec(level=3)],
    }

    return compressor_map.get(compressor.lower(), [ZstdCodec(level=3)])


def infer_chunks(
    shape: Tuple[int, ...], dtype: np.dtype, target_chunk_mb: float = 10.0
) -> Optional[Tuple[int, ...]]:
    """Infer reasonable chunk sizes based on array shape and dtype."""
    if len(shape) == 0:
        return None

    bytes_per_element = dtype.itemsize
    target_elements = (target_chunk_mb * 1024 * 1024) / bytes_per_element

    chunks = []
    remaining_elements = target_elements

    for dim_size in shape:
        if remaining_elements <= 1:
            chunks.append(max(1, dim_size) if dim_size == 0 else 1)
        elif dim_size == 0:
            # Zero-size dimension: chunk size must be at least 1 in zarr.
            chunks.append(1)
        else:
            chunk_dim = min(dim_size, int(remaining_elements))
            chunks.append(max(1, chunk_dim))
            remaining_elements = remaining_elements / max(1, chunk_dim)

    return tuple(chunks)


def copy_h5_attributes(
    h5_obj: Union[h5py.Group, h5py.Dataset],
    zarr_obj: Union[zarr.Group, zarr.Array],
) -> None:
    """Copy attributes from HDF5 object to Zarr object."""
    for key, value in h5_obj.attrs.items():
        try:
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            elif isinstance(value, np.ndarray) and value.dtype.kind == "S":
                value = [v.decode("utf-8", errors="replace") for v in value]
            elif isinstance(value, np.ndarray):
                # zarr v3 attrs require JSON-serialisable values.
                value = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                value = value.item()
            zarr_obj.attrs[key] = value
        except Exception as e:
            warnings.warn(f"Could not copy attribute '{key}': {e}")


def _normalize_chunks(chunks, shape):
    """Translate user-friendly chunk flag to a value zarr v3 accepts.

    zarr v3's ``Group.create_array`` accepts a tuple, the literal "auto",
    or ``None`` (no chunking — single chunk).
    """
    if chunks is True:
        return "auto"
    if chunks is False or chunks is None:
        # No chunking → one chunk for the whole array.
        # zarr v3 rejects 0 in any chunk dim, so clamp zero-length dims to 1.
        if not shape:
            return "auto"
        return tuple(max(1, d) for d in shape)
    return chunks


def migrate_dataset(
    h5_dataset: h5py.Dataset,
    zarr_parent: zarr.Group,
    name: str,
    compressor: Optional[Any],
    chunks: Optional[Union[bool, Tuple[int, ...]]] = True,
    show_progress: bool = False,
) -> Optional[zarr.Array]:
    """Migrate a single HDF5 dataset to Zarr (v3 API)."""
    try:
        _ = h5_dataset.shape
    except Exception as e:
        warnings.warn(f"Skipping corrupted dataset '{name}': {e}")
        return None

    shape = h5_dataset.shape
    dtype = h5_dataset.dtype

    if chunks is True:
        dataset_chunks = infer_chunks(shape, dtype)
    elif chunks is False:
        dataset_chunks = None
    else:
        dataset_chunks = chunks

    if dtype.kind == "O":
        return _migrate_object_dataset(h5_dataset, zarr_parent, name, compressor, shape)

    if show_progress and shape and np.prod(shape) > 1e6:
        print(f"  Migrating large dataset '{name}' {shape} {dtype}...")

    # Translate to zarr v3 chunk argument.
    z_chunks = _normalize_chunks(dataset_chunks if chunks is not True else True, shape)
    if chunks is True and dataset_chunks is not None:
        z_chunks = dataset_chunks  # use the inferred concrete tuple

    create_kwargs = dict(name=name, shape=shape, dtype=dtype)
    if shape:
        create_kwargs["chunks"] = z_chunks
    create_kwargs["compressors"] = compressor

    zarr_array = zarr_parent.create_array(**create_kwargs)

    try:
        if shape:
            if len(shape) > 0 and np.prod(shape) > 0:
                zarr_array[:] = h5_dataset[:]
        else:
            zarr_array[()] = h5_dataset[()]
    except Exception as e:
        warnings.warn(f"Error copying data for dataset '{name}': {e}. Leaving empty.")

    copy_h5_attributes(h5_dataset, zarr_array)
    return zarr_array


def _migrate_object_dataset(h5_dataset, zarr_parent, name, compressor, shape):
    """Migrate an object-dtype HDF5 dataset to Zarr (v3 API)."""
    import pickle

    warn_data_loss(
        f"Dataset '{name}'",
        "Object dtype will be converted to string or pickled",
    )
    try:
        if not h5_dataset.shape:
            value = h5_dataset[()]
            if isinstance(value, (bytes, str)):
                text = (
                    str(value)
                    if isinstance(value, str)
                    else value.decode("utf-8", errors="replace")
                )
                # Use a fixed-length unicode dtype large enough to hold the text.
                u_dtype = np.dtype(f"U{max(len(text), 1)}")
                zarr_array = zarr_parent.create_array(
                    name=name,
                    shape=(),
                    dtype=u_dtype,
                    compressors=None,
                )
                zarr_array[()] = text
            else:
                pickled_data = pickle.dumps(value)
                pickled_arr = np.frombuffer(pickled_data, dtype=np.uint8)
                zarr_array = zarr_parent.create_array(
                    name=name,
                    shape=pickled_arr.shape,
                    dtype=pickled_arr.dtype,
                    chunks=pickled_arr.shape,
                    compressors=compressor,
                )
                zarr_array[:] = pickled_arr
                zarr_array.attrs["_type"] = "pickled_scalar"
        elif len(h5_dataset) > 0:
            first_elem = h5_dataset[0]
            if isinstance(first_elem, (bytes, str)):
                data = np.array(
                    [
                        (
                            str(item)
                            if isinstance(item, str)
                            else item.decode("utf-8", errors="replace")
                        )
                        for item in h5_dataset[:]
                    ]
                )
                zarr_array = zarr_parent.create_array(
                    name=name,
                    shape=data.shape,
                    dtype=data.dtype,
                    chunks=data.shape,
                    compressors=None,
                )
                zarr_array[:] = data
            else:
                pickled_data = pickle.dumps(h5_dataset[:])
                pickled_arr = np.frombuffer(pickled_data, dtype=np.uint8)
                zarr_array = zarr_parent.create_array(
                    name=name,
                    shape=pickled_arr.shape,
                    dtype=pickled_arr.dtype,
                    chunks=pickled_arr.shape,
                    compressors=compressor,
                )
                zarr_array[:] = pickled_arr
                zarr_array.attrs["_type"] = "pickled"
        else:
            # Empty object dataset; create an empty unicode array.
            zarr_array = zarr_parent.create_array(
                name=name,
                shape=shape,
                dtype="U1",
                fill_value="",
            )
    except Exception as e:
        raise SciTeXIOError(
            f"Failed to migrate object dtype dataset '{name}'",
            context={"error": str(e)},
            suggestion="Consider converting object arrays before migration",
        )

    copy_h5_attributes(h5_dataset, zarr_array)
    return zarr_array


def migrate_group(
    h5_group: h5py.Group,
    zarr_parent: zarr.Group,
    compressor: Optional[Any],
    chunks: Optional[Union[bool, Tuple[int, ...]]] = True,
    show_progress: bool = False,
    _level: int = 0,
) -> None:
    """Recursively migrate HDF5 group to Zarr."""
    copy_h5_attributes(h5_group, zarr_parent)

    try:
        keys = list(h5_group.keys())
    except Exception as e:
        warnings.warn(f"Cannot access group keys: {e}")
        return

    for key in keys:
        try:
            item = h5_group[key]
        except Exception as e:
            warnings.warn(f"Cannot access item '{key}': {e}")
            continue

        if isinstance(item, h5py.Dataset):
            result = migrate_dataset(
                item, zarr_parent, key, compressor, chunks, show_progress
            )
            if result is None:
                print(f"  Warning: Skipped corrupted dataset '{key}'")
        elif isinstance(item, h5py.Group):
            if show_progress and _level < 2:
                print(f"{'  ' * _level}Migrating group '{key}'...")
            zarr_subgroup = zarr_parent.create_group(key)
            migrate_group(
                item, zarr_subgroup, compressor, chunks, show_progress, _level + 1
            )
        else:
            warnings.warn(f"Unknown HDF5 object type for '{key}': {type(item)}")


def validate_migration(
    h5_file: h5py.File,
    zarr_store: zarr.Group,
    show_progress: bool = False,
) -> None:
    """Validate that migration preserved data structure."""

    def validate_item(h5_item, zarr_item, path=""):
        if isinstance(h5_item, h5py.Dataset) and isinstance(zarr_item, zarr.Array):
            if h5_item.shape != zarr_item.shape:
                raise SciTeXIOError(
                    f"Shape mismatch at {path}",
                    context={
                        "h5_shape": h5_item.shape,
                        "zarr_shape": zarr_item.shape,
                    },
                )
            if h5_item.dtype.kind != "O" and zarr_item.dtype.kind != "O":
                if h5_item.dtype != zarr_item.dtype:
                    warnings.warn(
                        f"Dtype mismatch at {path}: "
                        f"HDF5={h5_item.dtype}, Zarr={zarr_item.dtype}"
                    )
        elif isinstance(h5_item, h5py.Group) and isinstance(zarr_item, zarr.Group):
            h5_keys = set(h5_item.keys())
            zarr_keys = set(zarr_item.keys())
            if h5_keys != zarr_keys:
                raise SciTeXIOError(
                    f"Key mismatch at {path}",
                    context={
                        "h5_only": h5_keys - zarr_keys,
                        "zarr_only": zarr_keys - h5_keys,
                    },
                )
            for key in h5_keys:
                validate_item(h5_item[key], zarr_item[key], f"{path}/{key}")

    validate_item(h5_file, zarr_store)

    if show_progress:
        print("  Validation passed")
