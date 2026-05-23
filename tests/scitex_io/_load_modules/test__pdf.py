#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for the PDF load pipeline.

We use real PDFs (built with matplotlib + pypdf) and avoid mocks so that
the actual source code paths in ``_pdf``, ``_pdf_text_extractors`` and
``_pdf_content_extractors`` are exercised end-to-end.

Note: fitz (PyMuPDF) and pdfplumber are intentionally not installed in
this venv. The pypdf-backed paths are the ones meant to be reachable
here. We do NOT use ``pytest.importorskip`` to dodge code paths.
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pypdf import PdfReader, PdfWriter

from scitex_io._load_modules._pdf import _load_pdf, load_pdf


# ---------------------------------------------------------------------------
# Helpers: real PDF builders
# ---------------------------------------------------------------------------
def _mk_text_pdf(path: Path, pages_text):
    """Render ``pages_text`` (list of str) into a multi-page PDF using mpl."""
    from matplotlib.backends.backend_pdf import PdfPages

    with PdfPages(str(path)) as pdf:
        for txt in pages_text:
            fig, ax = plt.subplots()
            ax.set_axis_off()
            ax.text(0.05, 0.5, txt, fontsize=10, family="monospace")
            pdf.savefig(fig)
            plt.close(fig)
    return path


def _mk_encrypted_pdf(path: Path, body_path: Path):
    r = PdfReader(str(body_path))
    w = PdfWriter()
    for p in r.pages:
        w.add_page(p)
    w.encrypt("password123")
    with open(path, "wb") as f:
        w.write(f)
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def single_page_pdf(tmp_path):
    p = tmp_path / "single.pdf"
    _mk_text_pdf(p, ["Hello World"])
    return p


@pytest.fixture
def scientific_pdf(tmp_path):
    """Multi-page PDF whose lines include IMRaD-style section headers."""
    p = tmp_path / "paper.pdf"
    pages = [
        "Frontpage content title\nauthors\n",
        "abstract\nThis is the abstract body.\n",
        "introduction\nIntro body sentence.\n",
        "methods\nMethod description here.\n",
        "results\nWe observed results.\nreferences\nSmith 2020.",
    ]
    _mk_text_pdf(p, pages)
    return p


@pytest.fixture
def empty_pdf(tmp_path):
    p = tmp_path / "empty.pdf"
    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    with open(p, "wb") as f:
        w.write(f)
    yield p


@pytest.fixture
def encrypted_pdf(tmp_path, single_page_pdf):
    p = tmp_path / "enc.pdf"
    _mk_encrypted_pdf(p, single_page_pdf)
    return p


@pytest.fixture
def malformed_pdf(tmp_path):
    p = tmp_path / "broken.pdf"
    p.write_bytes(b"%PDF-1.4\nthis is not a real pdf body\n%%EOF\n")
    return p


# ---------------------------------------------------------------------------
# load_pdf alias / public entry
# ---------------------------------------------------------------------------
class TestLoadPdfAlias:
    def test_alias_dispatches_to_load_pdf_returns_string(self, single_page_pdf):
        # Arrange
        # Act
        out = load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Assert
        assert isinstance(out, str)

    def test_alias_dispatches_to_load_pdf_contains_hello(self, single_page_pdf):
        # Arrange
        # Act
        out = load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Assert
        assert "Hello" in out


# ---------------------------------------------------------------------------
# _load_pdf: dispatch + validation
# ---------------------------------------------------------------------------
class TestLoadPdfDispatch:
    def test_missing_file_raises_filenotfounderror(self, tmp_path):
        # Arrange
        # Act
        ctx = pytest.raises(FileNotFoundError, match="PDF file not found")
        # Assert
        with ctx:
            _load_pdf(str(tmp_path / "missing.pdf"))

    def test_invalid_mode_raises_valueerror(self, single_page_pdf):
        # Arrange
        # Act
        ctx = pytest.raises(ValueError, match="Unknown extraction mode")
        # Assert
        with ctx:
            _load_pdf(str(single_page_pdf), mode="bogus", backend="pypdf2")

    def test_mode_text_returns_string(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Assert
        assert isinstance(out, str)

    def test_mode_text_contains_hello(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Assert
        assert "Hello" in out

    def test_mode_sections_returns_dict(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="sections", backend="pypdf2")
        # Assert
        assert isinstance(out, dict)

    def test_mode_sections_has_frontpage(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="sections", backend="pypdf2")
        # Assert
        assert "frontpage" in out

    def test_mode_metadata_returns_dict(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Assert
        assert isinstance(out, dict)

    def test_mode_metadata_file_name_is_single_pdf(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Assert
        assert out["file_name"] == "single.pdf"

    def test_mode_metadata_pages_is_1(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Assert
        assert out["pages"] == 1

    def test_mode_metadata_md5_hash_length_is_32(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Assert
        assert len(out["md5_hash"]) == 32

    def test_mode_metadata_backend_is_pypdf2(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Assert
        assert out["backend"] == "pypdf2"

    def test_mode_pages_returns_list(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="pages", backend="pypdf2")
        # Assert
        assert isinstance(out, list)

    def test_mode_pages_returns_5_items(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="pages", backend="pypdf2")
        # Assert
        assert len(out) == 5

    def test_mode_full_filename_is_paper_pdf(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert out["filename"] == "paper.pdf"

    def test_mode_full_backend_is_pypdf2(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert out["backend"] == "pypdf2"

    def test_mode_full_has_full_text_key(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert "full_text" in out

    def test_mode_full_pages_length_is_5(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert len(out["pages"]) == 5

    def test_mode_full_has_stats_key(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert "stats" in out

    def test_mode_full_stats_total_pages_is_5(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert out["stats"]["total_pages"] == 5

    def test_mode_full_stats_avg_words_per_page_non_negative(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert out["stats"]["avg_words_per_page"] >= 0

    def test_mode_scientific_extraction_mode_is_scientific(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert out["extraction_mode"] == "scientific"

    def test_mode_scientific_has_text_key(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert "text" in out

    def test_mode_scientific_tables_is_empty_dict(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert out["tables"] == {}

    def test_mode_scientific_images_is_empty_list(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert out["images"] == []

    def test_mode_scientific_has_stats_key(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert "stats" in out

    def test_mode_tables_returns_dict(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="tables")
        # Assert
        assert isinstance(out, dict)

    def test_mode_images_returns_list(self, single_page_pdf, tmp_path):
        # Arrange
        # Act
        out = _load_pdf(
            str(single_page_pdf),
            mode="images",
            output_dir=str(tmp_path / "imgs"),
        )
        # Assert
        assert isinstance(out, list)

    def test_mode_tables_without_pdfplumber_raises_importerror(
        self, single_page_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf_content_extractors as ce

        attr_restore.set(ce, "PDFPLUMBER_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="pdfplumber")
        # Assert
        with ctx:
            _load_pdf(str(single_page_pdf), mode="tables")

    def test_mode_images_without_fitz_raises_importerror(
        self, single_page_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf_content_extractors as ce

        attr_restore.set(ce, "FITZ_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="PyMuPDF")
        # Assert
        with ctx:
            _load_pdf(str(single_page_pdf), mode="images")

    def test_mode_full_with_fitz_extract_images_has_full_text(
        self, scientific_pdf, tmp_path
    ):
        # Arrange
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg"),
        )
        # Assert
        assert "full_text" in out

    def test_mode_full_with_fitz_extract_images_has_images_key(
        self, scientific_pdf, tmp_path
    ):
        # Arrange
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg"),
        )
        # Assert
        assert "images" in out

    def test_full_extract_images_error_returns_empty_image_list(
        self, scientific_pdf, tmp_path, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        attr_restore.set(pmod, "_extract_images", boom)
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg2"),
        )
        # Assert
        assert out.get("images") == []

    def test_full_tables_error_returns_empty_tables_dict(
        self, scientific_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        attr_restore.set(pmod, "_extract_tables", boom)
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="fitz")
        # Assert
        assert out.get("tables") == {}

    def test_scientific_tables_error_returns_empty_tables_dict(
        self, scientific_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        attr_restore.set(pmod, "_extract_tables", boom)
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        assert out["tables"] == {}

    def test_scientific_images_error_returns_empty_images_list(
        self, scientific_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        attr_restore.set(pmod, "_extract_images", boom)
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        assert out["images"] == []

    def test_scientific_tables_unavailable_returns_empty_dict(
        self, scientific_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        attr_restore.set(pmod, "PDFPLUMBER_AVAILABLE", False)
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        assert out["tables"] == {}

    def test_scientific_images_unavailable_returns_empty_list(
        self, scientific_pdf, attr_restore
    ):
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        attr_restore.set(pmod, "FITZ_AVAILABLE", False)
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        assert out["images"] == []

    def test_kwargs_mode_override_returns_string(self, single_page_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), backend="pypdf2", mode="text")
        # Assert
        assert isinstance(out, str)

    def test_output_dir_autocreated_for_full_returns_full_text(self, scientific_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Assert
        assert "full_text" in out

    def test_explicit_output_dir_returns_full_text(self, scientific_pdf, tmp_path):
        # Arrange
        odir = tmp_path / "imgs"
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="pypdf2",
            output_dir=str(odir),
        )
        # Assert
        assert "full_text" in out


# ---------------------------------------------------------------------------
# Encrypted / malformed PDFs propagate errors out of _load_pdf via the
# extractor exception handling.
# ---------------------------------------------------------------------------
class TestErrorPaths:
    def test_encrypted_pdf_text_extraction_raises_decryption_error(
        self, encrypted_pdf
    ):
        # Arrange
        from pypdf.errors import FileNotDecryptedError

        # Act
        ctx = pytest.raises(FileNotDecryptedError)
        # Assert
        with ctx:
            _load_pdf(str(encrypted_pdf), mode="text", backend="pypdf2")

    def test_malformed_pdf_text_extraction_raises_exception(self, malformed_pdf):
        # Arrange
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _load_pdf(str(malformed_pdf), mode="text", backend="pypdf2")

    def test_scientific_catches_error_branch_returns_error_key(self, malformed_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(malformed_pdf), mode="scientific", backend="pypdf2")
        # Assert
        assert "error" in out

    def test_full_catches_error_branch_returns_error_key(self, malformed_pdf):
        # Arrange
        # Act
        out = _load_pdf(str(malformed_pdf), mode="full", backend="pypdf2")
        # Assert
        assert "error" in out


# ---------------------------------------------------------------------------
# Docstring / signature sanity (cheap)
# ---------------------------------------------------------------------------
class TestSignature:
    def test_load_pdf_has_docstring(self):
        # Arrange
        # Act
        doc = _load_pdf.__doc__
        # Assert
        assert doc is not None

    def test_load_pdf_docstring_mentions_pdf(self):
        # Arrange
        # Act
        doc = _load_pdf.__doc__
        # Assert
        assert "PDF" in doc

    def test_signature_has_lpath_parameter(self):
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(_load_pdf)
        # Assert
        assert "lpath" in sig.parameters

    def test_signature_mode_default_is_full(self):
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(_load_pdf)
        # Assert
        assert sig.parameters["mode"].default == "full"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
