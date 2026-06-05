#!/usr/bin/env python3
# Timestamp: "2025-05-31"
# File: test__flush.py

"""Tests for the flush function in scitex.io module.

Real-collaborator tests: we use ``io.StringIO`` for stdout/stderr and a
recording ``sync_fn`` injected via kwarg instead of mocking ``os.sync``.
"""

import io
import sys
import types

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

from scitex_io import flush


def _make_fake_sys():
    fake = types.SimpleNamespace()
    fake.stdout = io.StringIO()
    fake.stderr = io.StringIO()
    return fake


def _recording_sync():
    calls = {"n": 0}

    def _sync():
        calls["n"] += 1

    return calls, _sync


# ---------------------------------------------------------------------------
# Happy path — flush is called on stdout/stderr and sync is invoked
# ---------------------------------------------------------------------------


def test_flush_invokes_sync_fn_once():
    # Arrange
    fake = _make_fake_sys()
    calls, sync_fn = _recording_sync()
    # Act
    flush(sys=fake, sync_fn=sync_fn)
    # Assert
    assert calls["n"] == 1


def test_flush_preserves_stdout_content():
    # Arrange
    fake = _make_fake_sys()
    fake.stdout.write("hello stdout")
    _calls, sync_fn = _recording_sync()
    # Act
    flush(sys=fake, sync_fn=sync_fn)
    # Assert
    assert fake.stdout.getvalue() == "hello stdout"


def test_flush_preserves_stderr_content():
    # Arrange
    fake = _make_fake_sys()
    fake.stderr.write("hello stderr")
    _calls, sync_fn = _recording_sync()
    # Act
    flush(sys=fake, sync_fn=sync_fn)
    # Assert
    assert fake.stderr.getvalue() == "hello stderr"


# ---------------------------------------------------------------------------
# sys=None — warning is raised, sync_fn is not invoked
# ---------------------------------------------------------------------------


def test_flush_with_none_sys_emits_user_warning():
    # Arrange
    _calls, sync_fn = _recording_sync()
    # Act
    ctx = pytest.warns(UserWarning, match="flush needs sys")
    # Assert
    with ctx:
        flush(sys=None, sync_fn=sync_fn)


def test_flush_with_none_sys_skips_sync_fn():
    # Arrange
    import warnings

    calls, sync_fn = _recording_sync()
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        flush(sys=None, sync_fn=sync_fn)
    # Assert
    assert calls["n"] == 0


# ---------------------------------------------------------------------------
# Real default sys (no kwarg) — no exception, output stays visible
# ---------------------------------------------------------------------------


def test_flush_with_real_default_sys_does_not_raise(capsys):
    # Arrange
    sys.stdout.write("real out")
    _calls, sync_fn = _recording_sync()
    # Act
    flush(sync_fn=sync_fn)
    # Assert
    captured = capsys.readouterr()
    assert captured.out == "real out"


# ---------------------------------------------------------------------------
# Error pass-through — stdout.flush failure propagates
# ---------------------------------------------------------------------------


class _ExplodingStream:
    closed = False

    def flush(self):
        raise OSError("flush boom")


def test_flush_propagates_stdout_flush_error():
    # Arrange
    fake = types.SimpleNamespace(stdout=_ExplodingStream(), stderr=io.StringIO())
    _calls, sync_fn = _recording_sync()
    # Act
    ctx = pytest.raises(OSError, match="flush boom")
    # Assert
    with ctx:
        flush(sys=fake, sync_fn=sync_fn)


def test_flush_propagates_stderr_flush_error():
    # Arrange
    fake = types.SimpleNamespace(stdout=io.StringIO(), stderr=_ExplodingStream())
    _calls, sync_fn = _recording_sync()
    # Act
    ctx = pytest.raises(OSError, match="flush boom")
    # Assert
    with ctx:
        flush(sys=fake, sync_fn=sync_fn)


def test_flush_propagates_sync_fn_error():
    # Arrange
    fake = _make_fake_sys()

    def boom():
        raise OSError("sync boom")

    # Act
    ctx = pytest.raises(OSError, match="sync boom")
    # Assert
    with ctx:
        flush(sys=fake, sync_fn=boom)


# ---------------------------------------------------------------------------
# Multiple calls are independent
# ---------------------------------------------------------------------------


def test_flush_multiple_invocations_call_sync_three_times():
    # Arrange
    fake = _make_fake_sys()
    calls, sync_fn = _recording_sync()
    # Act
    for _ in range(3):
        flush(sys=fake, sync_fn=sync_fn)
    # Assert
    assert calls["n"] == 3
