# Smoke test (TODO: real coverage).
def test_placeholder_true_case():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert True

# Add your tests here

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_zarr.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # Timestamp: "2025-07-11 15:44:00 (ywatanabe)"
# # File: /ssh:sp:/home/ywatanabe/proj/scitex_repo/src/scitex/io/_save_modules/_zarr.py
# # ----------------------------------------
# import os
#
# __FILE__ = __file__
# __DIR__ = os.path.dirname(__FILE__)
# # ----------------------------------------
# # src/scitex/io/_save_modules/_zarr.py
# from typing import Any, Optional
#
# import numpy as np
# import zarr
#
# # Detect Zarr version for API compatibility
# ZARR_V3 = int(zarr.__version__.split(".")[0]) >= 3
#
#
# def _get_compressor(compressor_name):
#     """Get compressor based on Zarr version."""
#     if ZARR_V3:
#         from zarr.codecs import GzipCodec, ZstdCodec
#
#         compressor_map = {
#             "zstd": ZstdCodec(level=3),
#             "gzip": GzipCodec(level=5),
#         }
#         return compressor_map.get(compressor_name.lower(), ZstdCodec(level=3))
#     else:
#         from numcodecs import LZ4, GZip, Zstd
#
#         compressor_map = {
#             "zstd": Zstd(level=3),
#             "lz4": LZ4(acceleration=1),
#             "gzip": GZip(level=5),
#         }
#         return compressor_map.get(compressor_name.lower(), Zstd(level=3))
#
#
# def _create_array(group, name, data, chunks=True, compressor=None, **kwargs):
#     """Create array with version-appropriate API."""
#     if ZARR_V3:
#         # Zarr v3 API: use create_array with compressors list
#         comp_kwargs = {}
#         if compressor is not None:
#             comp_kwargs["compressors"] = [compressor]
#
#         # Handle chunks parameter: v3 doesn't accept True/None
#         if chunks is True:
#             chunks = "auto"
#         elif chunks is None or chunks is False:
#             # Don't pass chunks, let zarr use defaults
#             return group.create_array(name, data=data, **comp_kwargs, **kwargs)
#
#         return group.create_array(
#             name, data=data, chunks=chunks, **comp_kwargs, **kwargs
#         )
#     else:
#         # Zarr v2 API: use create_dataset with compressor
#         return group.create_dataset(
#             name, data=data, chunks=chunks, compressor=compressor, **kwargs
#         )
#
#
# def _save_zarr(
#     obj: Any,
#     spath: str,
#     key: Optional[str] = None,
#     compressor="zstd",
#     chunks=True,
#     store_type="auto",
#     consolidate_metadata=False,
#     **kwargs,
# ):
#     """
#     Save object to Zarr format with automatic chunking and compression.
#
#     Parameters:
#     -----------
#     obj : Any
#         Object to save (dict, array, etc.)
#     spath : str
#         Path to Zarr store (.zarr extension or .zarr.zip)
#     key : str, optional
#         Key/group path within Zarr store
#     compressor : str
#         Compression algorithm ('zstd', 'gzip')
#     chunks : bool or tuple
#         Chunking strategy
#     store_type : str
#         'auto' (detect from extension), 'directory', or 'zip'
#     consolidate_metadata : bool
#         Consolidate metadata to reduce file count (directory stores only)
#     """
#     # Convert to dict if needed
#     if not isinstance(obj, dict):
#         obj = {"data": obj}
#
#     # Determine store type
#     if store_type == "auto":
#         if spath.endswith(".zip") or spath.endswith(".zarr.zip"):
#             store_type = "zip"
#         else:
#             store_type = "directory"
#
#     # Create appropriate store
#     if store_type == "zip":
#         # Single file ZIP store
#         store = zarr.storage.ZipStore(spath, mode="w")
#         root = zarr.open(store, mode="w")
#     else:
#         # Directory store
#         # Remove file if it exists (tempfile creates files, but zarr needs directories)
#         if os.path.exists(spath) and not os.path.isdir(spath):
#             os.remove(spath)
#
#         # Open or create Zarr store
#         try:
#             root = zarr.open(spath, mode="a")
#         except Exception:
#             root = zarr.open(spath, mode="w")
#
#     # Handle compressor configuration
#     if isinstance(compressor, str):
#         compressor = _get_compressor(compressor)
#
#     # Navigate to target group
#     if key:
#         # Create nested groups as needed
#         parts = [p for p in key.split("/") if p]
#         current_group = root
#
#         for part in parts[:-1]:
#             if part not in current_group:
#                 current_group = current_group.create_group(part)
#             else:
#                 current_group = current_group[part]
#
#         final_key = parts[-1] if parts else ""
#         if final_key:
#             if final_key in current_group:
#                 del current_group[final_key]  # Override
#             target_group = current_group.create_group(final_key)
#         else:
#             target_group = current_group
#     else:
#         target_group = root
#
#     # Save datasets
#     for dataset_name, data in obj.items():
#         if isinstance(data, str):
#             # String data
#             _create_array(
#                 target_group, dataset_name, data=np.array(data), compressor=None
#             )
#         elif isinstance(data, (int, float, bool)):
#             # Scalar data - convert to 0-d array
#             _create_array(
#                 target_group, dataset_name, data=np.array(data), compressor=None
#             )
#         else:
#             # Array data
#             data_array = np.asarray(data)
#
#             if data_array.dtype == np.object_:
#                 # Complex objects - pickle them
#                 import pickle
#
#                 pickled_data = pickle.dumps(data)
#                 dataset = _create_array(
#                     target_group,
#                     dataset_name,
#                     data=np.frombuffer(pickled_data, dtype=np.uint8),
#                     compressor=compressor,
#                 )
#                 dataset.attrs["_type"] = "pickled"
#             else:
#                 # Regular array data
#                 _create_array(
#                     target_group,
#                     dataset_name,
#                     data=data_array,
#                     chunks=chunks,
#                     compressor=compressor,
#                     **kwargs,
#                 )
#
#     # Close ZIP store if needed
#     if store_type == "zip":
#         store.close()
#
#     # Consolidate metadata if requested (directory stores only)
#     if store_type == "directory" and consolidate_metadata:
#         try:
#             zarr.consolidate_metadata(spath)
#             print(
#                 f"✅ Saved to Zarr (consolidated): {spath}" + (f"/{key}" if key else "")
#             )
#         except Exception:
#             print(f"✅ Saved to Zarr: {spath}" + (f"/{key}" if key else ""))
#     else:
#         print(f"✅ Saved to Zarr ({store_type}): {spath}" + (f"/{key}" if key else ""))
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_zarr.py
# --------------------------------------------------------------------------------



import importlib

import numpy as np
import pytest


def test_missing_zarr_preserves_existing_directory_store_target(tmp_path, attr_restore):
    # Arrange
    module = importlib.import_module("scitex_io._save_modules._zarr")
    target = tmp_path / "existing.zarr"
    original = b"caller-owned regular file"
    target.write_bytes(original)
    attr_restore.set(module, "zarr", None)
    # Act
    with pytest.raises(ImportError, match="Zarr saving requires zarr"):
        module._save_zarr(np.arange(3), str(target), compressor=None)
    # Assert
    assert target.read_bytes() == original


@pytest.mark.parametrize("store_type", ["directory", "zip"])
def test_missing_codecs_preserves_existing_target(tmp_path, attr_restore, store_type):
    """Codec refusal must precede directory replacement and ZIP write-mode opening."""
    # Arrange
    module = importlib.import_module("scitex_io._save_modules._zarr")
    target = tmp_path / "existing.bin"
    original = b"caller-owned content before codec failure"
    target.write_bytes(original)
    attr_restore.set(module, "GzipCodec", None)
    attr_restore.set(module, "ZstdCodec", None)
    # Act
    with pytest.raises(ImportError, match="requires GzipCodec and ZstdCodec"):
        module._save_zarr(
            np.arange(3), str(target), store_type=store_type, compressor="zstd"
        )
    # Assert
    assert target.read_bytes() == original


def test_missing_zipstore_preserves_existing_target(tmp_path, attr_restore):
    # Arrange
    module = importlib.import_module("scitex_io._save_modules._zarr")
    storage = importlib.import_module("zarr.storage")
    target = tmp_path / "existing.zip"
    original = b"caller-owned archive content"
    target.write_bytes(original)
    attr_restore.delete(storage, "ZipStore")
    # Act
    with pytest.raises(ImportError, match="requires zarr.storage.ZipStore"):
        module._save_zarr(np.arange(3), str(target), compressor=None)
    # Assert
    assert target.read_bytes() == original


@pytest.mark.parametrize("compression", ["none", "custom"])
def test_missing_builtin_codecs_retains_explicit_compression_passthrough(
    tmp_path, attr_restore, compression
):
    """Use real public codecs/storage; absence of default constructors must not overrefuse."""
    # Arrange
    import zarr
    from zarr.codecs import GzipCodec

    module = importlib.import_module("scitex_io._save_modules._zarr")
    compressors = {"none": None, "custom": [GzipCodec(level=1)]}
    target = tmp_path / "passthrough.zarr"
    values = np.arange(3, dtype=np.int32)
    attr_restore.set(module, "GzipCodec", None)
    attr_restore.set(module, "ZstdCodec", None)
    # Act
    module._save_zarr(values, str(target), compressor=compressors[compression])
    root = zarr.open(str(target), mode="r")
    # Assert
    assert np.array_equal(root["data"][:], values)
