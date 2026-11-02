#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public API for HDF5 to Zarr migration.

Internal helpers in _h5_helpers.py, error compat in _compat.py.
"""

import os
import warnings
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

try:
    import h5py
except ImportError:  # optional: pip install scitex-io[all]
    h5py = None
try:
    import zarr
except ImportError:  # optional: pip install scitex-io[all]
    zarr = None
from tqdm import tqdm

from ._compat import (
    FileFormatError,
    PathNotFoundError,
    SciTeXIOError,
    check_file_exists,
    check_path,
)
from ._h5_helpers import (
    copy_h5_attributes,
    get_zarr_compressor,
    migrate_group,
    validate_migration,
)

import scitex_logging as slogging

log = slogging.getLogger(__name__)


def migrate_h5_to_zarr(
    h5_path: Union[str, Path],
    zarr_path: Optional[Union[str, Path]] = None,
    compressor: Optional[Union[str, Any]] = "zstd",
    chunks: Optional[Union[bool, Tuple[int, ...]]] = True,
    overwrite: bool = False,
    show_progress: bool = True,
    validate: bool = True,
) -> str:
    """
    Migrate HDF5 file to Zarr format.

    Parameters
    ----------
    h5_path : str or Path
        Path to input HDF5 file
    zarr_path : str or Path, optional
        Path for output Zarr store. If None, uses h5_path with .zarr extension
    compressor : str or compressor object, optional
        Compression to use: 'zstd', 'lz4', 'gzip', 'blosc', or None
    chunks : bool or tuple, optional
        Chunking strategy. True for auto, False for no chunks, or specific shape
    overwrite : bool, optional
        Whether to overwrite existing Zarr store
    show_progress : bool, optional
        Whether to show migration progress
    validate : bool, optional
        Whether to validate the migration by comparing shapes

    Returns
    -------
    str
        Path to created Zarr store
    """
    if zarr is None:
        raise ImportError(
            "HDF5-to-Zarr migration requires zarr; install scitex-io[scientific]."
        )

    h5_path = Path(h5_path)
    if not h5_path.is_absolute():
        check_file_exists(str(h5_path))
    else:
        if not h5_path.exists():
            raise PathNotFoundError(str(h5_path))

    if zarr_path is None:
        zarr_path = h5_path.with_suffix(".zarr")
    else:
        zarr_path = Path(zarr_path)
        if not zarr_path.is_absolute():
            check_path(str(zarr_path))

    if zarr_path.exists() and not overwrite:
        raise SciTeXIOError(
            f"Zarr store already exists: {zarr_path}",
            suggestion="Use overwrite=True to replace existing store",
        )

    compressor_obj = get_zarr_compressor(compressor)

    if show_progress:
        log.info(f"Migrating HDF5 to Zarr:")
        log.info(f" Source: {h5_path}")
        log.info(f" Target: {zarr_path}")
        log.info(f" Compressor: {compressor}")

    try:
        with h5py.File(str(h5_path), "r") as h5_file:
            if zarr_path.exists() and overwrite:
                import shutil

                shutil.rmtree(zarr_path)

            zarr_store = zarr.open(str(zarr_path), mode="w")
            copy_h5_attributes(h5_file, zarr_store)
            migrate_group(h5_file, zarr_store, compressor_obj, chunks, show_progress)

            if show_progress:
                log.info("Migration complete!")

            if validate:
                if show_progress:
                    log.info("Validating migration...")
                validate_migration(h5_file, zarr_store, show_progress)

    except OSError as e:
        if "Unable to open file" in str(e) or "bad symbol table" in str(e):
            warnings.warn(f"HDF5 file appears to be corrupted: {h5_path}")
            raise FileFormatError(
                str(h5_path),
                expected_format="HDF5",
                actual_format="corrupted HDF5",
            )
        else:
            raise SciTeXIOError(
                f"Failed to open HDF5 file: {h5_path}",
                context={"error": str(e)},
            )
    except Exception as e:
        raise SciTeXIOError(
            f"Migration failed: {str(e)}",
            context={"h5_path": str(h5_path), "zarr_path": str(zarr_path)},
            suggestion="Check file permissions and disk space",
        )

    return str(zarr_path)


def migrate_h5_to_zarr_batch(
    h5_paths: List[Union[str, Path]],
    output_dir: Optional[Union[str, Path]] = None,
    compressor: Optional[Union[str, Any]] = "zstd",
    chunks: Optional[Union[bool, Tuple[int, ...]]] = True,
    overwrite: bool = False,
    parallel: bool = False,
    n_workers: Optional[int] = None,
) -> List[str]:
    """
    Migrate multiple HDF5 files to Zarr format.

    Parameters
    ----------
    h5_paths : list of str or Path
        List of HDF5 files to migrate
    output_dir : str or Path, optional
        Directory for output Zarr stores
    compressor : str or compressor object, optional
        Compression to use
    chunks : bool or tuple, optional
        Chunking strategy
    overwrite : bool, optional
        Whether to overwrite existing Zarr stores
    parallel : bool, optional
        Whether to process files in parallel
    n_workers : int, optional
        Number of parallel workers

    Returns
    -------
    list of str
        Paths to created Zarr stores
    """
    h5_paths = [Path(p) for p in h5_paths]
    if h5_paths and zarr is None:
        raise ImportError(
            "HDF5-to-Zarr batch migration requires zarr; "
            "install scitex-io[scientific]."
        )

    zarr_paths = []
    for h5_path in h5_paths:
        if output_dir is None:
            zarr_path = h5_path.with_suffix(".zarr")
        else:
            output_dir_path = Path(output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            zarr_path = output_dir_path / h5_path.with_suffix(".zarr").name
        zarr_paths.append(zarr_path)

    log.info(f"Migrating {len(h5_paths)} HDF5 files to Zarr format...")

    if parallel and len(h5_paths) > 1:
        migrated_paths = _migrate_parallel(
            h5_paths, zarr_paths, compressor, chunks, overwrite, n_workers
        )
    else:
        migrated_paths = _migrate_sequential(
            h5_paths, zarr_paths, compressor, chunks, overwrite
        )

    log.info(f"\nSuccessfully migrated {len(migrated_paths)}/{len(h5_paths)} files")
    return migrated_paths


def _migrate_parallel(h5_paths, zarr_paths, compressor, chunks, overwrite, n_workers):
    """Run migrations in parallel."""
    import functools
    from concurrent.futures import ProcessPoolExecutor, as_completed

    if n_workers is None:
        n_workers = min(os.cpu_count() or 4, len(h5_paths))

    log.info(f"Using {n_workers} parallel workers...")

    migrate_func = functools.partial(
        migrate_h5_to_zarr,
        compressor=compressor,
        chunks=chunks,
        overwrite=overwrite,
        show_progress=False,
        validate=True,
    )

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = {
            executor.submit(migrate_func, h5_path, zarr_path): i
            for i, (h5_path, zarr_path) in enumerate(zip(h5_paths, zarr_paths))
        }

        results = []
        with tqdm(total=len(h5_paths), desc="Migrating") as pbar:
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    results.append((idx, result))
                except Exception as e:
                    log.error(f"\nError migrating {h5_paths[idx]}: {e}")
                    results.append((idx, None))
                pbar.update(1)

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results if r[1] is not None]


def _migrate_sequential(h5_paths, zarr_paths, compressor, chunks, overwrite):
    """Run migrations sequentially."""
    migrated_paths = []
    for h5_path, zarr_path in tqdm(
        zip(h5_paths, zarr_paths), total=len(h5_paths), desc="Migrating"
    ):
        try:
            result = migrate_h5_to_zarr(
                h5_path,
                zarr_path,
                compressor=compressor,
                chunks=chunks,
                overwrite=overwrite,
                show_progress=False,
                validate=True,
            )
            migrated_paths.append(result)
        except Exception as e:
            log.error(f"\nError migrating {h5_path}: {e}")

    return migrated_paths
