#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-06 10:27:52 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-io/src/scitex_io/_load_modules/_pdf_text_extractors.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Text extraction functions for PDF loading.
"""

import logging
from typing import Any, Dict, List

# Module-level handles so tests can `mock.patch(<module>.fitz)` etc.
from scitex_dev import try_import_optional

from ._pdf_utils import (
    FITZ_AVAILABLE,
    PDFPLUMBER_AVAILABLE,
    PYPDF2_AVAILABLE,
    _clean_pdf_text,
)

fitz = try_import_optional("fitz")
pdfplumber = try_import_optional("pdfplumber")
# pypdf is the maintained successor to PyPDF2 (drop-in for PdfReader).
PyPDF2 = try_import_optional("pypdf")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backend-specific text extractors
# ---------------------------------------------------------------------------
def _extract_text_fitz(lpath: str, clean: bool) -> str:
    """Extract text using PyMuPDF."""
    if not FITZ_AVAILABLE or fitz is None:
        raise ImportError("PyMuPDF (fitz) not available")

    try:
        doc = fitz.open(lpath)
        text_parts = []

        for _page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(text)

        doc.close()

        full_text = "\n".join(text_parts)

        if clean:
            full_text = _clean_pdf_text(full_text)

        return full_text

    except Exception as e:
        logger.error(f"Error extracting text with fitz from {lpath}: {e}")
        raise


def _extract_text_pdfplumber(lpath: str, clean: bool) -> str:
    """Extract text using pdfplumber."""
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber not available")

    try:
        text_parts = []
        with pdfplumber.open(lpath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

        full_text = "\n".join(text_parts)

        if clean:
            full_text = _clean_pdf_text(full_text)

        return full_text

    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber from {lpath}: {e}")
        raise


def _extract_text_pypdf2(lpath: str, clean: bool) -> str:
    """Extract text using PyPDF2."""
    if not PYPDF2_AVAILABLE:
        raise ImportError("PyPDF2 not available")

    try:
        reader = PyPDF2.PdfReader(lpath)
        text_parts = []

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)

        full_text = "\n".join(text_parts)

        if clean:
            full_text = _clean_pdf_text(full_text)

        return full_text

    except Exception as e:
        logger.error(f"Error extracting text with PyPDF2 from {lpath}: {e}")
        raise


# ---------------------------------------------------------------------------
# Unified text extractor dispatcher
# ---------------------------------------------------------------------------
def _extract_text(lpath: str, backend: str, clean: bool) -> str:
    """Extract plain text from PDF."""
    if backend == "fitz":
        return _extract_text_fitz(lpath, clean)
    elif backend == "pdfplumber":
        return _extract_text_pdfplumber(lpath, clean)
    else:
        return _extract_text_pypdf2(lpath, clean)


# ---------------------------------------------------------------------------
# Page-by-page extraction
# ---------------------------------------------------------------------------
def _extract_pages(lpath: str, backend: str, clean: bool) -> List[Dict[str, Any]]:
    """Extract content page by page."""
    pages = []

    if backend == "fitz" and FITZ_AVAILABLE:
        doc = fitz.open(lpath)

        for page_num, page in enumerate(doc):
            text = page.get_text()
            if clean:
                text = _clean_pdf_text(text)

            pages.append(
                {
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                }
            )

        doc.close()

    elif backend == "pdfplumber" and PDFPLUMBER_AVAILABLE:
        with pdfplumber.open(lpath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if clean:
                    text = _clean_pdf_text(text)

                pages.append(
                    {
                        "page_number": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                        "word_count": len(text.split()),
                    }
                )

    elif backend == "pypdf2" and PYPDF2_AVAILABLE:
        reader = PyPDF2.PdfReader(lpath)

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()
            if clean:
                text = _clean_pdf_text(text)

            pages.append(
                {
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                }
            )

    return pages


# EOF
