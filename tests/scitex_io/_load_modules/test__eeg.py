#!/usr/bin/env python3
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__eeg.py

"""Real-collaborator tests for ``_load_eeg_data``.

The original suite patched ``scitex_io._load_modules._eeg.mne`` (the
module-level reference) and asserted on the mock's call-shape. We
replace that with a hand-rolled fake ``mne`` namespace injected via
the ``mne_module`` kwarg ``_load_eeg_data`` now accepts.

For the ``.eeg`` companion-file branches we inject a fake ``isfile``
callable instead of patching ``os.path.isfile``.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


# ---------------------------------------------------------------------------
# Hand-rolled fake mne namespace
# ---------------------------------------------------------------------------


class _RawSentinel:
    """Concrete object returned by fake readers — distinguishable by id."""


def _make_fake_mne():
    """Return ``(mne_ns, calls)`` where mne_ns mimics ``mne.io.read_raw_*``."""
    calls: list[dict] = []

    def _reader(name):
        sentinel = _RawSentinel()

        def fn(lpath, preload, **kwargs):
            calls.append({"name": name, "lpath": lpath, "preload": preload, **kwargs})
            return sentinel

        fn.sentinel = sentinel
        return fn

    io_ns = SimpleNamespace(
        read_raw_brainvision=_reader("brainvision"),
        read_raw_edf=_reader("edf"),
        read_raw_bdf=_reader("bdf"),
        read_raw_gdf=_reader("gdf"),
        read_raw_cnt=_reader("cnt"),
        read_raw_egi=_reader("egi"),
        read_raw=_reader("read_raw"),
    )
    return SimpleNamespace(io=io_ns), calls


# ---------------------------------------------------------------------------
# Module-level surface
# ---------------------------------------------------------------------------


def test_mne_available_flag_is_bool():
    """``MNE_AVAILABLE`` is a boolean flag."""
    # Arrange
    # Act
    from scitex_io._load_modules._eeg import MNE_AVAILABLE
    # Assert
    assert isinstance(MNE_AVAILABLE, bool)


# ---------------------------------------------------------------------------
# Extension validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_path",
    ["file.txt", "data.wav", "signal.mat", "test.xlsx"],
)
def test_load_eeg_data_rejects_unsupported_extension(invalid_path):
    """Reject paths whose extension is unsupported."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    ctx = pytest.raises(ValueError, match="File must have one of these extensions")
    # Assert
    with ctx:
        _load_eeg_data(invalid_path)


@pytest.mark.parametrize(
    "uppercase_path",
    ["file.EDF", "data.BDF", "test.CNT"],
)
def test_load_eeg_data_rejects_uppercase_extension(uppercase_path):
    """Extension matching is case-sensitive."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    ctx = pytest.raises(ValueError, match="File must have one of these extensions")
    # Assert
    with ctx:
        _load_eeg_data(uppercase_path)


# ---------------------------------------------------------------------------
# Per-extension dispatch — each test asserts the returned sentinel matches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lpath, reader_name",
    [
        ("test_file.vhdr", "brainvision"),
        ("markers.vmrk", "brainvision"),
        ("eeg_data.edf", "edf"),
        ("biosemi_data.bdf", "bdf"),
        ("general_data.gdf", "gdf"),
        ("neuroscan.cnt", "cnt"),
        ("egi_data.egi", "egi"),
        ("eeglab_data.set", "read_raw"),
    ],
)
def test_load_eeg_data_dispatches_to_expected_reader(lpath, reader_name):
    """Each extension routes to the matching ``mne.io.read_raw_*`` reader."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, _ = _make_fake_mne()
    expected_sentinel = getattr(mne_ns.io, f"read_raw_{reader_name}" if reader_name != "read_raw" else "read_raw").sentinel
    # Act
    result = _load_eeg_data(lpath, mne_module=mne_ns)
    # Assert
    assert result is expected_sentinel


# ---------------------------------------------------------------------------
# Kwargs forwarding + preload enforcement
# ---------------------------------------------------------------------------


def test_load_eeg_data_forwards_kwargs_to_reader():
    """User kwargs (other than ``preload``) reach the reader unchanged."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()
    # Act
    _load_eeg_data(
        "test.edf",
        mne_module=mne_ns,
        verbose=False,
        stim_channel="auto",
        misc=["ECG", "EOG"],
    )
    # Assert
    assert calls[0]["stim_channel"] == "auto"


def test_load_eeg_data_enforces_preload_true():
    """``preload`` is set to ``True`` even if the caller passes ``False``."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()
    # Act
    _load_eeg_data("test.cnt", mne_module=mne_ns, preload=False)
    # Assert
    assert calls[0]["preload"] is True


def test_load_eeg_data_preserves_non_preload_kwargs_when_overriding_preload():
    """Non-preload kwargs remain even when preload is stripped+re-injected."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()
    # Act
    _load_eeg_data("test.cnt", mne_module=mne_ns, preload=False, verbose=True)
    # Assert
    assert calls[0]["verbose"] is True


# ---------------------------------------------------------------------------
# .eeg companion-file detection
# ---------------------------------------------------------------------------


def test_load_eeg_data_eeg_extension_detects_brainvision_companions():
    """``.eeg`` with ``.vhdr``/``.vmrk`` companions routes to brainvision."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()

    def isfile(path):
        return path.endswith(".vhdr") or path.endswith(".vmrk")

    # Act
    result = _load_eeg_data("data.eeg", mne_module=mne_ns, isfile=isfile)
    # Assert
    assert result is mne_ns.io.read_raw_brainvision.sentinel


def test_load_eeg_data_eeg_extension_uses_vhdr_path_for_brainvision():
    """The .eeg path is rewritten to .vhdr before dispatch."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()

    def isfile(path):
        return path.endswith(".vhdr") or path.endswith(".vmrk")

    # Act
    _load_eeg_data("data.eeg", mne_module=mne_ns, isfile=isfile)
    # Assert
    assert calls[0]["lpath"] == "data.vhdr"


def test_load_eeg_data_eeg_extension_detects_nihon_koden_companions():
    """``.eeg`` with ``.21e``/``.pnt``/``.log`` companions routes to read_raw."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, _ = _make_fake_mne()

    def isfile(path):
        return path.endswith(".21e") or path.endswith(".pnt") or path.endswith(".log")

    # Act
    result = _load_eeg_data("nihon_data.eeg", mne_module=mne_ns, isfile=isfile)
    # Assert
    assert result is mne_ns.io.read_raw.sentinel


def test_load_eeg_data_eeg_extension_without_companions_raises():
    """A bare ``.eeg`` with no companion files raises ``ValueError``."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, _ = _make_fake_mne()
    # Act
    ctx = pytest.raises(ValueError, match="No associated files found for .eeg file")
    # Assert
    with ctx:
        _load_eeg_data("standalone.eeg", mne_module=mne_ns, isfile=lambda p: False)


# ---------------------------------------------------------------------------
# Reader-error propagation
# ---------------------------------------------------------------------------


def test_load_eeg_data_propagates_filenotfounderror_from_reader():
    """A ``FileNotFoundError`` from the reader bubbles up."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, _ = _make_fake_mne()

    def read_raw_edf(lpath, preload, **kwargs):
        raise FileNotFoundError("EDF file not found")

    mne_ns.io.read_raw_edf = read_raw_edf
    # Act
    ctx = pytest.raises(FileNotFoundError, match="EDF file not found")
    # Assert
    with ctx:
        _load_eeg_data("missing.edf", mne_module=mne_ns)


def test_load_eeg_data_propagates_valueerror_from_reader():
    """A ``ValueError`` from the reader bubbles up."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, _ = _make_fake_mne()

    def read_raw_bdf(lpath, preload, **kwargs):
        raise ValueError("Invalid BDF format")

    mne_ns.io.read_raw_bdf = read_raw_bdf
    # Act
    ctx = pytest.raises(ValueError, match="Invalid BDF format")
    # Assert
    with ctx:
        _load_eeg_data("invalid.bdf", mne_module=mne_ns)


# ---------------------------------------------------------------------------
# Multi-dot file paths — only the final segment is used as extension
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lpath, expected_reader",
    [
        ("file.with.dots.edf", "edf"),
        ("data.v1.0.bdf", "bdf"),
        ("experiment.session1.gdf", "gdf"),
    ],
)
def test_load_eeg_data_extracts_final_extension_only(lpath, expected_reader):
    """Multi-dot paths route by their final segment."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    mne_ns, calls = _make_fake_mne()
    # Act
    _load_eeg_data(lpath, mne_module=mne_ns)
    # Assert
    assert calls[0]["name"] == expected_reader


# ---------------------------------------------------------------------------
# Function signature
# ---------------------------------------------------------------------------


def test_load_eeg_data_signature_includes_lpath():
    """``_load_eeg_data`` accepts an ``lpath`` parameter."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    sig = inspect.signature(_load_eeg_data)
    # Assert
    assert "lpath" in sig.parameters


def test_load_eeg_data_signature_accepts_kwargs():
    """``_load_eeg_data`` accepts ``**kwargs``."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    sig = inspect.signature(_load_eeg_data)
    # Assert
    assert any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )


def test_load_eeg_data_signature_lpath_annotated_as_str():
    """``lpath`` is annotated as ``str``."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    sig = inspect.signature(_load_eeg_data)
    # Assert
    assert sig.parameters["lpath"].annotation is str


def test_load_eeg_data_signature_has_return_annotation():
    """``_load_eeg_data`` declares a return annotation."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    sig = inspect.signature(_load_eeg_data)
    # Assert
    assert sig.return_annotation is not inspect.Signature.empty


# ---------------------------------------------------------------------------
# Docstring smoke checks (single intent each)
# ---------------------------------------------------------------------------


def test_load_eeg_data_has_docstring():
    """``_load_eeg_data`` exposes a non-empty docstring."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    # Act
    docstring = _load_eeg_data.__doc__
    # Assert
    assert docstring is not None


@pytest.mark.parametrize(
    "needle",
    ["Load EEG data", "MNE-Python", "BrainVision", "EDF", "Parameters", "Returns", "Raises"],
)
def test_load_eeg_data_docstring_mentions_needle(needle):
    """Docstring mentions the documented item."""
    # Arrange
    from scitex_io._load_modules._eeg import _load_eeg_data
    docstring = _load_eeg_data.__doc__ or ""
    # Act
    present = needle in docstring
    # Assert
    assert present


if __name__ == "__main__":
    import os
    pytest.main([os.path.abspath(__file__)])
