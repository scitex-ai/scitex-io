#!/usr/bin/env python3
"""Tests for embed_metadata_jpeg."""

import json

import pytest

PIL = pytest.importorskip("PIL")
piexif = pytest.importorskip("piexif")

from scitex_io._metadata_modules.embed_metadata_jpeg import embed_metadata_jpeg


def _make_jpeg(path, size=(10, 10), mode="RGB"):
    img = PIL.Image.new(mode, size, color=(128, 64, 32) if mode == "RGB" else 128)
    img.save(str(path), "JPEG", quality=95)
    return path


def test_embed_jpeg_round_trip(tmp_path):
    # Arrange
    # Arrange
    p = _make_jpeg(tmp_path / "a.jpg")
    payload = json.dumps({"k": "v", "n": 42})
    embed_metadata_jpeg(str(p), payload)
    exif = piexif.load(str(p))
    # Act
    # Act
    desc = exif["0th"][piexif.ImageIFD.ImageDescription].decode("utf-8")
    # Assert
    # Assert
    assert desc == payload


def test_embed_jpeg_rgba_converted(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "rgba.jpg"
    img = PIL.Image.new("RGBA", (8, 8), (10, 20, 30, 200))
    img.save(str(p), "PNG")
    embed_metadata_jpeg(str(p), json.dumps({"mode": "rgba"}))
    # Act
    # Act
    out = PIL.Image.open(str(p))
    # Assert
    # Assert
    assert out.mode == "RGB"


def test_embed_jpeg_palette_mode(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "pal.jpg"
    img = PIL.Image.new("P", (8, 8), 5)
    img.save(str(p), "PNG")
    embed_metadata_jpeg(str(p), json.dumps({"mode": "p"}))
    # Act
    # Act
    out = PIL.Image.open(str(p))
    # Assert
    # Assert
    assert out.mode == "RGB"


def test_embed_jpeg_la_mode(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "la.jpg"
    img = PIL.Image.new("LA", (8, 8), (128, 200))
    img.save(str(p), "PNG")
    embed_metadata_jpeg(str(p), json.dumps({"mode": "la"}))
    # Act
    # Act
    out = PIL.Image.open(str(p))
    # Assert
    # Assert
    assert out.mode == "RGB"


def test_embed_jpeg_preserves_other_exif(tmp_path):
    # Arrange
    # Arrange
    p = _make_jpeg(tmp_path / "b.jpg")
    exif_dict = {
        "0th": {},
        "Exif": {piexif.ExifIFD.UserComment: b"prior"},
        "GPS": {},
        "1st": {},
    }
    img = PIL.Image.open(str(p))
    img.save(str(p), "JPEG", quality=95, exif=piexif.dump(exif_dict))
    embed_metadata_jpeg(str(p), json.dumps({"k": "v"}))
    # Act
    # Act
    after = piexif.load(str(p))
    # Assert
    # Assert
    assert after["Exif"][piexif.ExifIFD.UserComment] == b"prior"
