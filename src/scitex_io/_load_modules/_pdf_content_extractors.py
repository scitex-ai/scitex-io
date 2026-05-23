#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-06 10:27:52 (ywatanabe)"
# File: /home/ywatanabe/proj/scitex-io/src/scitex_io/_load_modules/_pdf_content_extractors.py
# ----------------------------------------
from __future__ import annotations

import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Content extraction functions for PDF loading:
tables, images, sections, and metadata.
"""

import logging
import re
from typing import Any, Dict, List

# Module-level handle so tests can `mock.patch(<module>.fitz)`.
from scitex_dev import try_import_optional

from ._pdf_text_extractors import _extract_text
from ._pdf_utils import (
    FITZ_AVAILABLE,
    PANDAS_AVAILABLE,
    PDFPLUMBER_AVAILABLE,
    PYPDF2_AVAILABLE,
    _calculate_file_hash,
    _clean_pdf_text,
)

fitz = try_import_optional("fitz")

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Table extraction
# ---------------------------------------------------------------------------
def _extract_tables(
    lpath: str, table_settings: Dict = None
) -> Dict[int, List["pd.DataFrame"]]:
    """
    Extract tables from PDF as pandas DataFrames.

    Returns:
        Dict mapping page numbers to list of DataFrames
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError(
            "pdfplumber required for table extraction. Install with:\n"
            "  pip install pdfplumber pandas"
        )

    if not PANDAS_AVAILABLE:
        raise ImportError("pandas required for table extraction")

    import pandas as pd
    import pdfplumber

    tables_dict = {}
    table_settings = table_settings or {}

    try:
        with pdfplumber.open(lpath) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # pdfplumber's Page.extract_tables() takes a single
                # `table_settings` dict — NOT **kwargs. The previous
                # `**table_settings` unpack raised TypeError for any
                # non-empty settings dict.
                tables = (
                    page.extract_tables(table_settings=table_settings)
                    if table_settings
                    else page.extract_tables()
                )

                if tables:
                    dfs = []
                    for table in tables:
                        if table and len(table) > 0:
                            if len(table) > 1 and all(
                                isinstance(cell, str) for cell in table[0] if cell
                            ):
                                df = pd.DataFrame(table[1:], columns=table[0])
                            else:
                                df = pd.DataFrame(table)

                            df = (
                                df.replace("", None)
                                .dropna(how="all", axis=1)
                                .dropna(how="all", axis=0)
                            )

                            if not df.empty:
                                dfs.append(df)

                    if dfs:
                        tables_dict[page_num] = dfs

        logger.info(f"Extracted tables from {len(tables_dict)} pages")
        return tables_dict

    except Exception as e:
        logger.error(f"Error extracting tables: {e}")
        raise


# ---------------------------------------------------------------------------
# Image extraction
# ---------------------------------------------------------------------------
def _extract_images(
    lpath: str, output_dir: str = None, save_as_jpg: bool = True
) -> List[Dict[str, Any]]:
    """
    Extract images from PDF with metadata.

    Args:
        lpath: Path to PDF file
        output_dir: Directory to save images (optional)
        save_as_jpg: If True, convert all images to JPG format (default: True)

    Returns:
        List of dicts containing image metadata and paths
    """
    if not FITZ_AVAILABLE:
        raise ImportError(
            "PyMuPDF (fitz) required for image extraction. Install with:\n"
            "  pip install PyMuPDF"
        )

    images_info = []

    try:
        doc = fitz.open(lpath)

        for page_num, page in enumerate(doc):
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                original_ext = base_image["ext"]

                image_info = {
                    "page": page_num + 1,
                    "index": img_index,
                    "width": base_image["width"],
                    "height": base_image["height"],
                    "colorspace": base_image["colorspace"],
                    "bpc": base_image["bpc"],
                    "original_ext": original_ext,
                    "size_bytes": len(image_bytes),
                }

                if output_dir:
                    _save_image(
                        image_bytes,
                        original_ext,
                        page_num,
                        img_index,
                        output_dir,
                        save_as_jpg,
                        image_info,
                    )

                images_info.append(image_info)

        doc.close()

        logger.info(f"Extracted {len(images_info)} images from PDF")
        return images_info

    except Exception as e:
        logger.error(f"Error extracting images: {e}")
        raise


def _save_image(
    image_bytes: bytes,
    original_ext: str,
    page_num: int,
    img_index: int,
    output_dir: str,
    save_as_jpg: bool,
    image_info: Dict,
) -> None:
    """Save a single extracted image to disk, updating image_info in place."""
    os.makedirs(output_dir, exist_ok=True)

    if save_as_jpg and original_ext not in ["jpg", "jpeg"]:
        try:
            import io

            from PIL import Image

            img_pil = Image.open(io.BytesIO(image_bytes))

            if img_pil.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img_pil.size, (255, 255, 255))
                if img_pil.mode == "P":
                    img_pil = img_pil.convert("RGBA")
                mask = img_pil.split()[-1] if img_pil.mode == "RGBA" else None
                background.paste(img_pil, mask=mask)
                img_pil = background
            elif img_pil.mode != "RGB":
                img_pil = img_pil.convert("RGB")

            filename = f"page_{page_num + 1}_img_{img_index}.jpg"
            filepath = os.path.join(output_dir, filename)
            img_pil.save(filepath, "JPEG", quality=95)
            image_info["ext"] = "jpg"

        except ImportError:
            logger.warning(
                "PIL not available for image conversion. "
                "Install with: pip install Pillow"
            )
            filename = f"page_{page_num + 1}_img_{img_index}.{original_ext}"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as img_file:
                img_file.write(image_bytes)
            image_info["ext"] = original_ext
    else:
        ext = "jpg" if original_ext == "jpeg" else original_ext
        filename = f"page_{page_num + 1}_img_{img_index}.{ext}"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as img_file:
            img_file.write(image_bytes)
        image_info["ext"] = ext

    image_info["filepath"] = filepath
    image_info["filename"] = filename


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------
def _parse_sections(text: str) -> Dict[str, str]:
    """
    Parse text into sections based on IMRaD structure.

    Sections: frontpage, abstract, introduction, methods, results,
    discussion, references.
    """
    sections = {}
    current_section = "frontpage"
    current_text = []

    section_patterns = [
        r"^abstract\s*$",
        r"^summary\s*$",
        r"^introduction\s*$",
        r"^background\s*$",
        r"^methods?\s*$",
        r"^materials?\s+and\s+methods?\s*$",
        r"^methodology\s*$",
        r"^results?\s*$",
        r"^discussion\s*$",
        r"^references?\s*$",
    ]

    lines = text.split("\n")

    for line in lines:
        line_lower = line.lower().strip()
        line_stripped = line.strip()

        is_header = False
        for pattern in section_patterns:
            if re.match(pattern, line_lower):
                if len(line_stripped) < 50:
                    if current_text:
                        sections[current_section] = "\n".join(current_text).strip()

                    current_section = line_lower.strip()
                    current_text = []
                    is_header = True
                    break

        if not is_header:
            current_text.append(line)

    if current_text:
        sections[current_section] = "\n".join(current_text).strip()

    return sections


def _extract_sections(lpath: str, backend: str, clean: bool) -> Dict[str, str]:
    """Extract text organized by sections."""
    text = _extract_text(lpath, backend, clean=False)
    sections = _parse_sections(text)

    if clean:
        for section, content in sections.items():
            sections[section] = _clean_pdf_text(content)

    return sections


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------
def _extract_metadata(lpath: str, backend: str) -> Dict[str, Any]:
    """Extract PDF metadata."""
    metadata = {
        "file_path": lpath,
        "file_name": os.path.basename(lpath),
        "file_size": os.path.getsize(lpath),
        "backend": backend,
    }

    if backend == "fitz" and FITZ_AVAILABLE:
        _extract_metadata_fitz(lpath, metadata)
    elif backend == "pdfplumber" and PDFPLUMBER_AVAILABLE:
        _extract_metadata_pdfplumber(lpath, metadata)
    elif backend == "pypdf2" and PYPDF2_AVAILABLE:
        _extract_metadata_pypdf2(lpath, metadata)

    metadata["md5_hash"] = _calculate_file_hash(lpath)
    return metadata


def _extract_metadata_fitz(lpath: str, metadata: Dict) -> None:
    """Populate metadata dict using fitz backend (in-place)."""

    try:
        doc = fitz.open(lpath)
        pdf_metadata = doc.metadata

        metadata.update(
            {
                "title": pdf_metadata.get("title", ""),
                "author": pdf_metadata.get("author", ""),
                "subject": pdf_metadata.get("subject", ""),
                "keywords": pdf_metadata.get("keywords", ""),
                "creator": pdf_metadata.get("creator", ""),
                "producer": pdf_metadata.get("producer", ""),
                "creation_date": str(pdf_metadata.get("creationDate", "")),
                "modification_date": str(pdf_metadata.get("modDate", "")),
                "pages": len(doc),
                "encrypted": doc.is_encrypted,
            }
        )

        doc.close()

    except Exception as e:
        logger.error(f"Error extracting metadata with fitz: {e}")


def _extract_metadata_pdfplumber(lpath: str, metadata: Dict) -> None:
    """Populate metadata dict using pdfplumber backend (in-place)."""
    import pdfplumber

    try:
        with pdfplumber.open(lpath) as pdf:
            metadata["pages"] = len(pdf.pages)
            if hasattr(pdf, "metadata"):
                metadata.update(pdf.metadata)
    except Exception as e:
        logger.error(f"Error extracting metadata with pdfplumber: {e}")


def _extract_metadata_pypdf2(lpath: str, metadata: Dict) -> None:
    """Populate metadata dict using pypdf backend (in-place)."""
    import pypdf as PyPDF2  # type: ignore[import-not-found]

    try:
        reader = PyPDF2.PdfReader(lpath)

        if reader.metadata:
            metadata.update(
                {
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "subject": reader.metadata.get("/Subject", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                    "producer": reader.metadata.get("/Producer", ""),
                    "creation_date": str(reader.metadata.get("/CreationDate", "")),
                    "modification_date": str(reader.metadata.get("/ModDate", "")),
                }
            )

        metadata["pages"] = len(reader.pages)
        metadata["encrypted"] = reader.is_encrypted

    except Exception as e:
        logger.error(f"Error extracting metadata with PyPDF2: {e}")


# EOF
