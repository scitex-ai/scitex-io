#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real-PDF tests for ``_pdf_content_extractors``.

Builds real PDFs and exercises section parsing, metadata extraction
(pypdf2 backend), and the unavailable-library branches of the table /
image / fitz / pdfplumber paths.
"""
from __future__ import annotations

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
    def test_no_headers_creates_frontpage_key(self):
        # Arrange
        # Act
        out = _parse_sections("just a line\nanother line")
        # Assert
        assert "frontpage" in out

    def test_no_headers_frontpage_contains_first_line(self):
        # Arrange
        # Act
        out = _parse_sections("just a line\nanother line")
        # Assert
        assert "just a line" in out["frontpage"]

    def test_recognises_imrad_headers_creates_frontpage_key(self):
        # Arrange
        text = (
            "title line\n"
            "abstract\nabstract body line 1\nabstract body line 2\n"
            "introduction\nintro body\n"
            "methods\nmethod body\n"
            "results\nresult body\n"
            "discussion\ndisc body\n"
            "references\nref body"
        )
        # Act
        out = _parse_sections(text)
        # Assert
        assert "frontpage" in out

    def test_recognises_imrad_headers_creates_all_imrad_sections(self):
        # Arrange
        text = (
            "title line\n"
            "abstract\nabstract body line 1\n"
            "introduction\nintro body\n"
            "methods\nmethod body\n"
            "results\nresult body\n"
            "discussion\ndisc body\n"
            "references\nref body"
        )
        # Act
        out = _parse_sections(text)
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
        )

    def test_recognises_imrad_headers_methods_body_in_methods_section(self):
        # Arrange
        text = (
            "abstract\nabstract body line 1\n"
            "methods\nmethod body\n"
            "results\nresult body\n"
        )
        # Act
        out = _parse_sections(text)
        # Assert
        assert "method body" in out["methods"]

    def test_long_header_not_promoted_creates_frontpage_key(self):
        # Arrange
        # Act
        out = _parse_sections("methodology approach extra words")
        # Assert
        assert "frontpage" in out

    def test_long_header_not_promoted_keeps_text_in_frontpage(self):
        # Arrange
        # Act
        out = _parse_sections("methodology approach extra words")
        # Assert
        assert "methodology approach" in out["frontpage"]

    def test_summary_alias_creates_summary_section(self):
        # Arrange
        # Act
        out = _parse_sections("summary\nbody\nbackground\nbg body")
        # Assert
        assert "summary" in out

    def test_background_alias_creates_background_section(self):
        # Arrange
        # Act
        out = _parse_sections("summary\nbody\nbackground\nbg body")
        # Assert
        assert "background" in out

    def test_empty_text_returns_empty_frontpage_dict(self):
        # Arrange
        # Act
        out = _parse_sections("")
        # Assert
        assert out == {"frontpage": ""}


# ---------------------------------------------------------------------------
# _extract_sections (full pipeline w/ real text)
# ---------------------------------------------------------------------------
class TestExtractSections:
    def test_clean_pass_returns_dict(self, tmp_path):
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
        # Assert
        assert isinstance(out, dict)

    def test_clean_pass_finds_at_least_one_imrad_section(self, tmp_path):
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
        # Assert
        assert any(s in out for s in ("abstract", "introduction", "methods"))

    def test_no_clean_returns_dict(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_sections(pdf_simple, "pypdf2", clean=False)
        # Assert
        assert isinstance(out, dict)

    def test_no_clean_creates_frontpage_key(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_sections(pdf_simple, "pypdf2", clean=False)
        # Assert
        assert "frontpage" in out


# ---------------------------------------------------------------------------
# _extract_metadata
# ---------------------------------------------------------------------------
class TestExtractMetadata:
    def test_basic_fields_file_name_is_source_filename(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert out["file_name"] == "s.pdf"

    def test_basic_fields_backend_is_pypdf2(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert out["backend"] == "pypdf2"

    def test_basic_fields_file_size_is_positive(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert out["file_size"] > 0

    def test_basic_fields_has_md5_hash_key(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert "md5_hash" in out

    def test_basic_fields_pages_is_1(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert out["pages"] == 1

    def test_basic_fields_encrypted_is_false(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "pypdf2")
        # Assert
        assert out["encrypted"] is False

    def test_custom_metadata_title_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Assert
        assert out["title"] == "Test Title"

    def test_custom_metadata_author_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Assert
        assert out["author"] == "Jane Doe"

    def test_custom_metadata_subject_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Assert
        assert out["subject"] == "Subject text"

    def test_custom_metadata_creator_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Assert
        assert out["creator"] == "Tester"

    def test_custom_metadata_producer_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pypdf2")
        # Assert
        assert out["producer"] == "Producer X"

    def test_unknown_backend_returns_backend_field(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Assert
        assert out["backend"] == "unknown"

    def test_unknown_backend_has_md5_hash(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Assert
        assert "md5_hash" in out

    def test_unknown_backend_omits_pages_key(self, pdf_simple):
        # Arrange
        # Act
        out = _extract_metadata(pdf_simple, "unknown")
        # Assert
        assert "pages" not in out

    def test_fitz_backend_field_is_fitz(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Assert
        assert out["backend"] == "fitz"

    def test_fitz_backend_pages_is_1(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Assert
        assert out["pages"] == 1

    def test_fitz_backend_encrypted_is_false(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Assert
        assert out["encrypted"] is False

    def test_fitz_backend_title_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Assert
        assert out["title"] == "Test Title"

    def test_fitz_backend_author_round_trips(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "fitz")
        # Assert
        assert out["author"] == "Jane Doe"

    def test_pdfplumber_backend_field_is_pdfplumber(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pdfplumber")
        # Assert
        assert out["backend"] == "pdfplumber"

    def test_pdfplumber_backend_pages_is_1(self, pdf_with_meta):
        # Arrange
        # Act
        out = _extract_metadata(pdf_with_meta, "pdfplumber")
        # Assert
        assert out["pages"] == 1

    def test_fitz_branch_skipped_when_unavailable_omits_pages(
        self, pdf_simple, attr_restore
    ):
        # Arrange
        attr_restore.set(ce, "FITZ_AVAILABLE", False)
        # Act
        out = _extract_metadata(pdf_simple, "fitz")
        # Assert
        assert "pages" not in out

    def test_pdfplumber_branch_skipped_when_unavailable_omits_pages(
        self, pdf_simple, attr_restore
    ):
        # Arrange
        attr_restore.set(ce, "PDFPLUMBER_AVAILABLE", False)
        # Act
        out = _extract_metadata(pdf_simple, "pdfplumber")
        # Assert
        assert "pages" not in out


class TestExtractMetadataPypdf2Direct:
    def test_no_metadata_object_adds_pages_key(self, tmp_path):
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
        # Assert
        assert "pages" in meta

    def test_no_metadata_object_pages_is_1(self, tmp_path):
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
        # Assert
        assert meta["pages"] == 1

    def test_error_path_swallowed_leaves_meta_empty(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        _extract_metadata_pypdf2(str(bad), meta)
        # Assert
        assert "pages" not in meta


class TestExtractMetadataFitzDirect:
    def test_fitz_populates_title(self, pdf_with_meta):
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Assert
        assert meta["title"] == "Test Title"

    def test_fitz_populates_author(self, pdf_with_meta):
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Assert
        assert meta["author"] == "Jane Doe"

    def test_fitz_populates_pages(self, pdf_with_meta):
        # Arrange
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_with_meta, meta)
        # Assert
        assert meta["pages"] == 1

    def test_fitz_error_swallowed_leaves_meta_empty(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        _extract_metadata_fitz(str(bad), meta)
        # Assert
        assert "title" not in meta

    def test_fitz_module_none_leaves_meta_empty(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(ce, "fitz", None)
        meta = {}
        # Act
        _extract_metadata_fitz(pdf_simple, meta)
        # Assert
        assert "title" not in meta


class TestExtractMetadataPdfplumberDirect:
    def test_pdfplumber_populates_pages(self, pdf_with_meta):
        # Arrange
        meta = {}
        # Act
        _extract_metadata_pdfplumber(pdf_with_meta, meta)
        # Assert
        assert meta["pages"] == 1

    def test_pdfplumber_error_swallowed_leaves_meta_empty(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"not a pdf")
        meta = {}
        # Act
        _extract_metadata_pdfplumber(str(bad), meta)
        # Assert
        assert "pages" not in meta


# ---------------------------------------------------------------------------
# _extract_tables / _extract_images — unavailable-lib paths
# ---------------------------------------------------------------------------
def _mk_table_pdf(path):
    """Build a PDF that pdfplumber can detect as containing a table."""
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from matplotlib.patches import Rectangle

    with PdfPages(str(path)) as pdf:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.set_xlim(0, 6)
        ax.set_ylim(0, 4)
        ax.set_axis_off()
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
    def test_real_extraction_returns_dict(self, pdf_with_table):
        # Arrange
        # Act
        out = _extract_tables(pdf_with_table)
        # Assert
        assert isinstance(out, dict)

    def test_with_table_settings_returns_dict(self, pdf_with_table):
        # Arrange
        # Act
        out = _extract_tables(
            pdf_with_table,
            table_settings={"vertical_strategy": "lines"},
        )
        # Assert
        assert isinstance(out, dict)

    def test_raises_importerror_without_pdfplumber(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(ce, "PDFPLUMBER_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="pdfplumber")
        # Assert
        with ctx:
            _extract_tables(pdf_simple)

    def test_raises_importerror_without_pandas(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(ce, "PDFPLUMBER_AVAILABLE", True)
        attr_restore.set(ce, "PANDAS_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="pandas")
        # Assert
        with ctx:
            _extract_tables(pdf_simple)

    def test_error_path_raises_exception_for_bad_input(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"definitely not a pdf")
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _extract_tables(str(bad))


class TestExtractImages:
    def test_real_extraction_no_output_dir_returns_list(self, pdf_with_image):
        # Arrange
        # Act
        out = _extract_images(pdf_with_image)
        # Assert
        assert isinstance(out, list)

    def test_real_extraction_with_output_dir_returns_list(
        self, pdf_with_image, tmp_path
    ):
        # Arrange
        odir = tmp_path / "out"
        # Act
        out = _extract_images(pdf_with_image, output_dir=str(odir), save_as_jpg=True)
        # Assert
        assert isinstance(out, list)

    def test_real_extraction_no_jpg_conversion_returns_list(
        self, pdf_with_image, tmp_path
    ):
        # Arrange
        odir = tmp_path / "out2"
        # Act
        out = _extract_images(pdf_with_image, output_dir=str(odir), save_as_jpg=False)
        # Assert
        assert isinstance(out, list)

    def test_raises_importerror_without_fitz(self, pdf_simple, attr_restore):
        # Arrange
        attr_restore.set(ce, "FITZ_AVAILABLE", False)
        # Act
        ctx = pytest.raises(ImportError, match="PyMuPDF")
        # Assert
        with ctx:
            _extract_images(pdf_simple)

    def test_error_path_raises_exception_for_bad_input(self, tmp_path):
        # Arrange
        bad = tmp_path / "bad.pdf"
        bad.write_bytes(b"definitely not a pdf")
        # Act
        ctx = pytest.raises(Exception)
        # Assert
        with ctx:
            _extract_images(str(bad))


# ---------------------------------------------------------------------------
# _save_image — exercise the on-disk save paths directly using a real PNG.
# ---------------------------------------------------------------------------
def _png_bytes():
    import io as _io

    from PIL import Image

    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _jpg_bytes():
    import io as _io

    from PIL import Image

    img = Image.new("RGB", (10, 10), (0, 255, 0))
    buf = _io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestSaveImage:
    def test_save_as_jpg_converting_png_sets_ext_jpg(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert info["ext"] == "jpg"

    def test_save_as_jpg_converting_png_filename_endswith_jpg(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert info["filename"].endswith(".jpg")

    def test_save_as_jpg_converting_png_filepath_exists(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_as_jpg_pass_through_for_jpeg_sets_ext_jpg(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert info["ext"] == "jpg"

    def test_save_as_jpg_pass_through_for_jpeg_filename_pattern(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert info["filename"] == "page_2_img_2.jpg"

    def test_save_as_jpg_pass_through_for_jpeg_filepath_exists(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _jpg_bytes(),
            original_ext="jpeg",
            page_num=1,
            img_index=2,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_without_jpg_conversion_keeps_png_ext(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Assert
        assert info["ext"] == "png"

    def test_save_without_jpg_conversion_filepath_exists(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_without_jpg_conversion_file_starts_with_png_magic(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _png_bytes(),
            original_ext="png",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=False,
            image_info=info,
        )
        # Assert
        assert Path(info["filepath"]).read_bytes()[:4] == b"\x89PNG"

    def test_save_png_already_jpg_extension_sets_ext_jpg(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _jpg_bytes(),
            original_ext="jpg",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert info["ext"] == "jpg"

    def test_save_png_already_jpg_extension_filepath_exists(self, tmp_path):
        # Arrange
        info = {}
        # Act
        _save_image(
            _jpg_bytes(),
            original_ext="jpg",
            page_num=0,
            img_index=0,
            output_dir=str(tmp_path),
            save_as_jpg=True,
            image_info=info,
        )
        # Assert
        assert Path(info["filepath"]).exists()

    def test_save_rgb_image_no_alpha_sets_ext_jpg(self, tmp_path):
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("RGB", (4, 4), (10, 20, 30))
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
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
        assert info["ext"] == "jpg"

    def test_save_palette_mode_image_sets_ext_jpg(self, tmp_path):
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("P", (4, 4), 0)
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
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
        assert info["ext"] == "jpg"

    def test_save_grayscale_alpha_image_sets_ext_jpg(self, tmp_path):
        # Arrange
        import io as _io

        from PIL import Image

        img = Image.new("LA", (4, 4), (128, 255))
        buf = _io.BytesIO()
        img.save(buf, format="PNG")
        info = {}
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
        assert info["ext"] == "jpg"

    def test_save_image_pil_unavailable_falls_back_ext_png(
        self, tmp_path, attr_restore
    ):
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        attr_restore.set(builtins, "__import__", fake_import)
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
        # Assert
        assert info["ext"] == "png"

    def test_save_image_pil_unavailable_falls_back_filename_pattern(
        self, tmp_path, attr_restore
    ):
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        attr_restore.set(builtins, "__import__", fake_import)
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
        # Assert
        assert info["filename"] == "page_3_img_1.png"

    def test_save_image_pil_unavailable_falls_back_filepath_exists(
        self, tmp_path, attr_restore
    ):
        # Arrange
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *a, **kw):
            if name == "PIL" or name.startswith("PIL"):
                raise ImportError("PIL not available")
            return real_import(name, *a, **kw)

        attr_restore.set(builtins, "__import__", fake_import)
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
        # Assert
        assert Path(info["filepath"]).exists()


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__), "-v"])
