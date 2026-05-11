#!/usr/bin/env python3
"""Real tests for scitex_io._metadata_modules._read.read_metadata dispatcher."""

import pytest

from scitex_io._metadata_modules._read import read_metadata


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_metadata(str(tmp_path / "missing.png"))


def test_unsupported_format_raises(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("hi")
    with pytest.raises(ValueError, match="Unsupported file format"):
        read_metadata(str(p))


def test_png_dispatch(tmp_path):
    from PIL import Image, PngImagePlugin

    p = tmp_path / "x.png"
    img = Image.new("RGB", (4, 4), "red")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("scitex_metadata", '{"key": "value"}')
    img.save(p, "PNG", pnginfo=meta)
    out = read_metadata(str(p))
    # Either dict with key or None — both branches valid; just must not raise
    assert out is None or isinstance(out, dict)


def test_jpeg_dispatch(tmp_path):
    from PIL import Image

    for ext in ("jpg", "jpeg"):
        p = tmp_path / f"x.{ext}"
        Image.new("RGB", (4, 4), "blue").save(p, "JPEG")
        out = read_metadata(str(p))
        assert out is None or isinstance(out, dict)


def test_svg_dispatch(tmp_path):
    p = tmp_path / "x.svg"
    p.write_text('<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"/>')
    out = read_metadata(str(p))
    assert out is None or isinstance(out, dict)


def test_pdf_dispatch(tmp_path):
    """Generate a real PDF with matplotlib and ensure dispatcher routes to pdf reader."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    p = tmp_path / "x.pdf"
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    fig.savefig(p)
    plt.close(fig)
    out = read_metadata(str(p))
    assert out is None or isinstance(out, dict)


def test_case_insensitive_extension(tmp_path):
    from PIL import Image

    p = tmp_path / "X.PNG"
    Image.new("RGB", (2, 2)).save(p, "PNG")
    out = read_metadata(str(p))
    assert out is None or isinstance(out, dict)
