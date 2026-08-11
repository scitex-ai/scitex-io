#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-06 10:27:52 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-io/src/scitex_io/_load_modules/_pdf_utils.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Utility classes and functions for PDF loading.
"""

import hashlib
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional library availability flags
# ---------------------------------------------------------------------------
from scitex_dev import try_import_optional

fitz = try_import_optional("fitz")  # PyMuPDF - preferred for text and images
FITZ_AVAILABLE = fitz is not None

pdfplumber = try_import_optional("pdfplumber")  # Best for table extraction
PDFPLUMBER_AVAILABLE = pdfplumber is not None

# pypdf is the maintained successor to PyPDF2; their PdfReader API
# is source-compatible for the read paths we use here.
PyPDF2 = try_import_optional("pypdf")  # type: ignore[import-not-found]
PYPDF2_AVAILABLE = PyPDF2 is not None

pd = try_import_optional("pandas")
PANDAS_AVAILABLE = pd is not None


# ---------------------------------------------------------------------------
# DotDict
# ---------------------------------------------------------------------------
class DotDict(dict):
    """Dictionary with dot notation access."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __init__(self, dictionary=None):
        if dictionary:
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    value = DotDict(value)
                self[key] = value


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
#: Raised when no PDF backend is installed. A module-level constant rather
#: than an inline literal so it can be asserted on directly — forcing the
#: "no backend available" branch would otherwise mean faking three
#: module-level import flags, and this package does not test with mocks.
#:
#: This message is the FIRST and often ONLY thing that tells a consumer the
#: capability needs a backend at all, so it must name something that
#: actually fixes the problem. The previous version said
#: "pip install PyPDF2" — but this module imports the module `pypdf`, the
#: maintained successor, so following that instruction installed a package
#: that did NOT resolve the error. An error that names the wrong remedy is
#: worse than one that names none: it spends the reader's time and returns
#: them to the same failure.
NO_PDF_BACKEND_MESSAGE = (
    "No PDF library available. Install one of:\n"
    '  pip install "scitex-io[pdf]"        '
    "# pypdf, BSD — the default\n"
    '  pip install "scitex-io[pdf-tables]" '
    "# pdfplumber, MIT — best for tables\n"
    '  pip install "scitex-io[pdf-fast]"   '
    "# PyMuPDF, AGPL-3.0 — fastest; the licence is a deliberate choice\n"
    "\n"
    "The bare package names also work (pypdf / pdfplumber / pymupdf), but "
    "prefer the extras: they pin the versions this loader is tested against."
)

#: The DEGRADED paths, where a backend IS available but not the preferred one.
#:
#: WHY THESE ARE NOT JUST "install PyMuPDF". They used to be, and that is the
#: hole this constant closes. `pdf-fast` is deliberately EXCLUDED from
#: `scitex-io[all]` because PyMuPDF is AGPL-3.0 and `[all]` is the install you
#: choose when you do NOT know what you need -- the worst possible surface for
#: an obligation you must know you are taking on.
#:
#: An exclusion nobody is told about is not a safeguard, it is a silent
#: under-install: the user typed the documented command to get everything, did
#: not get this, and has no way to learn why. So the carve-out has to be
#: VISIBLE AT THE POINT OF FAILURE -- naming the extra AND the licence, at the
#: moment the missing backend actually costs the caller something. That
#: converts a silent omission into a stated choice, which is the only thing
#: that makes the carve-out honest rather than a hole. (scitex-dev's ruling,
#: 2026-08-11: licence beats closure because the costs differ in
#: REVERSIBILITY -- a missing capability costs one pip command, an AGPL
#: obligation you have already distributed under cannot be un-acquired.)
#:
#: Named constants rather than inline strings so a test can assert on them
#: without provoking the degraded path, which would need three import flags
#: faked and this package does not test with mocks.
MISSING_FAST_BACKEND_MESSAGE = (
    "PyMuPDF (fitz) is the preferred backend for this mode and is not "
    "installed; falling back to a slower one.\n"
    '  pip install "scitex-io[pdf-fast]"\n'
    "NOTE: PyMuPDF is AGPL-3.0. It is deliberately NOT part of "
    '"scitex-io[all]" -- taking on a copyleft obligation should be a choice '
    "you make knowingly, not something [all] hands you."
)

MISSING_TABLES_BACKEND_MESSAGE = (
    "pdfplumber is the preferred backend for table extraction and is not "
    "installed; falling back to one that does not understand tables.\n"
    '  pip install "scitex-io[pdf-tables]"   # pdfplumber, MIT'
)


def _select_backend(mode: str, requested: str) -> str:
    """Select appropriate backend based on mode and availability."""
    if requested != "auto":
        return requested

    if mode in ["tables"]:
        if PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        else:
            logger.warning(MISSING_TABLES_BACKEND_MESSAGE)
            return "fitz" if FITZ_AVAILABLE else "pypdf2"

    elif mode in ["images", "scientific", "full"]:
        if FITZ_AVAILABLE:
            return "fitz"
        else:
            logger.warning(MISSING_FAST_BACKEND_MESSAGE)
            return "pdfplumber" if PDFPLUMBER_AVAILABLE else "pypdf2"

    else:  # text, sections, metadata, pages
        if FITZ_AVAILABLE:
            return "fitz"
        elif PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        elif PYPDF2_AVAILABLE:
            return "pypdf2"
        else:
            raise ImportError(NO_PDF_BACKEND_MESSAGE)


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------
def _clean_pdf_text(text: str) -> str:
    """Clean extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Fix hyphenated words at line breaks
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

    # Remove page numbers (common patterns)
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)
    text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", text, flags=re.IGNORECASE)

    # Clean up common PDF artifacts
    text = text.replace("\x00", "")  # Null bytes
    text = re.sub(r"[\x01-\x1f\x7f-\x9f]", "", text)  # Control characters

    # Normalize quotes and dashes
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Remove multiple consecutive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# File hash
# ---------------------------------------------------------------------------
def _calculate_file_hash(lpath: str) -> str:
    """Calculate MD5 hash of file."""
    hash_md5 = hashlib.md5()
    with open(lpath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# EOF
