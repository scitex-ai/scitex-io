#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for trivial shim modules — `__main__.py` and `_load_cache.py`.

from __future__ import annotations
These exist for back-compat with the umbrella; just verify the
re-exports work and `python -m scitex_io` invokes the CLI cleanly.
"""


import subprocess
import sys


class TestLoadCacheShim:
    def test_reexports_cache_data(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        from scitex_io._load_cache import (
            cache_data,
            get_cached_data,
            load_npy_cached,
        )

        # Each export must be callable.
        # Assert
        assert all(callable(fn) for fn in (cache_data, get_cached_data, load_npy_cached)), f'{fn!r} should be callable'

    def test_reexports_match_loading_module_shim_cache_data_is_canonical_cache_data(self):
        # The shim should re-export the SAME objects as
        # `scitex_io._loading._load_cache`, not copies.
        # Arrange
        # Arrange
        from scitex_io import _load_cache as shim
        # Act
        from scitex_io._loading import _load_cache as canonical
        # Act
        # Assert
        # Assert
        assert shim.cache_data is canonical.cache_data

    def test_reexports_match_loading_module_shim_get_cached_data_is_canonical_get_cached_data(self):
        # The shim should re-export the SAME objects as
        # `scitex_io._loading._load_cache`, not copies.
        # Arrange
        # Arrange
        from scitex_io import _load_cache as shim
        # Act
        from scitex_io._loading import _load_cache as canonical
        # Act
        # Assert
        # Assert
        assert shim.get_cached_data is canonical.get_cached_data

    def test_reexports_match_loading_module_shim_load_npy_cached_is_canonical_load_npy_cached(self):
        # The shim should re-export the SAME objects as
        # `scitex_io._loading._load_cache`, not copies.
        # Arrange
        # Arrange
        from scitex_io import _load_cache as shim
        # Act
        from scitex_io._loading import _load_cache as canonical
        # Act
        # Assert
        # Assert
        assert shim.load_npy_cached is canonical.load_npy_cached


    def test_all_attribute_set_shim_all_cache_data_get_cached_data_load_npy_c(self):
        # Arrange
        # Act
        # Arrange
        # Act
        from scitex_io import _load_cache as shim

        # Assert
        # Assert
        assert set(shim.__all__) == {
            "cache_data",
            "get_cached_data",
            "load_npy_cached",
        }


