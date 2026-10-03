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
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_ZarrExplorer.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-07-11 15:45:49 (ywatanabe)"
# # File: /ssh:sp:/home/ywatanabe/proj/scitex_repo/src/scitex/io/_ZarrExplorer.py
# # ----------------------------------------
# import os
#
# __FILE__ = __file__
# __DIR__ = os.path.dirname(__FILE__)
# # ----------------------------------------
#
# from typing import Any, List, Optional
#
# import zarr
# from ._zarr import _load_zarr_dataset
#
#
# class ZarrExplorer:
#     """Interactive Zarr store explorer."""
#
#     def __init__(self, storepath: str, mode: str = "r"):
#         self.storepath = storepath
#         self.mode = mode
#         self.store = zarr.open(storepath, mode=mode)
#
#     def __enter__(self):
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         pass  # Zarr doesn't need explicit closing
#
#     def explore(self, path: str = "/", max_depth: Optional[int] = None):
#         """Explore Zarr store structure."""
#         self.show(path, max_depth)
#
#     def show(
#         self,
#         path: str = "/",
#         max_depth: Optional[int] = None,
#         indent: str = "",
#         _current_depth: int = 0,
#     ):
#         """Display Zarr store structure."""
#         if max_depth is not None and _current_depth > max_depth:
#             return
#
#         if path == "/":
#             target = self.store
#         else:
#             target = self.store[path.lstrip("/")]
#
#         if hasattr(target, "keys"):  # Group
#             if path != "/":
#                 print(f"{indent}[{path.split('/')[-1]}]")
#
#             for key in sorted(target.keys()):
#                 subpath = f"{path}/{key}".replace("//", "/")
#                 self.show(subpath, max_depth, indent + "  ", _current_depth + 1)
#
#         else:  # Array
#             name = path.split("/")[-1]
#             shape = target.shape
#             dtype = target.dtype
#             size = target.size
#             compressor = getattr(target, "compressor", None)
#             compressed_size = getattr(target, "nbytes_stored", "unknown")
#
#             print(
#                 f"{indent}{name}: shape={shape}, dtype={dtype}, "
#                 f"size={size}, compressor={compressor}, "
#                 f"compressed_size={compressed_size}"
#             )
#
#     def keys(self, path: str = "/") -> List[str]:
#         """Get keys at specified path."""
#         if path == "/":
#             target = self.store
#         else:
#             target = self.store[path.lstrip("/")]
#
#         if hasattr(target, "keys"):
#             return list(target.keys())
#         return []
#
#     def load(self, path: str) -> Any:
#         """Load data from specified path."""
#         return _load_zarr_dataset(self.store[path.lstrip("/")])
#
#     def has_key(self, path: str) -> bool:
#         """Check if key exists (no locking issues!)."""
#         try:
#             _ = self.store[path.lstrip("/")]
#             return True
#         except KeyError:
#             return False
#
#
# def explore_zarr(storepath: str) -> None:
#     """Explore Zarr store structure."""
#     explorer = ZarrExplorer(storepath)
#     explorer.explore()
#
#
# def has_zarr_key(zarr_path: str, key: str) -> bool:
#     """Check if key exists in Zarr store (no locking issues!)."""
#     try:
#         store = zarr.open(zarr_path, mode="r")
#         _ = store[key.lstrip("/")]
#         return True
#     except (KeyError, ValueError):
#         return False
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_ZarrExplorer.py
# --------------------------------------------------------------------------------


import importlib

import numpy as np
import pytest


@pytest.mark.parametrize(
    ("level", "disabled"),
    [("INFO", False), ("WARNING", False), ("CRITICAL", False), ("WARNING", True)],
    ids=["info", "warning", "critical", "disabled"],
)
def test_zarrexplorer_show_stdout_is_exact_and_level_independent(
    tmp_path, capsys, level, disabled
):
    """Use genuine Zarr v2 storage through supported Zarr>=3, preserving its metadata."""
    # Arrange
    import zarr

    module = importlib.import_module("scitex_io._load_modules._ZarrExplorer")
    target = tmp_path / "display.zarr"
    root = zarr.open_group(str(target), mode="w", zarr_format=2)
    array = root.create_array("ints", data=np.arange(3, dtype=np.int32))
    expected = (
        f"..ints: shape={array.shape}, dtype={array.dtype}, size={array.size}, "
        f"compressor={array.compressor}, compressed_size={array.nbytes_stored}\n"
    )
    old_level, old_disabled = module.log.level, module.log.disabled
    module.log.setLevel(level)
    module.log.disabled = disabled
    # Act
    try:
        explorer = module.ZarrExplorer(str(target))
        result = explorer.show("/ints", indent="..")
        output = capsys.readouterr()
    finally:
        module.log.setLevel(old_level)
        module.log.disabled = old_disabled
    # Assert
    assert (output.out, output.err, result) == (expected, "", None)


def test_zarrexplorer_missing_zarr_refuses_constructor(tmp_path, attr_restore):
    # Arrange
    module = importlib.import_module("scitex_io._load_modules._ZarrExplorer")
    attr_restore.set(module, "zarr", None)
    target = tmp_path / "absent.zarr"
    # Act / Assert
    with pytest.raises(ImportError, match="ZarrExplorer requires zarr"):
        module.ZarrExplorer(str(target), mode="w")


def test_has_zarr_key_missing_zarr_refuses_before_open(tmp_path, attr_restore):
    # Arrange
    module = importlib.import_module("scitex_io._load_modules._ZarrExplorer")
    attr_restore.set(module, "zarr", None)
    target = tmp_path / "absent.zarr"
    # Act / Assert
    with pytest.raises(ImportError, match="has_zarr_key requires zarr"):
        module.has_zarr_key(str(target), "group")
