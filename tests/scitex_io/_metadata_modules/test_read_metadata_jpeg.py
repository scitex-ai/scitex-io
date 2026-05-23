#!/usr/bin/env python3
"""Tests for read_metadata_jpeg."""

import json

import pytest

PIL = pytest.importorskip("PIL")
piexif = pytest.importorskip("piexif")

from scitex_io._metadata_modules.embed_metadata_jpeg import embed_metadata_jpeg
from scitex_io._metadata_modules.read_metadata_jpeg import read_metadata_jpeg


def _make_jpeg(path):
    img = PIL.Image.new("RGB", (8, 8), (10, 20, 30))
    img.save(str(path), "JPEG", quality=95)
    return path


def test_read_returns_none_when_no_metadata(tmp_path):
    # Arrange
    # Act
    # Arrange
    # Act
    p = _make_jpeg(tmp_path / "no_meta.jpg")
    # Assert
    # Assert
    assert read_metadata_jpeg(str(p)) is None


def test_read_json_round_trip(tmp_path):
    # Arrange
    # Arrange
    p = _make_jpeg(tmp_path / "with_meta.jpg")
    payload = {"k": "v", "n": 7}
    embed_metadata_jpeg(str(p), json.dumps(payload))
    # Act
    # Act
    out = read_metadata_jpeg(str(p))
    # Assert
    # Assert
    assert out == payload


def test_read_non_json_description_returns_raw(tmp_path):
    # Arrange
    # Arrange
    p = _make_jpeg(tmp_path / "raw.jpg")
    exif_dict = {
        "0th": {piexif.ImageIFD.ImageDescription: b"plain text"},
        "Exif": {},
        "GPS": {},
        "1st": {},
    }
    img = PIL.Image.open(str(p))
    img.save(str(p), "JPEG", quality=95, exif=piexif.dump(exif_dict))
    # Act
    # Act
    out = read_metadata_jpeg(str(p))
    # Assert
    # Assert
    assert out == {"raw": "plain text"}


def test_read_returns_none_when_no_exif(tmp_path):
    # Arrange
    # Arrange
    p = _make_jpeg(tmp_path / "no_exif.jpg")
    # No EXIF attached; should return None.
    # Act
    # Act
    out = read_metadata_jpeg(str(p))
    # Assert
    # Assert
    assert out is None
