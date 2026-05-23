#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for ``_pdf_text_extractors``.

We don't mock pypdf. We build real PDFs and verify the extractor output.
"""
from __future__ import annotations

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
    def test_extract_with_clean_returns_string(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=True)
        # Assert
        assert isinstance(out, str)

    def test_extract_with_clean_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=True)
        # Assert
        assert "Hello" in out

    def test_extract_no_clean_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_simple, clean=False)
        # Assert
        assert "Hello" in out

    def test_multi_page_joined_contains_all_markers(self, pdf_multi):
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_multi, clean=True)
        # Assert
        assert all(piece in out for piece in ("Alpha", "Beta", "Gamma"))

    def test_blank_pdf_returns_empty_string(self, pdf_blank_pages):
        # Arrange
        # Act
        out = _extract_text_pypdf2(pdf_blank_pages, clean=True)
        # Assert
        assert out == ""

    def test_encrypted_raises_exception(self, pdf_encrypted):
        # Arrange
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _extract_text_pypdf2(pdf_encrypted, clean=False)

    def test_unavailable_raises_importerror(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(tx, "PYPDF2_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="PyPDF2 not available")
        # Assert
        with ctx:
            _extract_text_pypdf2(pdf_simple, clean=False)


# ---------------------------------------------------------------------------
# _extract_text_fitz — PyMuPDF backend (real)
# ---------------------------------------------------------------------------
class TestExtractTextFitz:
    def test_fitz_availability_flag_is_true(self):
        # Arrange
        # Act
        actual = tx.FITZ_AVAILABLE
        # Assert
        assert actual

    def test_fitz_module_handle_is_not_none(self):
        # Arrange
        # Act
        actual = tx.fitz
        # Assert
        assert actual is not None

    def test_fitz_real_extraction_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text_fitz(pdf_simple, clean=True)
        # Assert
        assert "Hello" in out

    def test_fitz_no_clean_contains_all_markers(self, pdf_multi):
        # Arrange
        # Act
        out = _extract_text_fitz(pdf_multi, clean=False)
        # Assert
        assert all(piece in out for piece in ("Alpha", "Beta", "Gamma"))

    def test_fitz_unavailable_raises_importerror(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(tx, "FITZ_AVAILABLE", False)
        attr_restore.set(tx, "fitz", None)
        # Act
        ctx = pytest.raises(ImportError, match="PyMuPDF")
        # Assert
        with ctx:
            _extract_text_fitz(pdf_simple, clean=False)

    def test_fitz_error_path_raises_exception(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf at all")
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _extract_text_fitz(str(bad), clean=False)


# ---------------------------------------------------------------------------
# _extract_text_pdfplumber — pdfplumber backend (real)
# ---------------------------------------------------------------------------
class TestExtractTextPdfplumber:
    def test_pdfplumber_availability_flag_is_true(self):
        # Arrange
        # Act
        actual = tx.PDFPLUMBER_AVAILABLE
        # Assert
        assert actual

    def test_pdfplumber_real_extraction_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text_pdfplumber(pdf_simple, clean=True)
        # Assert
        assert "Hello" in out

    def test_pdfplumber_no_clean_contains_all_markers(self, pdf_multi):
        # Arrange
        # Act
        out = _extract_text_pdfplumber(pdf_multi, clean=False)
        # Assert
        assert all(piece in out for piece in ("Alpha", "Beta", "Gamma"))

    def test_pdfplumber_unavailable_raises_importerror(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(tx, "PDFPLUMBER_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="pdfplumber")
        # Assert
        with ctx:
            _extract_text_pdfplumber(pdf_simple, clean=False)

    def test_pdfplumber_error_path_raises_exception(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf at all")
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _extract_text_pdfplumber(str(bad), clean=False)


# ---------------------------------------------------------------------------
# Unified dispatcher
# ---------------------------------------------------------------------------
class TestExtractText:
    def test_dispatch_pypdf2_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "pypdf2", clean=True)
        # Assert
        assert "Hello" in out

    def test_dispatch_unknown_falls_back_to_pypdf2(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "anything_else", clean=True)
        # Assert
        assert "Hello" in out

    def test_dispatch_fitz_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "fitz", clean=True)
        # Assert
        assert "Hello" in out

    def test_dispatch_pdfplumber_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_text(pdf_simple, "pdfplumber", clean=True)
        # Assert
        assert "Hello" in out


# ---------------------------------------------------------------------------
# _extract_pages
# ---------------------------------------------------------------------------
class TestExtractPages:
    def test_pypdf2_multi_page_returns_three_pages(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Assert
        assert len(pages) == 3

    def test_pypdf2_multi_page_first_page_number_is_1(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Assert
        assert pages[0]["page_number"] == 1

    def test_pypdf2_multi_page_second_page_number_is_2(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Assert
        assert pages[1]["page_number"] == 2

    def test_pypdf2_multi_page_third_page_number_is_3(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pypdf2", clean=True)
        # Assert
        assert pages[2]["page_number"] == 3

    def test_pypdf2_no_clean_returns_one_page(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pypdf2", clean=False)
        # Assert
        assert len(pages) == 1

    def test_pypdf2_no_clean_first_page_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pypdf2", clean=False)
        # Assert
        assert "Hello" in pages[0]["text"]

    def test_unknown_backend_returns_empty_list(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "no_such_backend", clean=False)
        # Assert
        assert pages == []

    def test_fitz_backend_returns_three_pages(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "fitz", clean=True)
        # Assert
        assert len(pages) == 3

    def test_fitz_backend_pages_no_clean_returns_one_page(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "fitz", clean=False)
        # Assert
        assert len(pages) == 1

    def test_fitz_backend_pages_no_clean_contains_hello(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "fitz", clean=False)
        # Assert
        assert "Hello" in pages[0]["text"]

    def test_pdfplumber_backend_returns_three_pages(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pdfplumber", clean=True)
        # Assert
        assert len(pages) == 3

    def test_pdfplumber_backend_page_numbers_are_sequential(self, pdf_multi):
        # Arrange
        # Act
        pages = _extract_pages(pdf_multi, "pdfplumber", clean=True)
        # Assert
        assert all(p["page_number"] == i + 1 for (i, p) in enumerate(pages))

    def test_pdfplumber_backend_no_clean_returns_one_page(self, pdf_simple):
        # Arrange
        # Act
        pages = _extract_pages(pdf_simple, "pdfplumber", clean=False)
        # Assert
        assert len(pages) == 1

    def test_fitz_backend_skipped_when_unavailable_returns_empty(
        self, pdf_simple, attr_restore
    ):
        # Arrange
        attr_restore.set(tx, "FITZ_AVAILABLE", False)
        # Act
        pages = _extract_pages(pdf_simple, "fitz", clean=False)
        # Assert
        assert pages == []

    def test_pdfplumber_backend_skipped_when_unavailable_returns_empty(
        self, pdf_simple, attr_restore
    ):
        # Arrange
        attr_restore.set(tx, "PDFPLUMBER_AVAILABLE", False)
        # Act
        pages = _extract_pages(pdf_simple, "pdfplumber", clean=False)
        # Assert
        assert pages == []


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])
