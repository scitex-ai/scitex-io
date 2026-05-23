#!/usr/bin/env python3
"""Tests for embed_metadata_pdf."""

import json

import pytest

pypdf = pytest.importorskip("pypdf")

from scitex_io._metadata_modules.embed_metadata_pdf import embed_metadata_pdf


def test_embed_pdf_round_trip_reader_metadata_title_t(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "a.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    payload = json.dumps({"hello": "world"})
    embed_metadata_pdf(str(p), payload, metadata={"title": "T", "author": "A"})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Title"] == "T"


def test_embed_pdf_round_trip_reader_metadata_author_a(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "a.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    payload = json.dumps({"hello": "world"})
    embed_metadata_pdf(str(p), payload, metadata={"title": "T", "author": "A"})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Author"] == "A"


def test_embed_pdf_round_trip_reader_metadata_subject_payload(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "a.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    payload = json.dumps({"hello": "world"})
    embed_metadata_pdf(str(p), payload, metadata={"title": "T", "author": "A"})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Subject"] == payload


def test_embed_pdf_round_trip_reader_metadata_creator_scitex(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "a.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    payload = json.dumps({"hello": "world"})
    embed_metadata_pdf(str(p), payload, metadata={"title": "T", "author": "A"})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Creator"] == "SciTeX"




def test_embed_pdf_empty_metadata_keys_reader_metadata_title(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "b.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    embed_metadata_pdf(str(p), "{}", metadata={})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Title"] == ""


def test_embed_pdf_empty_metadata_keys_reader_metadata_author(tmp_path):
    # Arrange
    # Arrange
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    p = tmp_path / "b.pdf"
    with open(p, "wb") as f:
        writer.write(f)
    embed_metadata_pdf(str(p), "{}", metadata={})
    # Act
    reader = pypdf.PdfReader(str(p))
    # Act
    # Assert
    # Assert
    assert reader.metadata["/Author"] == ""


