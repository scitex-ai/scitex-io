#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared fixtures for the observer-registry tests (real hooks, real files)."""

from __future__ import annotations

import logging
import os

import pytest

import scitex_io
from scitex_io._observers import (
    STRICT_ENV,
    _post_load_hooks,
    _post_save_hooks,
    reset_observer_failures,
)


@pytest.fixture
def hooks():
    """Run with ONLY the test's own hooks and zeroed failure counters.

    Entry-point observers are activated first so they cannot be appended
    after the lists are cleared.
    """
    scitex_io._ensure_observers_activated()
    saved_save, saved_load = list(_post_save_hooks), list(_post_load_hooks)
    saved_strict = os.environ.pop(STRICT_ENV, None)
    _post_save_hooks.clear()
    _post_load_hooks.clear()
    reset_observer_failures()
    yield
    _post_save_hooks[:] = saved_save
    _post_load_hooks[:] = saved_load
    if saved_strict is not None:
        os.environ[STRICT_ENV] = saved_strict
    reset_observer_failures()


@pytest.fixture
def strict_env(hooks):
    """SCITEX_IO_STRICT_PROVENANCE=1 for the duration of the test."""
    os.environ[STRICT_ENV] = "1"
    yield
    os.environ.pop(STRICT_ENV, None)


def _boom(*_args):
    raise RuntimeError("observer exploded")


@pytest.fixture
def boom():
    """A real observer that always fails."""
    return _boom


@pytest.fixture
def provenance_warnings():
    """Return the WARNING+ 'provenance LOST' records from a caplog."""

    def _select(caplog):
        # Scenario fixtures log during the setup phase, tests during call.
        records = caplog.get_records("setup") + caplog.get_records("call")
        return [
            r
            for r in records
            if r.levelno >= logging.WARNING and "provenance LOST" in r.getMessage()
        ]

    return _select
