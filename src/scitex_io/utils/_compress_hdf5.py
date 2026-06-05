#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-compress an existing HDF5 file with gzip.

Migrated from the scitex umbrella (``scitex.utils._compress_hdf5``). Lives
under ``scitex_io.utils`` alongside the other HDF5 helpers because HDF5
(re)compression is an I/O concern. ``h5py`` is an optional ``[scientific]``
dependency, so it is imported lazily inside the function — importing this
module (and ``scitex_io.utils``) stays cheap and h5py-free until the
function is actually called.
"""

from __future__ import annotations

import os

__all__ = ["compress_hdf5"]


def compress_hdf5(input_file, output_file=None, compression_level=4):
    """Compress an HDF5 file by rewriting every dataset with gzip.

    Parameters
    ----------
    input_file : str
        Path to the input HDF5 file.
    output_file : str, optional
        Path to the output compressed HDF5 file. If ``None``, uses
        ``<input_stem>.compressed<ext>``.
    compression_level : int, optional
        gzip compression level (1-9); higher means smaller output but
        slower processing. Defaults to 4.

    Returns
    -------
    str
        The path to the written compressed file.
    """
    # Import h5py only when actually needed — it is an optional dependency.
    try:
        import h5py
    except ImportError as exc:
        raise ImportError(
            "h5py is required for HDF5 compression but is not installed. "
            "Install it via `pip install scitex-io[scientific]` or `pip install h5py`."
        ) from exc

    # tqdm is purely cosmetic for very large datasets.
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None

    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}.compressed{ext}"

    print(f"Compressing {input_file} to {output_file}")

    with h5py.File(input_file, "r") as src, h5py.File(output_file, "w") as dst:
        # Copy file-level attributes.
        for key, value in src.attrs.items():
            dst.attrs[key] = value

        def copy_dataset(name, obj):
            if isinstance(obj, h5py.Dataset):
                # Surface progress for very large datasets.
                if len(obj.shape) > 0 and obj.shape[0] > 1000000:
                    print(f"Processing large dataset {name} with shape {obj.shape}")

                # Preserve existing chunking if present, else let h5py choose.
                chunks = True
                if obj.chunks is not None:
                    chunks = obj.chunks

                compressed_data = dst.create_dataset(
                    name,
                    shape=obj.shape,
                    dtype=obj.dtype,
                    compression="gzip",
                    compression_opts=compression_level,
                    chunks=chunks,
                )

                if len(obj.shape) > 0 and obj.shape[0] > 10000000:
                    # Stream huge datasets to avoid loading them whole.
                    chunk_size = 5000000
                    iterator = range(0, obj.shape[0], chunk_size)
                    if tqdm is not None:
                        iterator = tqdm(iterator, desc=f"Copying {name}")
                    for i in iterator:
                        end = min(i + chunk_size, obj.shape[0])
                        if len(obj.shape) == 1:
                            compressed_data[i:end] = obj[i:end]
                        else:
                            compressed_data[i:end, ...] = obj[i:end, ...]
                else:
                    compressed_data[()] = obj[()]

                for key, value in obj.attrs.items():
                    compressed_data.attrs[key] = value

            elif isinstance(obj, h5py.Group):
                group = dst.create_group(name)
                for key, value in obj.attrs.items():
                    group.attrs[key] = value

        src.visititems(copy_dataset)

    print(
        f"Compression complete. Original size: {os.path.getsize(input_file) / 1e9:.2f} GB, "
        f"New size: {os.path.getsize(output_file) / 1e9:.2f} GB"
    )

    return output_file


# EOF
