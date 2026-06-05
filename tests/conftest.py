#!/usr/bin/env python3
"""Test configuration for scitex-io.

Shared fixtures used to replace the banned ``monkeypatch``/``mocker``
parameters and the ``unittest.mock`` family while keeping the
collaborator real (or, when truly necessary, swapped by hand-restore).
"""
from __future__ import annotations

import os
import sys
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as td:
        yield td


@pytest.fixture
def env_save_restore():
    """Snapshot ``os.environ`` on enter, restore on exit.

    Use to set/unset env vars inside a test without leaking them.
    Replaces ``monkeypatch.setenv`` / ``monkeypatch.delenv``.

    Yields a small handle exposing ``set(k, v)`` / ``delete(k)`` so
    each call site reads naturally and the teardown is centralised.
    """
    snapshot = os.environ.copy()

    class _Handle:
        @staticmethod
        def set(key, value):
            os.environ[key] = value

        @staticmethod
        def delete(key):
            os.environ.pop(key, None)

    try:
        yield _Handle()
    finally:
        # Restore exact state — remove additions, restore removed/changed.
        for k in list(os.environ.keys()):
            if k not in snapshot:
                del os.environ[k]
        for k, v in snapshot.items():
            if os.environ.get(k) != v:
                os.environ[k] = v


@pytest.fixture
def attr_restore():
    """Snapshot module-attribute mutations and restore on teardown.

    Replaces ``monkeypatch.setattr(module, attr, value)`` without using
    the banned fixture parameter. Each ``set(obj, attr, value)`` call
    records the previous value (or sentinel for "did not exist") and
    restores it after the test.
    """
    _MISSING = object()
    saved: list[tuple] = []

    class _Handle:
        @staticmethod
        def set(obj, attr, value):
            prev = getattr(obj, attr, _MISSING)
            saved.append((obj, attr, prev))
            setattr(obj, attr, value)

        @staticmethod
        def delete(obj, attr):
            prev = getattr(obj, attr, _MISSING)
            saved.append((obj, attr, prev))
            if hasattr(obj, attr):
                delattr(obj, attr)

    try:
        yield _Handle()
    finally:
        for obj, attr, prev in reversed(saved):
            if prev is _MISSING:
                if hasattr(obj, attr):
                    try:
                        delattr(obj, attr)
                    except (AttributeError, TypeError):
                        pass
            else:
                try:
                    setattr(obj, attr, prev)
                except (AttributeError, TypeError):
                    pass


@pytest.fixture
def chdir_tmp(tmp_path):
    """Change CWD into ``tmp_path`` for the test, restore on teardown.

    Replaces ``monkeypatch.chdir(tmp_path)``.
    """
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


@pytest.fixture
def argv_restore():
    """Snapshot ``sys.argv`` and restore on teardown.

    Replaces ``monkeypatch.setattr(sys, "argv", [...])``.
    """
    saved = list(sys.argv)
    try:
        yield sys.argv
    finally:
        sys.argv[:] = saved
