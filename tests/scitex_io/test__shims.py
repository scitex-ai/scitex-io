#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for trivial shim modules — `__main__.py` and `_load_cache.py`.

These exist for back-compat with the umbrella; just verify the
re-exports work and `python -m scitex_io` invokes the CLI cleanly.
"""

from __future__ import annotations

import subprocess
import sys


class TestLoadCacheShim:
    def test_reexports_cache_data(self):
        from scitex_io._load_cache import (
            cache_data,
            get_cached_data,
            load_npy_cached,
        )

        # Each export must be callable.
        for fn in (cache_data, get_cached_data, load_npy_cached):
            assert callable(fn), f"{fn!r} should be callable"

    def test_reexports_match_loading_module(self):
        # The shim should re-export the SAME objects as
        # `scitex_io._loading._load_cache`, not copies.
        from scitex_io import _load_cache as shim
        from scitex_io._loading import _load_cache as canonical

        assert shim.cache_data is canonical.cache_data
        assert shim.get_cached_data is canonical.get_cached_data
        assert shim.load_npy_cached is canonical.load_npy_cached

    def test_all_attribute(self):
        from scitex_io import _load_cache as shim

        assert set(shim.__all__) == {
            "cache_data",
            "get_cached_data",
            "load_npy_cached",
        }


class TestMainEntryPoint:
    def test_python_dash_m_scitex_io_help(self):
        """`python -m scitex_io --help` should exit 0 and print help."""
        result = subprocess.run(
            [sys.executable, "-m", "scitex_io", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"exit {result.returncode}; stderr={result.stderr!r}"
        )
        assert "Usage" in result.stdout or "usage" in result.stdout.lower()

    def test_python_dash_m_scitex_io_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "scitex_io", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
