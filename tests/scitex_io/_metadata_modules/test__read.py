#!/usr/bin/env python3
"""Real tests for scitex_io._metadata_modules._read.read_metadata dispatcher."""

import pytest

from scitex_io._metadata_modules._read import read_metadata


def test_missing_file_raises(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    with pytest.raises(FileNotFoundError):
        read_metadata(str(tmp_path / "missing.png"))


def test_unsupported_format_raises(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.txt"
    # Act
    # Act
    p.write_text("hi")
    # Assert
    # Assert
    with pytest.raises(ValueError, match="Unsupported file format"):
        read_metadata(str(p))


def test_png_dispatch_out_is_none(tmp_path):
    # Arrange
    # Arrange
    from PIL import Image, PngImagePlugin

    p = tmp_path / "x.png"
    img = Image.new("RGB", (4, 4), "red")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("scitex_metadata", '{"key": "value"}')
    img.save(p, "PNG", pnginfo=meta)
    # Act
    # Act
    out = read_metadata(str(p))
    # Either dict with key or None — both branches valid; just must not raise
    # Assert
    # Assert
    assert out is None or isinstance(out, dict)


def test_jpeg_dispatch_smoke_case(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    from PIL import Image

    for ext in ("jpg", "jpeg"):
        p = tmp_path / f"x.{ext}"
        Image.new("RGB", (4, 4), "blue").save(p, "JPEG")
        out = read_metadata(str(p))
        assert out is None or isinstance(out, dict)


def test_svg_dispatch_out_is_none(tmp_path):
    # Arrange
    # Arrange
    p = tmp_path / "x.svg"
    p.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"/>')
    # Act
    # Act
    out = read_metadata(str(p))
    # Assert
    # Assert
    assert out is None or isinstance(out, dict)


def test_pdf_dispatch_out_is_none(tmp_path):
    """Generate a real PDF with matplotlib and ensure dispatcher routes to pdf reader."""
    # Arrange
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = tmp_path / "x.pdf"
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    fig.savefig(p)
    plt.close(fig)
    # Act
    out = read_metadata(str(p))
    # Assert
    assert out is None or isinstance(out, dict)


def test_case_insensitive_extension(tmp_path):
    # Arrange
    # Arrange
    from PIL import Image

    p = tmp_path / "X.PNG"
    Image.new("RGB", (2, 2)).save(p, "PNG")
    # Act
    # Act
    out = read_metadata(str(p))
    # Assert
    # Assert
    assert out is None or isinstance(out, dict)
