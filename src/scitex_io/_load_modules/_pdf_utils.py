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
def _select_backend(mode: str, requested: str) -> str:
    """Select appropriate backend based on mode and availability."""
    if requested != "auto":
        return requested

    if mode in ["tables"]:
        if PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        else:
            logger.warning(
                "pdfplumber not available for table extraction. "
                "Install with: pip install pdfplumber"
            )
            return "fitz" if FITZ_AVAILABLE else "pypdf2"

    elif mode in ["images", "scientific", "full"]:
        if FITZ_AVAILABLE:
            return "fitz"
        else:
            logger.warning(
                "PyMuPDF (fitz) recommended for image extraction. "
                "Install with: pip install PyMuPDF"
            )
            return "pdfplumber" if PDFPLUMBER_AVAILABLE else "pypdf2"

    else:  # text, sections, metadata, pages
        if FITZ_AVAILABLE:
            return "fitz"
        elif PDFPLUMBER_AVAILABLE:
            return "pdfplumber"
        elif PYPDF2_AVAILABLE:
            return "pypdf2"
        else:
            raise ImportError(
                "No PDF library available. Install one of:\n"
                "  pip install PyMuPDF     # Recommended\n"
                "  pip install pdfplumber  # Best for tables\n"
                "  pip install PyPDF2      # Basic fallback"
            )


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
