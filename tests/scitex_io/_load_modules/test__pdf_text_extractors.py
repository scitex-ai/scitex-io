#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for ``_pdf_text_extractors``.

from __future__ import annotations
We don't mock pypdf. We build real PDFs and verify the extractor output.
"""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pypdf import PdfReader, PdfWriter

from scitex_io._load_modules import _pdf_text_extractors as tx
from scitex_io._load_modules._pdf_text_extractors import (
    _extract_pages,
    _extract_text,
    _extract_text_fitz,
    _extract_text_pdfplumber,
    _extract_text_pypdf2,
)


# ---------------------------------------------------------------------------
def _mk_text_pdf(path: Path, pages_text):
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(str(path)) as pdf:
        for txt in pages_text:
            fig, ax = plt.subplots()
            ax.set_axis_off()
            ax.text(0.05, 0.5, txt, fontsize=10, family="monospace")
            pdf.savefig(fig)
            plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def pdf_simple(tmp_path):
    p = tmp_path / "s.pdf"
    _mk_text_pdf(p, ["Hello PDF World"])
    return str(p)


@pytest.fixture
def pdf_multi(tmp_path):
    p = tmp_path / "m.pdf"
    _mk_text_pdf(p, ["Alpha page one", "Beta page two", "Gamma page three"])
    return str(p)


@pytest.fixture
def pdf_blank_pages(tmp_path):
    """Mix of blank and text pages — tests the ``if text.strip()`` branch."""
    p = tmp_path / "blanks.pdf"
    w = PdfWriter()
    w.add_blank_page(width=200, height=200)
    with open(p, "wb") as f:
        w.write(f)
    yield str(p)


@pytest.fixture
def pdf_encrypted(tmp_path, pdf_simple):
    src = PdfReader(pdf_simple)
    w = PdfWriter()
    for pg in src.pages:
        w.add_page(pg)
    w.encrypt("pw")
    out = tmp_path / "enc.pdf"
    with open(out, "wb") as f:
        w.write(f)
    yield str(out)


# ---------------------------------------------------------------------------
# _extract_text_pypdf2
# ---------------------------------------------------------------------------
class TestExtractTextPypdf2:
    def test_extract_with_clean_out_is_str(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=True)
        # Act
        # Assert
        # Assert
        assert isinstance(out, str)

    def test_extract_with_clean_hello_in_out_and_pdf_in_out(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=True)
        # Act
        # Assert
        # Assert
        assert "Hello" in out and "PDF" in out

    def test_extract_no_clean(self, pdf_simple):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=False)
        # Assert
        # Assert
        assert "Hello" in out

    def test_multi_page_joined(self, pdf_multi):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_multi, clean=True)
        # Assert
        # Assert
        assert "Alpha" in out and "Beta" in out and "Gamma" in out

    def test_blank_pdf_returns_empty(self, pdf_blank_pages):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_blank_pages, clean=True)
        # Assert
        # Assert
        assert out == ""

    def test_encrypted_raises_raises_exception(self, pdf_encrypted):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        with pytest.raises(Exception):
            _extract_text_pypdf2(pdf_encrypted, clean=False)

    def test_unavailable_raises_raises_importerror(self, pdf_simple, monkeypatch):
        # Force the availability flag to False to hit the early ImportError.
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(tx, "PYPDF2_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="PyPDF2 not available"):
            _extract_text_pypdf2(pdf_simple, clean=False)


# ---------------------------------------------------------------------------
# _extract_text_fitz — PyMuPDF backend (real)
# ---------------------------------------------------------------------------
class TestExtractTextFitz:
    def test_fitz_real_extraction_tx_fitz_available_and_tx_fitz_is_not_none(
        self, pdf_simple
    ):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert tx.FITZ_AVAILABLE and tx.fitz is not None

    def test_fitz_real_extraction_hello_in_out(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_text_fitz(pdf_simple, clean=True)
        # Act
        # Assert
        # Assert
        assert "Hello" in out

    def test_fitz_no_clean(self, pdf_multi):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        out = _extract_text_fitz(pdf_multi, clean=False)
        # Assert
        assert all(piece in out for piece in ("Alpha", "Beta", "Gamma"))

    def test_fitz_unavailable_raises(self, pdf_simple, monkeypatch):
        # Force the availability flag to False (and clear ``fitz``) to hit
        # the explicit ImportError branch.
        # Arrange
        # Arrange
        monkeypatch.setattr(tx, "FITZ_AVAILABLE", False)
        # Act
        # Act
        monkeypatch.setattr(tx, "fitz", None)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="PyMuPDF"):
            _extract_text_fitz(pdf_simple, clean=False)

    def test_fitz_error_path(self, tmp_path):
        # Garbage file → fitz.open raises → caught and re-raised by us.
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        # Act
        # Act
        bad.write_bytes(b"not a pdf at all")
        # Assert
        # Assert
        with pytest.raises(Exception):
            _extract_text_fitz(str(bad), clean=False)


# ---------------------------------------------------------------------------
# _extract_text_pdfplumber — pdfplumber backend (real)
# ---------------------------------------------------------------------------
class TestExtractTextPdfplumber:
    def test_pdfplumber_real_extraction_tx_pdfplumber_available(self, pdf_simple):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert tx.PDFPLUMBER_AVAILABLE

    def test_pdfplumber_real_extraction_hello_in_out(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_text_pdfplumber(pdf_simple, clean=True)
        # Act
        # Assert
        # Assert
        assert "Hello" in out

    def test_pdfplumber_no_clean(self, pdf_multi):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        out = _extract_text_pdfplumber(pdf_multi, clean=False)
        # Assert
        assert all(piece in out for piece in ("Alpha", "Beta", "Gamma"))

    def test_pdfplumber_unavailable_raises(self, pdf_simple, monkeypatch):
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(tx, "PDFPLUMBER_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="pdfplumber"):
            _extract_text_pdfplumber(pdf_simple, clean=False)

    def test_pdfplumber_error_path(self, tmp_path):
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        # Act
        # Act
        bad.write_bytes(b"not a pdf at all")
        # Assert
        # Assert
        with pytest.raises(Exception):
            _extract_text_pdfplumber(str(bad), clean=False)


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------
class TestExtractText:
    def test_dispatch_pypdf2_hello_in_out(self, pdf_simple):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "pypdf2", clean=True)
        # Assert
        # Assert
        assert "Hello" in out

    def test_dispatch_unknown_falls_back_to_pypdf2(self, pdf_simple):
        # Source: anything other than 'fitz'/'pdfplumber' uses pypdf2.
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "anything_else", clean=True)
        # Assert
        # Assert
        assert "Hello" in out

    def test_dispatch_fitz_hello_in_out(self, pdf_simple):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "fitz", clean=True)
        # Assert
        # Assert
        assert "Hello" in out

    def test_dispatch_pdfplumber_hello_in_out(self, pdf_simple):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "pdfplumber", clean=True)
        # Assert
        # Assert
        assert "Hello" in out


# ---------------------------------------------------------------------------
# _extract_pages
# ---------------------------------------------------------------------------
class TestExtractPages:
    def test_pypdf2_multi_page_len_pages_is_3(self, pdf_multi):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert len(pages) == 3

    def test_pypdf2_multi_page_pages_0_page_number_1(self, pdf_multi):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert pages[0]["page_number"] == 1

    def test_pypdf2_multi_page_pages_1_page_number_2(self, pdf_multi):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert pages[1]["page_number"] == 2

    def test_pypdf2_multi_page_pages_2_page_number_3(self, pdf_multi):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert pages[2]["page_number"] == 3

    def test_pypdf2_no_clean_len_pages_is_1(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pypdf2", clean=False)
        # Act
        # Assert
        # Assert
        assert len(pages) == 1

    def test_pypdf2_no_clean_hello_in_pages_0_text(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pypdf2", clean=False)
        # Act
        # Assert
        # Assert
        assert "Hello" in pages[0]["text"]

    def test_unknown_backend_returns_empty(self, pdf_simple):
        # Source: only fitz/pdfplumber/pypdf2 branches populate the list.
        # Anything else (or backends whose lib is missing) returns [].
        # Arrange
        # Act
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "no_such_backend", clean=False)
        # Assert
        # Assert
        assert pages == []

    def test_fitz_backend_pages(self, pdf_multi):
        # Arrange
        # Act
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "fitz", clean=True)
        # Assert
        # Assert
        assert len(pages) == 3
        for i, p in enumerate(pages):
            assert p["page_number"] == i + 1
            assert isinstance(p["text"], str)

    def test_fitz_backend_pages_no_clean_len_pages_is_1(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "fitz", clean=False)
        # Act
        # Assert
        # Assert
        assert len(pages) == 1

    def test_fitz_backend_pages_no_clean_hello_in_pages_0_text(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "fitz", clean=False)
        # Act
        # Assert
        # Assert
        assert "Hello" in pages[0]["text"]

    def test_pdfplumber_backend_pages_len_pages_is_3(self, pdf_multi):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pdfplumber", clean=True)
        # Act
        # Assert
        # Assert
        assert len(pages) == 3

    def test_pdfplumber_backend_pages_all_p_page_number_i_1_for_i_p_in_enumerate_pages(
        self, pdf_multi
    ):
        # Arrange
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pdfplumber", clean=True)
        # Act
        # Assert
        # Assert
        assert all(p["page_number"] == i + 1 for (i, p) in enumerate(pages))

    def test_pdfplumber_backend_pages_no_clean(self, pdf_simple):
        # Arrange
        # Act
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pdfplumber", clean=False)
        # Assert
        # Assert
        assert len(pages) == 1

    def test_fitz_backend_skipped_when_unavailable(self, pdf_simple, monkeypatch):
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(tx, "FITZ_AVAILABLE", False)
        # Assert
        # Assert
        assert _extract_pages(pdf_simple, "fitz", clean=False) == []

    def test_pdfplumber_backend_skipped_when_unavailable(self, pdf_simple, monkeypatch):
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(tx, "PDFPLUMBER_AVAILABLE", False)
        # Assert
        # Assert
        assert _extract_pages(pdf_simple, "pdfplumber", clean=False) == []


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])
