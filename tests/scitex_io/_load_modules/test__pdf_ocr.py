#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for the ``ocr=`` fallback on the PDF text path.

No mocks and no monkeypatch: we build a genuine image-only PDF (a rendered
image of text, with NO text layer) and a genuine text-layer PDF with fitz,
then exercise the real extraction path.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from scitex_io._load_modules._pdf_text_extractors import _extract_text

fitz = pytest.importorskip("fitz")  # PyMuPDF; required to build the fixtures

# OCR actually runs only when scitex_cv AND its easyocr engine are importable.
_OCR_AVAILABLE = (
    importlib.util.find_spec("scitex_cv") is not None
    and importlib.util.find_spec("easyocr") is not None
)
_OCR_SKIP_REASON = "scitex_cv / easyocr not importable; OCR path skipped"


# ---------------------------------------------------------------------------
# Fixtures: real PDFs built with fitz
# ---------------------------------------------------------------------------
def _mk_image_only_pdf(path: Path, text: str) -> str:
    """A PDF whose only content is a rendered image of ``text`` (no text layer).

    We first draw the text on a scratch page, rasterise it to a pixmap, then
    embed that pixmap as an image on a fresh page. The result has no
    selectable/extractable text layer, exactly like a scanned document.
    """
    scratch = fitz.open()
    spage = scratch.new_page(width=600, height=200)
    spage.insert_text((40, 110), text, fontsize=48)
    pix = spage.get_pixmap(dpi=200)
    scratch.close()

    out = fitz.open()
    page = out.new_page(width=pix.width, height=pix.height)
    page.insert_image(page.rect, pixmap=pix)
    out.save(str(path))
    out.close()
    return str(path)


def _mk_text_pdf(path: Path, text: str) -> str:
    """A normal PDF carrying a real, extractable text layer."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=24)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def image_only_pdf(tmp_path):
    return _mk_image_only_pdf(tmp_path / "scanned.pdf", "HELLO OCR")


@pytest.fixture
def text_pdf(tmp_path):
    return _mk_text_pdf(tmp_path / "born_digital.pdf", "SAMPLE TEXT LAYER")


# ---------------------------------------------------------------------------
# (a) ocr=False on an image-only PDF -> empty text (default path unchanged)
# ---------------------------------------------------------------------------
def test_ocr_false_on_image_only_pdf_returns_empty(image_only_pdf):
    text = _extract_text(image_only_pdf, "fitz", clean=True, ocr=False)
    assert text.strip() == ""


# ---------------------------------------------------------------------------
# (b) ocr=True on a real image-only PDF -> recovers the known text
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _OCR_AVAILABLE, reason=_OCR_SKIP_REASON)
def test_ocr_true_on_image_only_pdf_recovers_text(image_only_pdf):
    text = _extract_text(image_only_pdf, "fitz", clean=True, ocr=True)
    assert "HELLO" in text.upper()


# ---------------------------------------------------------------------------
# (c) ocr=True on a normal text PDF -> still returns the text layer (no OCR)
# ---------------------------------------------------------------------------
def test_ocr_true_on_text_pdf_still_uses_text_layer(text_pdf):
    text = _extract_text(text_pdf, "fitz", clean=True, ocr=True)
    assert "SAMPLE TEXT LAYER" in text
