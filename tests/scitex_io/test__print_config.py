#!/usr/bin/env python3
"""Tests for ``scitex_io._print_config`` (ported from scitex_gen._fs._print_config).

The upstream tests patched ``scitex_gen._fs._print_config.scitex`` (a
module-level attribute that the original implementation referenced via
``scitex.io.load_configs``). The ported implementation in
``scitex_io._print_config`` instead does a *local* ``from scitex_io
import load_configs`` inside the function body, so those patch points
no longer exist. New focused tests below exercise the function via the
real ``load_configs`` path.
"""

from __future__ import annotations

import contextlib

import pytest

from scitex_io import print_config
from scitex_io._print_config import print_config_main


@contextlib.contextmanager
def _swap_attr(obj, name, value):
    sentinel = object()
    prev = getattr(obj, name, sentinel)
    setattr(obj, name, value)
    try:
        yield
    finally:
        if prev is sentinel:
            delattr(obj, name)
        else:
            setattr(obj, name, prev)


class _PrintRecorder:
    def __init__(self):
        self.calls = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))


class TestPrintConfigCLI:
    """Smoke tests for the CLI wrapper."""

    def test_print_config_main_with_no_key_prints_available_configurations(
        self, monkeypatch, capsys
    ):
        # Stub out load_configs so we don't hit the filesystem.
        import scitex_io

        monkeypatch.setattr(scitex_io, "load_configs", lambda: {"a": 1, "b": 2})

        # Re-import the helper so it picks up the patched ``load_configs``.
        import scitex_io._print_config as _pc

        _pc.print_config(None)
        captured = capsys.readouterr()
        assert "Available configurations:" in captured.out

    def test_print_config_simple_key_prints_value(self, monkeypatch, capsys):
        import scitex_io

        monkeypatch.setattr(
            scitex_io, "load_configs", lambda: {"hello": "world"}
        )

        import scitex_io._print_config as _pc

        _pc.print_config("hello")
        captured = capsys.readouterr()
        assert "world" in captured.out

    def test_print_config_main_argparse(self, monkeypatch, capsys):
        """`print_config_main` parses argv and delegates to `print_config`."""
        import scitex_io

        monkeypatch.setattr(
            scitex_io, "load_configs", lambda: {"k": "v"}
        )

        print_config_main(["k"])
        captured = capsys.readouterr()
        assert "v" in captured.out

    def test_print_config_missing_key_does_not_crash(self, monkeypatch, capsys):
        import scitex_io

        monkeypatch.setattr(scitex_io, "load_configs", lambda: {})

        # Should print "None" (or similar) instead of raising.
        print_config("nonexistent.deep.key")
        # The function catches everything and falls through; just assert
        # *something* was printed.
        captured = capsys.readouterr()
        assert captured.out  # non-empty


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
