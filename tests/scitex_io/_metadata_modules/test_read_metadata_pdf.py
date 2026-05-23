#!/usr/bin/env python3
"""Tests for read_metadata_pdf."""

import json

import pytest

pypdf = pytest.importorskip("pypdf")

from scitex_io._metadata_modules.embed_metadata_pdf import embed_metadata_pdf
from scitex_io._metadata_modules.read_metadata_pdf import read_metadata_pdf


def _make_pdf(path):
    from pypdf import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=72, height=72)
    with open(path, "wb") as f:
        w.write(f)
    return path


def test_read_returns_none_when_no_metadata(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    p = _make_pdf(tmp_path / "no_meta.pdf")
    # Assert
    # Assert
    assert read_metadata_pdf(str(p)) is None


def test_read_json_round_trip(tmp_path):
    # Arrange
    # Arrange
    p = _make_pdf(tmp_path / "with_meta.pdf")
    payload = {"abc": 123, "nested": {"x": 1}}
    embed_metadata_pdf(
        str(p), json.dumps(payload), metadata={"title": "T", "author": "A"}
    )
    # Act
    # Act
    out = read_metadata_pdf(str(p))
    # Assert
    # Assert
    assert out == payload


def test_read_non_json_subject_falls_back_to_field_dict(tmp_path):
    # Arrange
    # Arrange
    p = _make_pdf(tmp_path / "plain.pdf")
    # Write a Subject that isn't JSON so the parser falls into the
    # "build from available fields" branch.
    from pypdf import PdfWriter

    reader = pypdf.PdfReader(str(p))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "T2",
            "/Author": "A2",
            "/Subject": "not-json",
            "/Creator": "X",
        }
    )
    with open(p, "wb") as f:
        writer.write(f)

    # Act
    # Act
    out = read_metadata_pdf(str(p))
    # Assert
    # Assert
    assert out == {
        "title": "T2",
        "author": "A2",
        "subject": "not-json",
        "creator": "X",
    }
