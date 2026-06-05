#!/usr/bin/env python3
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__con.py

"""Real-collaborator tests for ``_load_con``.

The original suite patched ``scitex_io._load_modules._con.mne`` and
asserted on the mock's call shape — that's call-record theater, not
behavior. We replace it with hand-rolled fake raw objects injected via
the ``reader`` kwarg the production function now accepts (kept
defaulting to ``mne.io.read_raw_fif`` for real use).
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


# ---------------------------------------------------------------------------
# Fake raw object — exposes only the methods/attrs ``_load_con`` touches
# ---------------------------------------------------------------------------


class _FakeRaw:
    """Hand-rolled stand-in for an ``mne.io.Raw`` object."""

    def __init__(self, df: pd.DataFrame, sfreq: float):
        self._df = df
        self.info = {"sfreq": sfreq}

    def to_data_frame(self):
        return self._df


def _reader_returning(df: pd.DataFrame, sfreq: float):
    """Build a fake reader callable returning the supplied raw payload."""
    calls = []

    def reader(lpath, preload, **kwargs):
        calls.append({"lpath": lpath, "preload": preload, **kwargs})
        return _FakeRaw(df, sfreq)

    reader.calls = calls
    return reader


# ---------------------------------------------------------------------------
# Module-level surface
# ---------------------------------------------------------------------------


def test_mne_available_flag_is_bool():
    """``MNE_AVAILABLE`` is a boolean flag."""
    # Arrange
    # Act
    from scitex_io._load_modules._con import MNE_AVAILABLE
    # Assert
    assert isinstance(MNE_AVAILABLE, bool)


# ---------------------------------------------------------------------------
# Extension validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_path",
    ["file.txt", "data.fif", "connectivity.csv", "test.xlsx"],
)
def test_load_con_rejects_non_con_extension(invalid_path):
    """Reject paths whose extension is not ``.con``."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame({"x": [1]}), 250.0)
    # Act
    ctx = pytest.raises(ValueError, match="File must have .con extension")
    # Assert
    with ctx:
        _load_con(invalid_path, reader=reader)


# ---------------------------------------------------------------------------
# Result shape / contents
# ---------------------------------------------------------------------------


def test_load_con_returns_dataframe():
    """``_load_con`` returns a pandas DataFrame."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(
        pd.DataFrame({"channel_1": [1, 2, 3], "channel_2": [4, 5, 6]}), 250.0
    )
    # Act
    result = _load_con("test_file.con", reader=reader)
    # Assert
    assert isinstance(result, pd.DataFrame)


def test_load_con_appends_samp_rate_column():
    """Result DataFrame gains a ``samp_rate`` column."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(
        pd.DataFrame({"channel_1": [1, 2, 3]}), 250.0
    )
    # Act
    result = _load_con("test_file.con", reader=reader)
    # Assert
    assert "samp_rate" in result.columns


def test_load_con_samp_rate_value_matches_sfreq():
    """All ``samp_rate`` entries equal ``info['sfreq']``."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(
        pd.DataFrame({"channel_1": [1, 2, 3]}), 512.0
    )
    # Act
    result = _load_con("connectivity.con", reader=reader)
    # Assert
    assert all(result["samp_rate"] == 512.0)


def test_load_con_preserves_input_columns():
    """Original channel columns survive the round-trip."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(
        pd.DataFrame(
            {"Fp1": [0.1, 0.2, 0.3], "Fp2": [0.4, 0.5, 0.6], "F3": [0.7, 0.8, 0.9]}
        ),
        512.0,
    )
    # Act
    result = _load_con("connectivity.con", reader=reader)
    # Assert
    assert set(("Fp1", "Fp2", "F3")).issubset(result.columns)


def test_load_con_preserves_input_values():
    """Channel values are unchanged."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(
        pd.DataFrame({"Fp1": [0.1, 0.2, 0.3]}), 512.0
    )
    # Act
    result = _load_con("connectivity.con", reader=reader)
    # Assert
    assert list(result["Fp1"]) == [0.1, 0.2, 0.3]


@pytest.mark.parametrize("sfreq", [250.0, 500.0, 1000.0, 2048.0])
def test_load_con_propagates_sfreq_to_samp_rate(sfreq):
    """``info['sfreq']`` propagates verbatim into ``samp_rate``."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame({"channel": [1, 2, 3]}), sfreq)
    # Act
    result = _load_con("test.con", reader=reader)
    # Assert
    assert result["samp_rate"].iloc[0] == sfreq


# ---------------------------------------------------------------------------
# Reader invocation contract
# ---------------------------------------------------------------------------


def test_load_con_passes_kwargs_to_reader():
    """User kwargs are forwarded to the reader."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame({"data": [1, 2, 3]}), 250.0)
    # Act
    _load_con(
        "test.con",
        reader=reader,
        verbose=False,
        picks=["eeg"],
        exclude=["bad_channel"],
        proj=True,
    )
    # Assert
    assert reader.calls[0]["picks"] == ["eeg"]


def test_load_con_always_calls_reader_with_preload_true():
    """``preload=True`` is unconditionally passed to the reader."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame({"data": [1]}), 250.0)
    # Act
    _load_con("test.con", reader=reader)
    # Assert
    assert reader.calls[0]["preload"] is True


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


def test_load_con_propagates_filenotfounderror_from_reader():
    """A FileNotFoundError from the reader bubbles up unchanged."""
    # Arrange
    from scitex_io._load_modules._con import _load_con

    def reader(lpath, preload, **kwargs):
        raise FileNotFoundError("File not found")

    # Act
    ctx = pytest.raises(FileNotFoundError, match="File not found")
    # Assert
    with ctx:
        _load_con("nonexistent.con", reader=reader)


def test_load_con_propagates_valueerror_from_reader():
    """A ValueError from the reader bubbles up unchanged."""
    # Arrange
    from scitex_io._load_modules._con import _load_con

    def reader(lpath, preload, **kwargs):
        raise ValueError("Invalid file format")

    # Act
    ctx = pytest.raises(ValueError, match="Invalid file format")
    # Assert
    with ctx:
        _load_con("invalid.con", reader=reader)


def test_load_con_raises_keyerror_when_sfreq_missing():
    """Missing ``sfreq`` in ``raw.info`` raises ``KeyError``."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    raw_without_sfreq = SimpleNamespace(
        info={},
        to_data_frame=lambda: pd.DataFrame({"x": [1]}),
    )

    def reader(lpath, preload, **kwargs):
        return raw_without_sfreq

    # Act
    ctx = pytest.raises(KeyError)
    # Assert
    with ctx:
        _load_con("test.con", reader=reader)


# ---------------------------------------------------------------------------
# Edge cases — empty + large DataFrames
# ---------------------------------------------------------------------------


def test_load_con_empty_input_returns_dataframe():
    """An empty input frame still yields a DataFrame."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame(), 250.0)
    # Act
    result = _load_con("empty.con", reader=reader)
    # Assert
    assert isinstance(result, pd.DataFrame)


def test_load_con_empty_input_has_samp_rate_column():
    """``samp_rate`` is appended even on an empty frame."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame(), 250.0)
    # Act
    result = _load_con("empty.con", reader=reader)
    # Assert
    assert "samp_rate" in result.columns


def test_load_con_empty_input_returns_zero_rows():
    """Empty input → zero-row output."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader = _reader_returning(pd.DataFrame(), 250.0)
    # Act
    result = _load_con("empty.con", reader=reader)
    # Assert
    assert len(result) == 0


def test_load_con_large_input_preserves_shape():
    """Large input → shape (n_samples, n_channels + 1) for samp_rate."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    n_samples, n_channels = 1000, 64
    columns = [f"channel_{i}" for i in range(n_channels)]
    df = pd.DataFrame(np.random.randn(n_samples, n_channels), columns=columns)
    reader = _reader_returning(df, 1000.0)
    # Act
    result = _load_con("large.con", reader=reader)
    # Assert
    assert result.shape == (n_samples, n_channels + 1)


def test_load_con_large_input_samp_rate_constant():
    """Every row of ``samp_rate`` carries the sfreq value."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    n_samples, n_channels = 1000, 64
    columns = [f"channel_{i}" for i in range(n_channels)]
    df = pd.DataFrame(np.random.randn(n_samples, n_channels), columns=columns)
    reader = _reader_returning(df, 1000.0)
    # Act
    result = _load_con("large.con", reader=reader)
    # Assert
    assert all(result["samp_rate"] == 1000.0)


# ---------------------------------------------------------------------------
# Function signature
# ---------------------------------------------------------------------------


def test_load_con_signature_includes_lpath():
    """``_load_con`` accepts ``lpath`` as a parameter."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    # Act
    sig = inspect.signature(_load_con)
    # Assert
    assert "lpath" in sig.parameters


def test_load_con_signature_accepts_kwargs():
    """``_load_con`` accepts ``**kwargs``."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    # Act
    sig = inspect.signature(_load_con)
    # Assert
    assert any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )


def test_load_con_signature_has_return_annotation():
    """``_load_con`` declares a return annotation."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    # Act
    sig = inspect.signature(_load_con)
    # Assert
    assert sig.return_annotation is not inspect.Signature.empty


# ---------------------------------------------------------------------------
# Realistic EEG payload sanity-check
# ---------------------------------------------------------------------------


@pytest.fixture
def eeg_reader():
    """Reader that returns a 10-channel × 2560-sample frame at 256 Hz."""
    eeg_channels = ["Fp1", "Fp2", "F3", "F4", "C3", "C4", "P3", "P4", "O1", "O2"]
    n_samples = 2560
    np.random.seed(42)
    eeg_data = np.random.randn(n_samples, len(eeg_channels)) * 50e-6
    df = pd.DataFrame(eeg_data, columns=eeg_channels)
    return _reader_returning(df, 256.0), eeg_channels, n_samples


def test_load_con_eeg_payload_returns_dataframe(eeg_reader):
    """Realistic EEG input still yields a DataFrame."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader, _, _ = eeg_reader
    # Act
    result = _load_con("eeg.con", reader=reader, verbose=False)
    # Assert
    assert isinstance(result, pd.DataFrame)


def test_load_con_eeg_payload_has_expected_shape(eeg_reader):
    """Realistic EEG input → expected shape (samples, channels+1)."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader, channels, n_samples = eeg_reader
    # Act
    result = _load_con("eeg.con", reader=reader, verbose=False)
    # Assert
    assert result.shape == (n_samples, len(channels) + 1)


def test_load_con_eeg_payload_contains_all_input_channels(eeg_reader):
    """All EEG channel columns survive the round-trip."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader, channels, _ = eeg_reader
    # Act
    result = _load_con("eeg.con", reader=reader, verbose=False)
    # Assert
    assert all(col in result.columns for col in channels)


def test_load_con_eeg_payload_samp_rate_is_256(eeg_reader):
    """Every ``samp_rate`` row carries the 256 Hz sampling rate."""
    # Arrange
    from scitex_io._load_modules._con import _load_con
    reader, _, _ = eeg_reader
    # Act
    result = _load_con("eeg.con", reader=reader, verbose=False)
    # Assert
    assert all(result["samp_rate"] == 256.0)


if __name__ == "__main__":
    import os
    pytest.main([os.path.abspath(__file__)])
