#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-06 10:27:52 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-io/src/scitex_io/_load_modules/_pdf.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Enhanced PDF loading module with comprehensive extraction capabilities.

This module provides advanced PDF extraction for scientific papers, including:
- Text extraction with formatting preservation
- Table extraction as pandas DataFrames
- Image extraction with metadata
- Section-aware text parsing
- Multiple extraction modes for different use cases
"""

import logging
import tempfile
from typing import Any, Dict

# Expose the fitz / pypdf / pdfplumber module handles at this module's
# top level so tests that `mock.patch("scitex_io._load_modules._pdf.fitz")`
# can find them. They're re-imported here (not re-exported from
# _pdf_utils) so the patched value affects only this module's view.
from scitex_dev import try_import_optional

from ._pdf_utils import (
    FITZ_AVAILABLE,
    PANDAS_AVAILABLE,
    PDFPLUMBER_AVAILABLE,
    DotDict,
    _select_backend,
)
from ._pdf_utils import (
    PYPDF2_AVAILABLE as PYPDF2_AVAILABLE,  # re-export for test patches
)

fitz = try_import_optional("fitz")  # PyMuPDF
pdfplumber = try_import_optional("pdfplumber")
# pypdf is the maintained successor to PyPDF2.
PyPDF2 = try_import_optional("pypdf")
from ._pdf_content_extractors import (
    _extract_images,
    _extract_metadata,
    _extract_sections,
    _extract_tables,
)
from ._pdf_text_extractors import _extract_pages, _extract_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public API alias (used by scitex_io load dispatcher)
# ---------------------------------------------------------------------------
def load_pdf(lpath: str, mode: str = "full", **kwargs) -> Any:
    """Alias for _load_pdf kept for backwards compatibility."""
    return _load_pdf(lpath, mode=mode, **kwargs)


def _load_pdf(lpath: str, mode: str = "full", **kwargs) -> Any:
    """
    Load PDF file with comprehensive extraction capabilities.

    Args:
        lpath: Path to PDF file
        mode: Extraction mode (default: 'full')
            - 'full': Complete extraction including text, sections, metadata,
              pages, tables, and images
            - 'scientific': Optimized for scientific papers (text + sections +
              tables + images + stats)
            - 'text': Plain text extraction only
            - 'sections': Section-aware text extraction
            - 'tables': Extract tables as DataFrames
            - 'images': Extract images with metadata
            - 'metadata': PDF metadata only
            - 'pages': Page-by-page extraction
        **kwargs: Additional arguments
            - backend: 'auto' (default), 'fitz', 'pdfplumber', or 'pypdf2'
            - clean_text: Clean extracted text (default: True)
            - extract_images: Extract images to files (default: False for
              'full' mode, True for 'scientific')
            - output_dir: Directory for extracted images/tables (temp dir)
            - save_as_jpg: Convert all extracted images to JPG (default: True)
            - table_settings: Dict of pdfplumber table extraction settings

    Returns:
        Extracted content based on mode:
        - 'text': str
        - 'sections': Dict[str, str]
        - 'tables': Dict[int, List[pd.DataFrame]]
        - 'images': List[Dict] with image metadata
        - 'metadata': Dict with PDF metadata
        - 'pages': List[Dict] with page content
        - 'full'/'scientific': DotDict with comprehensive extraction

    Examples:
        >>> import scitex.io as stx

        >>> # Full extraction (default)
        >>> data = stx.load("paper.pdf")
        >>> print(data['full_text'])
        >>> print(data['sections'])

        >>> # Scientific mode
        >>> paper = stx.load("paper.pdf", mode="scientific")
        >>> print(paper['text'])
        >>> print(paper['sections'])

        >>> # Simple text only
        >>> text = stx.load("paper.pdf", mode="text")

        >>> # Tables only
        >>> tables = stx.load("paper.pdf", mode="tables")
    """
    mode = kwargs.get("mode", mode)
    backend = kwargs.get("backend", "auto")
    clean_text = kwargs.get("clean_text", True)
    extract_images = kwargs.get("extract_images", False)
    output_dir = kwargs.get("output_dir", None)
    table_settings = kwargs.get("table_settings", {})

    if not os.path.exists(lpath):
        raise FileNotFoundError(f"PDF file not found: {lpath}")

    backend = _select_backend(mode, backend)

    if output_dir is None and (
        extract_images or mode in ["images", "scientific", "full"]
    ):
        output_dir = tempfile.mkdtemp(prefix="pdf_extract_")
        logger.debug(f"Using temporary directory: {output_dir}")

    if mode == "text":
        return _extract_text(lpath, backend, clean_text)
    elif mode == "sections":
        return _extract_sections(lpath, backend, clean_text)
    elif mode == "tables":
        return _extract_tables(lpath, table_settings)
    elif mode == "images":
        save_as_jpg = kwargs.get("save_as_jpg", True)
        return _extract_images(lpath, output_dir, save_as_jpg)
    elif mode == "metadata":
        return _extract_metadata(lpath, backend)
    elif mode == "pages":
        return _extract_pages(lpath, backend, clean_text)
    elif mode == "scientific":
        save_as_jpg = kwargs.get("save_as_jpg", True)
        return _extract_scientific(
            lpath, clean_text, output_dir, table_settings, save_as_jpg
        )
    elif mode == "full":
        save_as_jpg = kwargs.get("save_as_jpg", True)
        return _extract_full(
            lpath,
            backend,
            clean_text,
            extract_images,
            output_dir,
            table_settings,
            save_as_jpg,
        )
    else:
        raise ValueError(f"Unknown extraction mode: {mode}")


# ---------------------------------------------------------------------------
# Composite extractors
# ---------------------------------------------------------------------------
def _extract_scientific(
    lpath: str,
    clean_text: bool,
    output_dir: str,
    table_settings: Dict,
    save_as_jpg: bool = True,
) -> DotDict:
    """
    Optimized extraction for scientific papers.
    Extracts text, tables, images, and sections in a structured format.
    """
    result: Dict[str, Any] = {
        "pdf_path": lpath,
        "filename": os.path.basename(lpath),
        "extraction_mode": "scientific",
    }

    try:
        backend = _select_backend("text", "auto")
        result["text"] = _extract_text(lpath, backend, clean_text)
        result["sections"] = _extract_sections(lpath, backend, clean_text)
        result["metadata"] = _extract_metadata(lpath, backend)

        if PDFPLUMBER_AVAILABLE and PANDAS_AVAILABLE:
            try:
                result["tables"] = _extract_tables(lpath, table_settings)
            except Exception as e:
                logger.warning(f"Could not extract tables: {e}")
                result["tables"] = {}
        else:
            result["tables"] = {}
            logger.info("Table extraction requires pdfplumber and pandas")

        if FITZ_AVAILABLE:
            try:
                result["images"] = _extract_images(lpath, output_dir, save_as_jpg)
            except Exception as e:
                logger.warning(f"Could not extract images: {e}")
                result["images"] = []
        else:
            result["images"] = []
            logger.info("Image extraction requires PyMuPDF (fitz)")

        result["stats"] = {
            "total_chars": len(result["text"]),
            "total_words": len(result["text"].split()),
            "total_pages": result["metadata"].get("pages", 0),
            "num_sections": len(result["sections"]),
            "num_tables": sum(len(tables) for tables in result["tables"].values()),
            "num_images": len(result["images"]),
        }

        logger.info(
            f"Scientific extraction complete: "
            f"{result['stats']['total_pages']} pages, "
            f"{result['stats']['num_sections']} sections, "
            f"{result['stats']['num_tables']} tables, "
            f"{result['stats']['num_images']} images"
        )

    except Exception as e:
        logger.error(f"Error in scientific extraction: {e}")
        result["error"] = str(e)

    return DotDict(result)


def _extract_full(
    lpath: str,
    backend: str,
    clean: bool,
    extract_images: bool,
    output_dir: str,
    table_settings: Dict,
    save_as_jpg: bool = True,
) -> DotDict:
    """Extract comprehensive data from PDF."""
    result: Dict[str, Any] = {
        "pdf_path": lpath,
        "filename": os.path.basename(lpath),
        "backend": backend,
        "extraction_params": {
            "clean_text": clean,
            "extract_images": extract_images,
        },
    }

    try:
        result["full_text"] = _extract_text(lpath, backend, clean)
        result["sections"] = _extract_sections(lpath, backend, clean)
        result["metadata"] = _extract_metadata(lpath, backend)
        result["pages"] = _extract_pages(lpath, backend, clean)

        if PDFPLUMBER_AVAILABLE and PANDAS_AVAILABLE:
            try:
                result["tables"] = _extract_tables(lpath, table_settings)
            except Exception as e:
                logger.warning(f"Could not extract tables: {e}")
                result["tables"] = {}

        if extract_images and FITZ_AVAILABLE:
            try:
                result["images"] = _extract_images(lpath, output_dir, save_as_jpg)
            except Exception as e:
                logger.warning(f"Could not extract images: {e}")
                result["images"] = []

        result["stats"] = {
            "total_chars": len(result["full_text"]),
            "total_words": len(result["full_text"].split()),
            "total_pages": len(result["pages"]),
            "num_sections": len(result["sections"]),
            "num_tables": sum(
                len(tables) for tables in result.get("tables", {}).values()
            ),
            "num_images": len(result.get("images", [])),
            "avg_words_per_page": (
                len(result["full_text"].split()) / len(result["pages"])
                if result["pages"]
                else 0
            ),
        }

    except Exception as e:
        logger.error(f"Error in full extraction: {e}")
        result["error"] = str(e)

    return DotDict(result)


# EOF
