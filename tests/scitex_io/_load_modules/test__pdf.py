#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for the PDF load pipeline.

from __future__ import annotations
We use real PDFs (built with matplotlib + pypdf) and avoid mocks so that
the actual source code paths in ``_pdf``, ``_pdf_text_extractors`` and
``_pdf_content_extractors`` are exercised end-to-end.

Note: fitz (PyMuPDF) and pdfplumber are intentionally not installed in
this venv. The pypdf-backed paths are the ones meant to be reachable
here. We do NOT use ``pytest.importorskip`` to dodge code paths.
"""

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
    def test_alias_dispatches_to_load_pdf_out_is_str(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert isinstance(out, str)

    def test_alias_dispatches_to_load_pdf_hello_in_out(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "Hello" in out


# ---------------------------------------------------------------------------
# _load_pdf: dispatch + validation
# ---------------------------------------------------------------------------
class TestLoadPdfDispatch:
    def test_missing_file_raises(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            _load_pdf(str(tmp_path / "missing.pdf"))

    def test_invalid_mode_raises(self, single_page_pdf):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        with pytest.raises(ValueError, match="Unknown extraction mode"):
            _load_pdf(str(single_page_pdf), mode="bogus", backend="pypdf2")

    def test_mode_text_out_is_str(self, single_page_pdf):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="text", backend="pypdf2")
        # Assert
        # Assert
        assert isinstance(out, str) and "Hello" in out

    def test_mode_sections_out_is_dict(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="sections", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_mode_sections_frontpage_in_out(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="sections", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "frontpage" in out

    def test_mode_metadata_out_is_dict(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_mode_metadata_out_file_name_single_pdf(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["file_name"] == "single.pdf"

    def test_mode_metadata_out_pages_1(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["pages"] == 1

    def test_mode_metadata_md5_hash_in_out_and_len_out_md5_hash_32(
        self, single_page_pdf
    ):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "md5_hash" in out and len(out["md5_hash"]) == 32

    def test_mode_metadata_out_backend_pypdf2(self, single_page_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="metadata", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "pypdf2"

    def test_mode_pages_out_is_list(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="pages", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert isinstance(out, list)

    def test_mode_pages_len_out_is_5(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="pages", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert len(out) == 5

    def test_mode_full_pypdf2_out_filename_paper_pdf(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["filename"] == "paper.pdf"

    def test_mode_full_pypdf2_out_backend_pypdf2(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "pypdf2"

    def test_mode_full_pypdf2_full_text_in_out(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "full_text" in out

    def test_mode_full_pypdf2_pages_in_out_and_len_out_pages_5(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "pages" in out and len(out["pages"]) == 5

    def test_mode_full_pypdf2_stats_in_out(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "stats" in out

    def test_mode_full_pypdf2_stats_total_pages_5(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # DotDict allows dict-style access
        # Assert
        assert out["filename"] == "paper.pdf"
        assert out["backend"] == "pypdf2"
        assert "full_text" in out
        assert "pages" in out and len(out["pages"]) == 5
        assert "stats" in out
        stats = out["stats"]
        # Act
        # Assert
        assert stats["total_pages"] == 5

    def test_mode_full_pypdf2_stats_avg_words_per_page_0(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # DotDict allows dict-style access
        # Assert
        assert out["filename"] == "paper.pdf"
        assert out["backend"] == "pypdf2"
        assert "full_text" in out
        assert "pages" in out and len(out["pages"]) == 5
        assert "stats" in out
        stats = out["stats"]
        # Act
        # Assert
        assert stats["avg_words_per_page"] >= 0

    def test_mode_scientific_out_extraction_mode_scientific(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["extraction_mode"] == "scientific"

    def test_mode_scientific_text_in_out_and_sections_in_out_and_metadata_in_out(
        self, scientific_pdf
    ):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "text" in out and "sections" in out and "metadata" in out

    def test_mode_scientific_out_tables(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["tables"] == {}

    def test_mode_scientific_out_images(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert out["images"] == []

    def test_mode_scientific_stats_in_out(self, scientific_pdf):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific", backend="pypdf2")
        # Act
        # Assert
        # Assert
        assert "stats" in out

    def test_mode_tables_out_is_dict(self, single_page_pdf):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), mode="tables")
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_mode_images_out_is_list(self, single_page_pdf, tmp_path):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(
            str(single_page_pdf),
            mode="images",
            output_dir=str(tmp_path / "imgs"),
        )
        # Assert
        # Assert
        assert isinstance(out, list)

    def test_mode_tables_no_pdfplumber_raises(self, single_page_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf_content_extractors as ce

        # Act
        # Act
        monkeypatch.setattr(ce, "PDFPLUMBER_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="pdfplumber"):
            _load_pdf(str(single_page_pdf), mode="tables")

    def test_mode_images_no_fitz_raises(self, single_page_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf_content_extractors as ce

        # Act
        # Act
        monkeypatch.setattr(ce, "FITZ_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="PyMuPDF"):
            _load_pdf(str(single_page_pdf), mode="images")

    def test_mode_full_with_fitz_extract_images_full_text_in_out(
        self, scientific_pdf, tmp_path
    ):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg"),
        )
        # Act
        # Assert
        # Assert
        assert "full_text" in out

    def test_mode_full_with_fitz_extract_images_images_in_out(
        self, scientific_pdf, tmp_path
    ):
        # Arrange
        # Arrange
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg"),
        )
        # Act
        # Assert
        # Assert
        assert "images" in out

    def test_full_extract_images_error_branch(
        self, scientific_pdf, tmp_path, monkeypatch
    ):
        # Make _extract_images raise to exercise the inner except-clause.
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        monkeypatch.setattr(pmod, "_extract_images", boom)
        # Act
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="fitz",
            extract_images=True,
            output_dir=str(tmp_path / "fimg2"),
        )
        # The inner except in _extract_full assigns result["images"] = []
        # Assert
        # Assert
        assert out.get("images") == []

    def test_full_tables_error_branch(self, scientific_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        monkeypatch.setattr(pmod, "_extract_tables", boom)
        # Act
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="fitz")
        # Assert
        # Assert
        assert out.get("tables") == {}

    def test_scientific_tables_error_branch(self, scientific_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        monkeypatch.setattr(pmod, "_extract_tables", boom)
        # Act
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        # Assert
        assert out["tables"] == {}

    def test_scientific_images_error_branch(self, scientific_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        def boom(*a, **k):
            raise RuntimeError("forced")

        monkeypatch.setattr(pmod, "_extract_images", boom)
        # Act
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        # Assert
        assert out["images"] == []

    def test_scientific_tables_unavailable_branch(self, scientific_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        monkeypatch.setattr(pmod, "PDFPLUMBER_AVAILABLE", False)
        # Act
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        # Assert
        assert out["tables"] == {}

    def test_scientific_images_unavailable_branch(self, scientific_pdf, monkeypatch):
        # Arrange
        # Arrange
        from scitex_io._load_modules import _pdf as pmod

        monkeypatch.setattr(pmod, "FITZ_AVAILABLE", False)
        # Act
        # Act
        out = _load_pdf(str(scientific_pdf), mode="scientific")
        # Assert
        # Assert
        assert out["images"] == []

    def test_kwargs_mode_override(self, single_page_pdf):
        """Passing mode as a kwarg also works."""
        # Arrange
        # Act
        out = _load_pdf(str(single_page_pdf), backend="pypdf2", mode="text")
        # Assert
        assert isinstance(out, str)

    def test_output_dir_autocreated_for_full(self, scientific_pdf):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(str(scientific_pdf), mode="full", backend="pypdf2")
        # No explicit error and we have results
        # Assert
        # Assert
        assert "full_text" in out

    def test_explicit_output_dir(self, scientific_pdf, tmp_path):
        # Arrange
        # Arrange
        odir = tmp_path / "imgs"
        # Act
        # Act
        out = _load_pdf(
            str(scientific_pdf),
            mode="full",
            backend="pypdf2",
            output_dir=str(odir),
        )
        # Assert
        # Assert
        assert "full_text" in out


# ---------------------------------------------------------------------------
# Encrypted / malformed PDFs propagate errors out of _load_pdf via the
# extractor exception handling.
# ---------------------------------------------------------------------------
class TestErrorPaths:
    def test_encrypted_pdf_text_extraction_raises(self, encrypted_pdf):
        # Arrange
        # Act
        # Arrange
        # Act
        from pypdf.errors import FileNotDecryptedError

        # Assert
        # Assert
        with pytest.raises(FileNotDecryptedError):
            _load_pdf(str(encrypted_pdf), mode="text", backend="pypdf2")

    def test_malformed_pdf_text_extraction_raises(self, malformed_pdf):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        with pytest.raises(Exception):
            _load_pdf(str(malformed_pdf), mode="text", backend="pypdf2")

    def test_scientific_catches_error_branch(self, malformed_pdf):
        # Scientific mode swallows the inner error and writes it to result["error"].
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(str(malformed_pdf), mode="scientific", backend="pypdf2")
        # Assert
        # Assert
        assert "error" in out

    def test_full_catches_error_branch(self, malformed_pdf):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _load_pdf(str(malformed_pdf), mode="full", backend="pypdf2")
        # Assert
        # Assert
        assert "error" in out


# ---------------------------------------------------------------------------
# Docstring / signature sanity (cheap)
# ---------------------------------------------------------------------------
class TestSignature:
    def test_has_docstring_load_pdf_doc_and_pdf_in_load_pdf_doc(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert _load_pdf.__doc__ and "PDF" in _load_pdf.__doc__

    def test_signature_params_lpath_in_sig_parameters(self):
        # Arrange
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(_load_pdf)
        # Act
        # Assert
        # Assert
        assert "lpath" in sig.parameters

    def test_signature_params_sig_parameters_mode_default_full(self):
        # Arrange
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(_load_pdf)
        # Act
        # Assert
        # Assert
        assert sig.parameters["mode"].default == "full"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__), "-v"])
