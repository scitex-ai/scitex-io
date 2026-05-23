"""Tests for SVG metadata embedding."""

import json

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")

from scitex_io._metadata_modules.embed_metadata_svg import embed_metadata_svg


_DEFAULT_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <circle cx="50" cy="50" r="40" fill="red"/>
</svg>"""


def _write_svg(path, content=_DEFAULT_SVG):
    path.write_text(content, encoding="utf-8")


class TestEmbedMetadataSvg:
    """Tests for embed_metadata_svg function."""

    @pytest.fixture
    def simple_embedded_content(self, tmp_path):
        svg_path = tmp_path / "simple.svg"
        _write_svg(svg_path)
        embed_metadata_svg(str(svg_path), json.dumps({"test": "value", "number": 42}))
        return svg_path.read_text(encoding="utf-8")

    @pytest.fixture
    def overwritten_content(self, tmp_path):
        svg_path = tmp_path / "overwrite.svg"
        _write_svg(svg_path)
        embed_metadata_svg(str(svg_path), json.dumps({"first": True}))
        embed_metadata_svg(str(svg_path), json.dumps({"second": True}))
        return svg_path.read_text(encoding="utf-8")

    @pytest.fixture
    def namespaced_content(self, tmp_path):
        svg_path = tmp_path / "ns.svg"
        svg_with_ns = """<?xml version="1.0"?>
<svg xmlns:scitex="http://scitex.io/metadata" xmlns="http://www.w3.org/2000/svg">
  <rect width="100" height="100"/>
</svg>"""
        _write_svg(svg_path, svg_with_ns)
        embed_metadata_svg(str(svg_path), json.dumps({"test": 1}))
        return svg_path.read_text(encoding="utf-8")

    def test_embed_simple_metadata_adds_scitex_namespace(self, simple_embedded_content):
        # Arrange
        # Act
        # Assert
        assert 'xmlns:scitex="http://scitex.io/metadata"' in simple_embedded_content

    def test_embed_simple_metadata_adds_metadata_element(self, simple_embedded_content):
        # Arrange
        # Act
        # Assert
        assert '<metadata id="scitex_metadata">' in simple_embedded_content

    def test_embed_simple_metadata_adds_scitex_data_tag(self, simple_embedded_content):
        # Arrange
        # Act
        # Assert
        assert "<scitex:data>" in simple_embedded_content

    def test_embed_simple_metadata_embeds_value(self, simple_embedded_content):
        # Arrange
        # Act
        # Assert
        assert '"test": "value"' in simple_embedded_content

    def test_embed_overwrites_keeps_single_metadata_element(self, overwritten_content):
        # Arrange
        # Act
        # Assert
        assert overwritten_content.count('<metadata id="scitex_metadata">') == 1

    def test_embed_overwrites_keeps_only_newest_value(self, overwritten_content):
        # Arrange
        # Act
        # Assert
        assert '"second": true' in overwritten_content

    def test_embed_overwrites_drops_old_value(self, overwritten_content):
        # Arrange
        # Act
        # Assert
        assert '"first": true' not in overwritten_content

    def test_embed_preserves_namespace_when_already_present(self, namespaced_content):
        # Arrange
        # Act
        # Assert
        # Should only have one namespace declaration
        assert namespaced_content.count("xmlns:scitex") == 1

    def test_invalid_svg_raises_value_error(self, tmp_path):
        # Arrange
        svg_path = tmp_path / "invalid.svg"
        svg_path.write_bytes(b"not an svg file")
        # Act
        ctx = pytest.raises(ValueError, match="Invalid SVG file")
        # Assert
        with ctx:
            embed_metadata_svg(str(svg_path), json.dumps({"test": 1}))


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
