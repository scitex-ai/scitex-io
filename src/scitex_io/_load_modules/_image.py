#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-14 07:55:38 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_load_modules/_image.py

from typing import Any

from PIL import Image


def _load_image(lpath: str, **kwargs) -> Any:
    """Load an image file.

    Parameters
    ----------
    lpath : str
        Path to the image. Supported extensions: .jpg .jpeg .png .tiff .tif.
    metadata : bool, optional
        Kept for API-compat with the rest of the stx.io.load dispatcher.
        Currently unused by the PIL backend — always stripped before
        forwarding kwargs so `PIL.Image.open` does not choke on it.
        Default: False.
    **kwargs
        Remaining kwargs forwarded to `PIL.Image.open`. Note: PIL only
        accepts `mode` and `formats` — most scitex-io-standard kwargs
        (recursive, verbose, dir, …) are also filtered below.

    Returns
    -------
    PIL.Image
    """
    # Filter out scitex-io-wide kwargs that PIL.Image.open doesn't accept.
    # `metadata` is the common one (dispatcher-level kwarg for return-shape
    # control); the rest are harmless to strip.
    _SCITEX_ONLY = {"metadata", "recursive", "verbose", "dir", "show"}
    pil_kwargs = {k: v for k, v in kwargs.items() if k not in _SCITEX_ONLY}

    supported_exts = [".jpg", ".jpeg", ".png", ".tiff", ".tif"]
    if not any(lpath.lower().endswith(ext) for ext in supported_exts):
        raise ValueError(
            f"Unsupported image format: '{lpath}'. "
            f"Supported extensions: {', '.join(supported_exts)}."
        )
    return Image.open(lpath, **pil_kwargs)


# EOF
