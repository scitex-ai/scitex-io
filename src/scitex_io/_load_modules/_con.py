#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-14 07:51:45 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_load_modules/_con.py

from typing import Any, Callable, Optional

try:
    import mne

    MNE_AVAILABLE = True
except ImportError:
    mne = None  # type: ignore[assignment]
    MNE_AVAILABLE = False


def _load_con(
    lpath: str,
    *,
    reader: Optional[Callable[..., Any]] = None,
    **kwargs,
) -> Any:
    """Load an MNE ``.con`` (FIF-format) file as a DataFrame.

    Parameters
    ----------
    lpath : str
        Path to the ``.con`` file.
    reader : callable, optional
        Override the underlying raw-FIF reader (``mne.io.read_raw_fif``).
        Used by tests to inject a fake raw-object factory; production
        leaves this ``None`` and uses real MNE.
    """
    if reader is None:
        if not MNE_AVAILABLE:
            raise ImportError(
                "Loading .con files requires the 'mne' package. "
                "Install with: pip install mne"
            )
        reader = mne.io.read_raw_fif
    if not lpath.endswith(".con"):
        raise ValueError("File must have .con extension")
    raw = reader(lpath, preload=True, **kwargs)
    samp_rate = raw.info["sfreq"]
    obj = raw.to_data_frame()
    obj["samp_rate"] = samp_rate
    return obj


# EOF
