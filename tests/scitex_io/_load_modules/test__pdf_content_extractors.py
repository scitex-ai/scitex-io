#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for ``_pdf_content_extractors``.

from __future__ import annotations
Builds real PDFs and exercises section parsing, metadata extraction
(pypdf2 backend), and the unavailable-library branches of the table /
image / fitz / pdfplumber paths.
"""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pypdf import PdfReader, PdfWriter

from scitex_io._load_modules import _pdf_content_extractors as ce
from scitex_io._load_modules._pdf_content_extractors import (
    _extract_images,
    _extract_metadata,
    _extract_metadata_fitz,
    _extract_metadata_pdfplumber,
    _extract_metadata_pypdf2,
    _extract_sections,
    _extract_tables,
    _parse_sections,
    _save_image,
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


@pytest.fixture
def pdf_simple(tmp_path):
    p = tmp_path / "s.pdf"
    _mk_text_pdf(p, ["hello world"])
    return str(p)


@pytest.fixture
def pdf_with_meta(tmp_path):
    """A real PDF where the producer/author metadata is filled in."""
    src = tmp_path / "tmp_src.pdf"
    _mk_text_pdf(src, ["body"])
    out = tmp_path / "meta.pdf"

    r = PdfReader(str(src))
    w = PdfWriter()
    for pg in r.pages:
        w.add_page(pg)
    w.add_metadata(
        {
            "/Title": "Test Title",
            "/Author": "Jane Doe",
            "/Subject": "Subject text",
            "/Creator": "Tester",
            "/Producer": "Producer X",
            "/CreationDate": "D:20240101000000",
            "/ModDate": "D:20240202000000",
        }
    )
    with open(out, "wb") as f:
        w.write(f)
    yield str(out)


# ---------------------------------------------------------------------------
# _parse_sections
# ---------------------------------------------------------------------------
class TestParseSections:
    def test_no_headers_means_all_frontpage_frontpage_in_out(self):
        # Arrange
        # Arrange
        # Act
        out = _parse_sections("just a line\nanother line")
        # Act
        # Assert
        # Assert
        assert "frontpage" in out

    def test_no_headers_means_all_frontpage_just_a_line_in_out_frontpage(self):
        # Arrange
        # Arrange
        # Act
        out = _parse_sections("just a line\nanother line")
        # Act
        # Assert
        # Assert
        assert "just a line" in out["frontpage"]

    def test_recognises_imrad_headers_frontpage_in_out(self):
        # Arrange
        # Arrange
        text = (
            "title line\n"
            "abstract\n"
            "abstract body line 1\n"
            "abstract body line 2\n"
            "introduction\n"
            "intro body\n"
            "methods\n"
            "method body\n"
            "results\n"
            "result body\n"
            "discussion\n"
            "disc body\n"
            "references\n"
            "ref body"
        )
        # Act
        out = _parse_sections(text)
        # Act
        # Assert
        # Assert
        assert "frontpage" in out

    def test_recognises_imrad_headers_all_s_in_out_for_s_in_abstract_introduction_methods_results_(
        self,
    ):
        # Arrange
        # Arrange
        text = (
            "title line\n"
            "abstract\n"
            "abstract body line 1\n"
            "abstract body line 2\n"
            "introduction\n"
            "intro body\n"
            "methods\n"
            "method body\n"
            "results\n"
            "result body\n"
            "discussion\n"
            "disc body\n"
            "references\n"
            "ref body"
        )
        # Act
        out = _parse_sections(text)
        # Act
        # Assert
        # Assert
        assert all(
            s in out
            for s in (
                "abstract",
                "introduction",
                "methods",
                "results",
                "discussion",
                "references",
            )
        ), f"missing section {s}: {list(out)}"

    def test_recognises_imrad_headers_method_body_in_out_methods(self):
        # Arrange
        # Arrange
        text = (
            "title line\n"
            "abstract\n"
            "abstract body line 1\n"
            "abstract body line 2\n"
            "introduction\n"
            "intro body\n"
            "methods\n"
            "method body\n"
            "results\n"
            "result body\n"
            "discussion\n"
            "disc body\n"
            "references\n"
            "ref body"
        )
        # Act
        out = _parse_sections(text)
        # Act
        # Assert
        # Assert
        assert "method body" in out["methods"]

    def test_long_header_not_treated_as_header_frontpage_in_out(self):
        # A line that matches a section regex but is >= 50 chars should NOT
        # be promoted; in fact, "abstract " followed by content makes
        # ``re.match(r"^abstract\s*$", ...)`` fail anyway, but the LEN guard
        # in the source covers a separate branch when the regex matches a
        # short header. Use a long matching line to exercise the not-header
        # path explicitly.
        # Arrange
        # Arrange
        long_line = "methodology" + " " * 60  # length > 50 once stripped? no -
        # strip-len matters; build a line that matches r"^methods?\s*$"
        # but with extra whitespace padding (>=50 chars stripped).
        # ``line_stripped = line.strip()`` so padding alone won't trip the
        # length guard. We need a header-like word but length>=50 after
        # strip. e.g. "methods " plus stuff that still matches the regex —
        # impossible because regex anchors. So we instead test that a
        # non-matching line is NOT treated as header (covers the inner
        # branch by simply having `is_header` stay False).
        # Act
        out = _parse_sections("methodology approach extra words")
        # Act
        # Assert
        # Assert
        assert "frontpage" in out

    def test_long_header_not_treated_as_header_methodology_approach_in_out_frontpage(
        self,
    ):
        # A line that matches a section regex but is >= 50 chars should NOT
        # be promoted; in fact, "abstract " followed by content makes
        # ``re.match(r"^abstract\s*$", ...)`` fail anyway, but the LEN guard
        # in the source covers a separate branch when the regex matches a
        # short header. Use a long matching line to exercise the not-header
        # path explicitly.
        # Arrange
        # Arrange
        long_line = "methodology" + " " * 60  # length > 50 once stripped? no -
        # strip-len matters; build a line that matches r"^methods?\s*$"
        # but with extra whitespace padding (>=50 chars stripped).
        # ``line_stripped = line.strip()`` so padding alone won't trip the
        # length guard. We need a header-like word but length>=50 after
        # strip. e.g. "methods " plus stuff that still matches the regex —
        # impossible because regex anchors. So we instead test that a
        # non-matching line is NOT treated as header (covers the inner
        # branch by simply having `is_header` stay False).
        # Act
        out = _parse_sections("methodology approach extra words")
        # Act
        # Assert
        # Assert
        assert "methodology approach" in out["frontpage"]

    def test_summary_and_background_aliases_summary_in_out(self):
        # Arrange
        # Arrange
        # Act
        out = _parse_sections("summary\nbody\nbackground\nbg body")
        # Act
        # Assert
        # Assert
        assert "summary" in out

    def test_summary_and_background_aliases_background_in_out(self):
        # Arrange
        # Arrange
        # Act
        out = _parse_sections("summary\nbody\nbackground\nbg body")
        # Act
        # Assert
        # Assert
        assert "background" in out

    def test_empty_text_out_equals_frontpage(self):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _parse_sections("")
        # Single empty line → one frontpage entry with empty content.
        # Assert
        # Assert
        assert out == {"frontpage": ""}


# ---------------------------------------------------------------------------
# _extract_sections (full pipeline w/ real text)
# ---------------------------------------------------------------------------
class TestExtractSections:
    def test_clean_pass_out_is_dict(self, tmp_path):
        # Build a PDF whose plain text contains section-like lines on their own.
        # Arrange
        # Arrange
        pdf = tmp_path / "p.pdf"
        _mk_text_pdf(
            pdf,
            [
                "abstract\nthis is abstract body",
                "introduction\nintro words",
                "methods\nmethod words",
            ],
        )
        # Act
        out = _extract_sections(str(pdf), "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_clean_pass_any_s_in_out_for_s_in_abstract_introduction_methods(
        self, tmp_path
    ):
        # Build a PDF whose plain text contains section-like lines on their own.
        # Arrange
        # Arrange
        pdf = tmp_path / "p.pdf"
        _mk_text_pdf(
            pdf,
            [
                "abstract\nthis is abstract body",
                "introduction\nintro words",
                "methods\nmethod words",
            ],
        )
        # Act
        out = _extract_sections(str(pdf), "pypdf2", clean=True)
        # Act
        # Assert
        # Assert
        assert any(s in out for s in ("abstract", "introduction", "methods"))

    def test_no_clean_out_is_dict(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_sections(pdf_simple, "pypdf2", clean=False)
        # Act
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_no_clean_frontpage_in_out(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_sections(pdf_simple, "pypdf2", clean=False)
        # Act
        # Assert
        # Assert
        assert "frontpage" in out


# ---------------------------------------------------------------------------
# _extract_metadata
# ---------------------------------------------------------------------------
class TestExtractMetadata:
    def test_basic_fields_out_file_name_s_pdf(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["file_name"] == "s.pdf"

    def test_basic_fields_out_backend_pypdf2(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "pypdf2"

    def test_basic_fields_out_file_size_0(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["file_size"] > 0

    def test_basic_fields_md5_hash_in_out(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert "md5_hash" in out

    def test_basic_fields_out_pages_1(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["pages"] == 1

    def test_basic_fields_out_encrypted_is_false(self, pdf_simple):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["encrypted"] is False

    def test_custom_metadata_fields_out_title_test_title(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["title"] == "Test Title"

    def test_custom_metadata_fields_out_author_jane_doe(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["author"] == "Jane Doe"

    def test_custom_metadata_fields_out_subject_subject_text(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["subject"] == "Subject text"

    def test_custom_metadata_fields_out_creator_tester(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["creator"] == "Tester"

    def test_custom_metadata_fields_out_producer_producer_x(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Act
        # Assert
        # Assert
        assert out["producer"] == "Producer X"

    def test_unknown_backend_still_returns_core_fields_out_backend_unknown(
        self, pdf_simple
    ):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "unknown"

    def test_unknown_backend_still_returns_core_fields_md5_hash_in_out(
        self, pdf_simple
    ):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Act
        # Assert
        # Assert
        assert "md5_hash" in out

    def test_unknown_backend_still_returns_core_fields_pages_not_in_out(
        self, pdf_simple
    ):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Act
        # Assert
        # Assert
        assert "pages" not in out

    def test_fitz_backend_out_backend_fitz(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "fitz"

    def test_fitz_backend_out_pages_1(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Act
        # Assert
        # Assert
        assert out["pages"] == 1

    def test_fitz_backend_out_encrypted_is_false(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Act
        # Assert
        # Assert
        assert out["encrypted"] is False

    def test_fitz_backend_out_title_test_title(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Act
        # Assert
        # Assert
        assert out["title"] == "Test Title"

    def test_fitz_backend_out_author_jane_doe(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Act
        # Assert
        # Assert
        assert out["author"] == "Jane Doe"

    def test_pdfplumber_backend_out_backend_pdfplumber(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pdfplumber")
        # Act
        # Assert
        # Assert
        assert out["backend"] == "pdfplumber"

    def test_pdfplumber_backend_out_pages_1(self, pdf_with_meta):
        # Arrange
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pdfplumber")
        # Act
        # Assert
        # Assert
        assert out["pages"] == 1

    def test_fitz_branch_skipped_when_unavailable(self, pdf_simple, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setattr(ce, "FITZ_AVAILABLE", False)
        # Act
        # Act
        out = _extract_metadata(pdf_simple, "fitz")
        # No "pages" key since the fitz branch was never entered
        # Assert
        # Assert
        assert "pages" not in out

    def test_pdfplumber_branch_skipped_when_unavailable(self, pdf_simple, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setattr(ce, "PDFPLUMBER_AVAILABLE", False)
        # Act
        # Act
        out = _extract_metadata(pdf_simple, "pdfplumber")
        # Assert
        # Assert
        assert "pages" not in out


class TestExtractMetadataPypdf2Direct:
    def test_no_metadata_object_pages_in_meta(self, tmp_path):
        # A PDF without /Info dict — pypdf returns None for .metadata.
        # Arrange
        # Arrange
        src = tmp_path / "src.pdf"
        _mk_text_pdf(src, ["x"])
        out = tmp_path / "nometa.pdf"
        r = PdfReader(str(src))
        w = PdfWriter()
        for pg in r.pages:
            w.add_page(pg)
        with open(out, "wb") as f:
            w.write(f)
        meta = {"file_path": str(out), "file_name": "nometa.pdf"}
        # Act
        _extract_metadata_pypdf2(str(out), meta)
        # Act
        # Assert
        # Assert
        assert "pages" in meta

    def test_no_metadata_object_meta_pages_1(self, tmp_path):
        # A PDF without /Info dict — pypdf returns None for .metadata.
        # Arrange
        # Arrange
        src = tmp_path / "src.pdf"
        _mk_text_pdf(src, ["x"])
        out = tmp_path / "nometa.pdf"
        r = PdfReader(str(src))
        w = PdfWriter()
        for pg in r.pages:
            w.add_page(pg)
        with open(out, "wb") as f:
            w.write(f)
        meta = {"file_path": str(out), "file_name": "nometa.pdf"}
        # Act
        _extract_metadata_pypdf2(str(out), meta)
        # Act
        # Assert
        # Assert
        assert meta["pages"] == 1

    def test_error_path_swallowed(self, tmp_path):
        # Point at a non-PDF — the except branch logs and returns silently.
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        # Act
        _extract_metadata_pypdf2(str(bad), meta)
        # Function does not raise; nothing meaningful added
        # Assert
        # Assert
        assert "pages" not in meta


class TestExtractMetadataFitzDirect:
    def test_fitz_populates_meta_title_test_title(self, pdf_with_meta):
        # Arrange
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Act
        # Assert
        # Assert
        assert meta["title"] == "Test Title"

    def test_fitz_populates_meta_author_jane_doe(self, pdf_with_meta):
        # Arrange
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Act
        # Assert
        # Assert
        assert meta["author"] == "Jane Doe"

    def test_fitz_populates_meta_pages_1(self, pdf_with_meta):
        # Arrange
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Act
        # Assert
        # Assert
        assert meta["pages"] == 1

    def test_fitz_error_swallowed(self, tmp_path):
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        # Act
        _extract_metadata_fitz(str(bad), meta)
        # Assert
        # Assert
        assert "title" not in meta

    def test_fitz_function_when_fitz_none(self, pdf_simple, monkeypatch):
        # When fitz module handle is None, calling .open AttributeError →
        # the except branch swallows it.
        # Arrange
        # Arrange
        monkeypatch.setattr(ce, "fitz", None)
        meta = {}
        # Act
        # Act
        _extract_metadata_fitz(pdf_simple, meta)
        # Assert
        # Assert
        assert "title" not in meta


class TestExtractMetadataPdfplumberDirect:
    def test_pdfplumber_populates_meta_pages_1(self, pdf_with_meta):
        # Arrange
        # Arrange
        meta = {}
        # Act
        # Act
        _extract_metadata_pdfplumber(pdf_with_meta, meta)
        # Assert
        # Assert
        assert meta["pages"] == 1

    def test_pdfplumber_error_swallowed(self, tmp_path):
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        # Act
        _extract_metadata_pdfplumber(str(bad), meta)
        # Nothing crashes — error logged
        # Assert
        # Assert
        assert "pages" not in meta


# ---------------------------------------------------------------------------
# _extract_tables / _extract_images — unavailable-lib paths
# ---------------------------------------------------------------------------
def _mk_table_pdf(path):
    """Build a PDF that pdfplumber can detect as containing a table.

    Tables in PDFs need ruling lines (or text aligned to a grid) for
    pdfplumber to detect them. We use reportlab's table support emulated
    via raw drawing in matplotlib — drawing visible grid lines around
    cells so pdfplumber's line-based table detection picks them up.
    """
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import Rectangle

    with PdfPages(str(path)) as pdf:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_xlim(0, 6)
        ax.set_ylim(0, 4)
        ax.set_axis_off()
        # Draw a 2x3 grid with text inside each cell, ruled.
        cells = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
        cw, ch = 2.0, 1.0
        for r in range(3):
            for c in range(3):
                x, y = c * cw, 3 - r * ch
                ax.add_patch(Rectangle((x, y), cw, ch, fill=False, edgecolor="black"))
                ax.text(x + 0.1, y + 0.3, cells[r][c], fontsize=10)
        pdf.savefig(fig)
        plt.close(fig)
    return path


def _mk_image_pdf(path):
    """Build a PDF that embeds a raster image (which fitz will then extract)."""
    import io as _io

    import numpy as np
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image

    # Make a small PNG and stuff it inside via matplotlib imshow
    arr = (np.random.default_rng(0).integers(0, 255, (8, 8, 3))).astype("uint8")
    img = Image.fromarray(arr)
    img_buf = _io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    with PdfPages(str(path)) as pdf:
        fig, ax = plt.subplots()
        ax.set_axis_off()
        ax.imshow(arr)
        pdf.savefig(fig)
        plt.close(fig)
    return path


@pytest.fixture
def pdf_with_table(tmp_path):
    return str(_mk_table_pdf(tmp_path / "table.pdf"))


@pytest.fixture
def pdf_with_image(tmp_path):
    return str(_mk_image_pdf(tmp_path / "img.pdf"))


class TestExtractTables:
    def test_real_extraction_out_is_dict(self, pdf_with_table):
        # Real pdfplumber + pandas table extraction. We don't assert on
        # exact cell content (heuristics vary) — only that it returns a
        # dict without crashing, and exercises the inner DataFrame path.
        # Arrange
        # Arrange
        import pandas as pd  # ensure available

        # Act
        # Act
        out = _extract_tables(pdf_with_table)
        # Assert
        # Assert
        assert isinstance(out, dict)
        # Whether or not pdfplumber actually finds a table depends on
        # heuristics; both outcomes traverse the function's full body.
        for page_num, dfs in out.items():
            assert isinstance(page_num, int)
            for df in dfs:
                assert isinstance(df, pd.DataFrame)

    def test_with_table_settings(self, pdf_with_table):
        # Pass non-trivial settings → exercises the ``table_settings or {}``
        # branch and the ``**table_settings`` call site.
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_tables(
            pdf_with_table,
            table_settings={"vertical_strategy": "lines"},
        )
        # Assert
        # Assert
        assert isinstance(out, dict)

    def test_raises_without_pdfplumber(self, pdf_simple, monkeypatch):
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(ce, "PDFPLUMBER_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="pdfplumber"):
            _extract_tables(pdf_simple)

    def test_raises_without_pandas(self, pdf_simple, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.setattr(ce, "PDFPLUMBER_AVAILABLE", True)
        # Act
        # Act
        monkeypatch.setattr(ce, "PANDAS_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="pandas"):
            _extract_tables(pdf_simple)

    def test_error_path_raises_exception_2(self, tmp_path):
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        # Act
        # Act
        bad.write_bytes(b"definitely not a pdf")
        # Assert
        # Assert
        with pytest.raises(Exception):
            _extract_tables(str(bad))


class TestExtractImages:
    def test_real_extraction_no_output_dir(self, pdf_with_image):
        # Arrange
        # Act
        # Arrange
        # Act
        out = _extract_images(pdf_with_image)
        # Assert
        # Assert
        assert isinstance(out, list)
        # mpl embeds the imshow image — fitz finds 1 image.
        if out:
            info = out[0]
            assert info["page"] == 1
            assert info["index"] == 0
            assert info["width"] > 0
            assert info["height"] > 0

    def test_real_extraction_with_output_dir(self, pdf_with_image, tmp_path):
        # Arrange
        # Arrange
        odir = tmp_path / "out"
        # Act
        # Act
        out = _extract_images(pdf_with_image, output_dir=str(odir), save_as_jpg=True)
        # Assert
        # Assert
        assert isinstance(out, list)
        if out:
            assert "filepath" in out[0]
            assert Path(out[0]["filepath"]).exists()

    def test_real_extraction_no_jpg_conversion(self, pdf_with_image, tmp_path):
        # Arrange
        # Arrange
        odir = tmp_path / "out2"
        # Act
        # Act
        out = _extract_images(pdf_with_image, output_dir=str(odir), save_as_jpg=False)
        # Assert
        # Assert
        assert isinstance(out, list)

    def test_raises_without_fitz(self, pdf_simple, monkeypatch):
        # Arrange
        # Act
        # Arrange
        # Act
        monkeypatch.setattr(ce, "FITZ_AVAILABLE", False)
        # Assert
        # Assert
        with pytest.raises(ImportError, match="PyMuPDF"):
            _extract_images(pdf_simple)

    def test_error_path_raises_exception_2(self, tmp_path):
        # Arrange
        # Arrange
        bad = tmp_path / "bad.pdf"
        # Act
        # Act
        bad.write_bytes(b"definitely not a pdf")
        # Assert
        # Assert
        with pytest.raises(Exception):
            _extract_images(str(bad))


# ---------------------------------------------------------------------------
# _save_image — exercise the on-disk save paths directly using a real PNG.
# ---------------------------------------------------------------------------
class TestSaveImage:
    def _png_bytes(self):
        import io as _io

        from PIL import Image

        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def _jpg_bytes(self):
        import io as _io

        from PIL import Image

        img = Image.new("RGB", (10, 10), (0, 255, 0))
        buf = _io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()

    def test_save_as_jpg_converting_png_info_ext_jpg(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_as_jpg_converting_png_info_filename_endswith_jpg(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["filename"].endswith(".jpg")

    def test_save_as_jpg_converting_png_path_info_filepath_exists(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_as_jpg_pass_through_for_jpeg_info_ext_jpg(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_as_jpg_pass_through_for_jpeg_info_filename_page_2_img_2_jpg(
        self, tmp_path
    ):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["filename"] == "page_2_img_2.jpg"

    def test_save_as_jpg_pass_through_for_jpeg_path_info_filepath_exists(
        self, tmp_path
    ):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_without_jpg_conversion_info_ext_png(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["ext"] == "png"

    def test_save_without_jpg_conversion_path_info_filepath_exists(self, tmp_path):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_without_jpg_conversion_path_info_filepath_read_bytes_4_b_x89png(
        self, tmp_path
    ):
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).read_bytes()[:4] == b"\x89PNG"

    def test_save_png_already_jpg_extension_info_ext_jpg(self, tmp_path):
        # Branch: save_as_jpg=True AND original_ext in ['jpg','jpeg'] → else branch
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._jpg_bytes(),
            original_ext="jpg",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_png_already_jpg_extension_path_info_filepath_exists(self, tmp_path):
        # Branch: save_as_jpg=True AND original_ext in ['jpg','jpeg'] → else branch
        # Arrange
        # Arrange
        info = {}
        # Act
        _save_image(
            self._jpg_bytes(),
            original_ext="jpg",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_rgb_image_no_alpha(self, tmp_path):
        # Exercise the ``elif img_pil.mode != 'RGB'`` False path
        # (RGB image → no conversion needed)
        # Arrange
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("RGB", (4, 4), (10, 20, 30))
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
        # Act
        # Act
        _save_image(
            buf.getvalue(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_palette_mode_image(self, tmp_path):
        # Exercise the ``if img_pil.mode == 'P'`` branch
        # Arrange
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("P", (4, 4), 0)
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
        # Act
        # Act
        _save_image(
            buf.getvalue(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_grayscale_alpha_image(self, tmp_path):
        # Exercise the ``LA`` mode branch
        # Arrange
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("LA", (4, 4), (128, 255))
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
        # Act
        # Act
        _save_image(
            buf.getvalue(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        # Assert
        assert info["ext"] == "jpg"

    def test_save_image_pil_unavailable_falls_back_info_ext_png(
        self, tmp_path, monkeypatch
    ):
        # Force ``import PIL.Image`` to raise so we hit the ImportError branch
        # that writes the raw bytes with the original extension.
        # Arrange
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        info = {}
        # Act
        _save_image(
            b"\x89PNG\r\n\x1a\nfake-bytes",
            original_ext="png",
            page_num=2,
            img_index=1,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["ext"] == "png"

    def test_save_image_pil_unavailable_falls_back_info_filename_page_3_img_1_png(
        self, tmp_path, monkeypatch
    ):
        # Force ``import PIL.Image`` to raise so we hit the ImportError branch
        # that writes the raw bytes with the original extension.
        # Arrange
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        info = {}
        # Act
        _save_image(
            b"\x89PNG\r\n\x1a\nfake-bytes",
            original_ext="png",
            page_num=2,
            img_index=1,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert info["filename"] == "page_3_img_1.png"

    def test_save_image_pil_unavailable_falls_back_path_info_filepath_exists(
        self, tmp_path, monkeypatch
    ):
        # Force ``import PIL.Image`` to raise so we hit the ImportError branch
        # that writes the raw bytes with the original extension.
        # Arrange
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        info = {}
        # Act
        _save_image(
            b"\x89PNG\r\n\x1a\nfake-bytes",
            original_ext="png",
            page_num=2,
            img_index=1,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Act
        # Assert
        # Assert
        assert Path(info["filepath"]).exists()


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])
