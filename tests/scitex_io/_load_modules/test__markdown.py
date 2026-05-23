#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2025-06-03 08:27:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__markdown.py

"""Tests for Markdown file loading functionality.

This module tests the Markdown loading functionality including the _load_markdown
and load_markdown functions with support for HTML and plain text conversion.
"""

import os
import tempfile

import pytest

# Optional deps for the markdown loader (`scitex_io._load_modules._markdown`
# imports both at runtime). Skip cleanly when either is missing so the
# suite stays green on fresh installs.
pytest.importorskip("markdown")
pytest.importorskip("html2text")

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


class TestLoadMarkdown:
    """Test the _load_markdown function."""

    @pytest.fixture
    def basic_md_plain(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        md = (
            "# Test Header\n\nThis is a paragraph.\n\n"
            "- Item 1\n- Item 2\n\n## Subheader\n\nMore content here."
        )
        p = tmp_path / "basic.md"
        p.write_text(md)
        return _load_markdown(str(p))

    def test_load_markdown_basic_returns_string(self, basic_md_plain):
        # Arrange
        loaded = basic_md_plain
        # Act
        result_type = type(loaded)
        # Assert
        assert result_type is str

    def test_load_markdown_basic_includes_header_text(self, basic_md_plain):
        # Arrange
        loaded = basic_md_plain
        # Act
        has_header = "Test Header" in loaded
        # Assert
        assert has_header

    def test_load_markdown_basic_includes_list_item(self, basic_md_plain):
        # Arrange
        loaded = basic_md_plain
        # Act
        has_item = "Item 1" in loaded
        # Assert
        assert has_item

    def test_load_markdown_basic_includes_subheader_content(self, basic_md_plain):
        # Arrange
        loaded = basic_md_plain
        # Act
        has_more = "More content" in loaded
        # Assert
        assert has_more

    @pytest.fixture
    def basic_md_html(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        md = (
            "# Test Header\n\nThis is a **bold** paragraph with *italic* text.\n\n"
            "- Item 1\n- Item 2"
        )
        p = tmp_path / "html.md"
        p.write_text(md)
        return _load_markdown(str(p), style="html")

    def test_load_markdown_html_returns_string(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        result_type = type(loaded)
        # Assert
        assert result_type is str

    def test_load_markdown_html_emits_h1_tag(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        has_h1 = "<h1>" in loaded
        # Assert
        assert has_h1

    def test_load_markdown_html_emits_strong_tag(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        has_strong = "<strong>" in loaded
        # Assert
        assert has_strong

    def test_load_markdown_html_emits_em_tag(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        has_em = "<em>" in loaded
        # Assert
        assert has_em

    def test_load_markdown_html_emits_ul_tag(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        has_ul = "<ul>" in loaded
        # Assert
        assert has_ul

    def test_load_markdown_html_emits_li_tag(self, basic_md_html):
        # Arrange
        loaded = basic_md_html
        # Act
        has_li = "<li>" in loaded
        # Assert
        assert has_li

    def test_load_markdown_empty_file(self):
        """Test loading empty Markdown file."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._markdown import _load_markdown

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            temp_path = f.name

        try:
            loaded_content = _load_markdown(temp_path)
            # html2text adds newlines even for empty content
            assert loaded_content == "\n\n"
        finally:
            os.unlink(temp_path)

    def test_load_markdown_invalid_style(self):
        """Test loading Markdown with invalid style option."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._markdown import _load_markdown

        md_content = "# Test"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(md_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid style option"):
                _load_markdown(temp_path, style="invalid")
        finally:
            os.unlink(temp_path)

    def test_load_markdown_nonexistent_file(self):
        """Test loading non-existent Markdown file."""
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown

        # Assert
        with pytest.raises(FileNotFoundError):
            _load_markdown("nonexistent_file.md")

    _COMPLEX_MD = """# Main Title

## Section 1

This is a paragraph with **bold** and *italic* text.

### Subsection

Here's a [link](https://example.com) and some `inline code`.

```python
def hello():
    print("Hello, World!")
```

#### Lists

1. Ordered item 1
2. Ordered item 2
   - Nested unordered item
   - Another nested item

> This is a blockquote
> spanning multiple lines

| Column 1 | Column 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

---

Final paragraph."""

    @pytest.fixture
    def complex_md_html(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "complex.md"
        p.write_text(self._COMPLEX_MD)
        return _load_markdown(str(p), style="html")

    @pytest.fixture
    def complex_md_text(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "complex.md"
        p.write_text(self._COMPLEX_MD)
        return _load_markdown(str(p), style="plain_text")

    def test_load_markdown_complex_html_includes_h1(self, complex_md_html):
        # Arrange
        loaded = complex_md_html
        # Act
        result = "<h1>" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_html_includes_h2(self, complex_md_html):
        # Arrange
        loaded = complex_md_html
        # Act
        result = "<h2>" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_html_includes_code_tag(self, complex_md_html):
        # Arrange
        loaded = complex_md_html
        # Act
        result = "<code>" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_html_includes_blockquote(self, complex_md_html):
        # Arrange
        loaded = complex_md_html
        # Act
        result = "<blockquote>" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_html_preserves_table_content(self, complex_md_html):
        # Arrange
        loaded = complex_md_html
        # Act
        result = "Column 1" in loaded and "Cell 1" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_text_includes_main_title(self, complex_md_text):
        # Arrange
        loaded = complex_md_text
        # Act
        result = "Main Title" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_text_includes_section_1(self, complex_md_text):
        # Arrange
        loaded = complex_md_text
        # Act
        result = "Section 1" in loaded
        # Assert
        assert result

    def test_load_markdown_complex_text_includes_code_identifier(self, complex_md_text):
        # Arrange
        loaded = complex_md_text
        # Act
        result = "hello" in loaded
        # Assert
        assert result

    def test_load_markdown_with_kwargs(self):
        """Test that _load_markdown accepts kwargs parameter."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._markdown import _load_markdown

        md_content = "# Test"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(md_content)
            temp_path = f.name

        try:
            # Should not raise error with additional kwargs
            result = _load_markdown(temp_path, custom_arg=True, another_arg="test")
            assert isinstance(result, str)
        finally:
            os.unlink(temp_path)

    @pytest.fixture
    def special_chars_md_loaded(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        md_content = (
            "# Título con acentos\n\nContenido con caracteres especiales: ñáéíóú\n\n"
            "- Elementos con símbolos: €, ©, ®\n- Emojis: 🚀 🎉 ⭐\n\n"
            "`código con tildes: función()`"
        )
        p = tmp_path / "special.md"
        p.write_text(md_content, encoding="utf-8")
        return _load_markdown(str(p))

    def test_load_markdown_preserves_titulo(self, special_chars_md_loaded):
        # Arrange
        loaded = special_chars_md_loaded
        # Act
        result = "Título" in loaded
        # Assert
        assert result

    def test_load_markdown_preserves_accent_letters(self, special_chars_md_loaded):
        # Arrange
        loaded = special_chars_md_loaded
        # Act
        result = "ñáéíóú" in loaded
        # Assert
        assert result

    def test_load_markdown_preserves_funcion_token(self, special_chars_md_loaded):
        # Arrange
        loaded = special_chars_md_loaded
        # Act
        result = "función" in loaded
        # Assert
        assert result

    def test_load_markdown_function_signature_lpath_md_in_params(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._markdown import _load_markdown
        sig = inspect.signature(_load_markdown)
        # Act
        params = list(sig.parameters.keys())
        # Act
        # Assert
        # Assert
        assert "lpath_md" in params

    def test_load_markdown_function_signature_style_in_params(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._markdown import _load_markdown
        sig = inspect.signature(_load_markdown)
        # Act
        params = list(sig.parameters.keys())
        # Act
        # Assert
        # Assert
        assert "style" in params

    def test_load_markdown_function_signature_kwargs_in_params_or_len_p_for_p_in_sig_parameters_values_if_(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._markdown import _load_markdown
        sig = inspect.signature(_load_markdown)
        # Act
        params = list(sig.parameters.keys())
        # Act
        # Assert
        # Assert
        assert (
            "kwargs" in params
            or len([p for p in sig.parameters.values() if p.kind == p.VAR_KEYWORD]) > 0
        )


    def test_load_markdown_docstring_load_markdown_doc_is_not_none(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown
        # Act
        # Assert
        # Assert
        assert _load_markdown.__doc__ is not None

    def test_load_markdown_docstring_len_load_markdown_doc_strip_100(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown
        # Act
        # Assert
        # Assert
        assert len(_load_markdown.__doc__.strip()) > 100

    def test_load_markdown_docstring_markdown_in_load_markdown_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown
        # Act
        # Assert
        # Assert
        assert "Markdown" in _load_markdown.__doc__

    def test_load_markdown_docstring_parameters_in_load_markdown_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown
        # Act
        # Assert
        # Assert
        assert "Parameters" in _load_markdown.__doc__

    def test_load_markdown_docstring_returns_in_load_markdown_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._markdown import _load_markdown
        # Act
        # Assert
        # Assert
        assert "Returns" in _load_markdown.__doc__


    def test_load_markdown_default_style_matches_explicit_plain_text(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "x.md"
        p.write_text("# Test **bold**")
        # Act
        result_default = _load_markdown(str(p))
        result_explicit = _load_markdown(str(p), style="plain_text")
        # Assert
        assert result_default == result_explicit

    def test_load_markdown_default_style_strips_html_tags(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "x.md"
        p.write_text("# Test **bold**")
        # Act
        result_default = _load_markdown(str(p))
        # Assert
        assert "<" not in result_default


class TestLoadMarkdownAlternative:
    """Test the load_markdown function (alternative implementation)."""

    def test_load_markdown_alt_basic_returns_string(self, tmp_path):
        # Arrange
        from scitex_io._load_modules import load_markdown

        p = tmp_path / "alt.md"
        p.write_text("# Test Header\n\nParagraph content.")
        # Act
        loaded = load_markdown(str(p))
        # Assert
        assert isinstance(loaded, str)

    def test_load_markdown_alt_basic_includes_header_text(self, tmp_path):
        # Arrange
        from scitex_io._load_modules import load_markdown

        p = tmp_path / "alt.md"
        p.write_text("# Test Header\n\nParagraph content.")
        # Act
        loaded = load_markdown(str(p))
        # Assert
        assert "Test Header" in loaded

    def test_load_markdown_alt_html_emits_h1_tag(self, tmp_path):
        # Arrange
        from scitex_io._load_modules import load_markdown

        p = tmp_path / "alt.md"
        p.write_text("# Test **bold**")
        # Act
        loaded = load_markdown(str(p), style="html")
        # Assert
        assert "<h1>" in loaded

    def test_load_markdown_alt_html_emits_strong_tag(self, tmp_path):
        # Arrange
        from scitex_io._load_modules import load_markdown

        p = tmp_path / "alt.md"
        p.write_text("# Test **bold**")
        # Act
        loaded = load_markdown(str(p), style="html")
        # Assert
        assert "<strong>" in loaded

    def test_load_markdown_alt_signature_lpath_md_in_params(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules import load_markdown
        sig = inspect.signature(load_markdown)
        # Act
        params = list(sig.parameters.keys())
        # Act
        # Assert
        # Assert
        assert "lpath_md" in params

    def test_load_markdown_alt_signature_style_in_params(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules import load_markdown
        sig = inspect.signature(load_markdown)
        # Act
        params = list(sig.parameters.keys())
        # Act
        # Assert
        # Assert
        assert "style" in params


    def test_load_markdown_alt_docstring_load_markdown_doc_is_not_none(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules import load_markdown
        # Act
        # Assert
        # Assert
        assert load_markdown.__doc__ is not None

    def test_load_markdown_alt_docstring_markdown_in_load_markdown_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules import load_markdown
        # Act
        # Assert
        # Assert
        assert "Markdown" in load_markdown.__doc__



class TestMarkdownDependencies:
    """Test Markdown processing dependencies and edge cases."""

    def test_markdown_html_style_returns_h1_tag_for_top_header(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        md_path = tmp_path / "x.md"
        md_path.write_text("# Test")
        # Act
        result = _load_markdown(str(md_path), style="html")
        # Assert
        assert "<h1>" in result and "Test" in result

    def test_markdown_plain_text_style_strips_html_tags(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        md_path = tmp_path / "x.md"
        md_path.write_text("# Test\n")
        # Act
        result = _load_markdown(str(md_path), style="plain_text")
        # Assert
        assert "<" not in result

    @pytest.fixture
    def utf8_md_loaded(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "utf8.md"
        p.write_text("# Tëst wîth spëcîal chàractërs", encoding="utf-8")
        return _load_markdown(str(p))

    def test_file_encoding_preserves_test_token(self, utf8_md_loaded):
        # Arrange
        loaded = utf8_md_loaded
        # Act
        result = "Tëst" in loaded
        # Assert
        assert result

    def test_file_encoding_preserves_special_token(self, utf8_md_loaded):
        # Arrange
        loaded = utf8_md_loaded
        # Act
        result = "spëcîal" in loaded
        # Assert
        assert result

    @pytest.fixture
    def large_md_loaded(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        sections = []
        for i in range(50):
            sections.append(f"## Section {i}")
            sections.append(
                f"This is content for section {i} with **bold** and *italic* text."
            )
            sections.append("")
        p = tmp_path / "large.md"
        p.write_text("\n".join(sections))
        return _load_markdown(str(p))

    def test_large_file_includes_first_section_label(self, large_md_loaded):
        # Arrange
        loaded = large_md_loaded
        # Act
        result = "Section 0" in loaded
        # Assert
        assert result

    def test_large_file_includes_last_section_label(self, large_md_loaded):
        # Arrange
        loaded = large_md_loaded
        # Act
        result = "Section 49" in loaded
        # Assert
        assert result

    def test_large_file_produces_long_output(self, large_md_loaded):
        # Arrange
        loaded = large_md_loaded
        # Act
        result_len = len(loaded)
        # Assert
        assert result_len > 1000


class TestMarkdownErrorHandling:
    """Test error handling and edge cases."""

    def test_file_permission_error(self):
        """Test handling of file permission errors."""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._markdown import _load_markdown

        # Create a file and remove read permissions (on Unix systems)
        md_content = "# Test"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(md_content)
            temp_path = f.name

        try:
            # Try to remove read permissions (may not work on all systems)
            try:
                os.chmod(temp_path, 0o000)
                with pytest.raises(PermissionError):
                    _load_markdown(temp_path)
            except (OSError, PermissionError):
                # Permission change failed, skip this test
                pass
        finally:
            # Restore permissions and clean up
            try:
                os.chmod(temp_path, 0o644)
                os.unlink(temp_path)
            except (OSError, FileNotFoundError):
                pass

    def test_io_error_for_nonexistent_path_raises_filenotfounderror(self, tmp_path):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        missing = tmp_path / "does_not_exist.md"
        # Act
        ctx = pytest.raises(FileNotFoundError)
        # Assert
        with ctx:
            _load_markdown(str(missing))

    @pytest.mark.parametrize(
        "md_content",
        [
            "",  # Empty content
            "\n\n\n",  # Only whitespace
            "Plain text without markdown",  # No markdown syntax
            "# \n",  # Empty header
            "[broken link]()",  # Malformed link
            "```\ncode block without language\n```",  # Code block without language
        ],
    )
    def test_markdown_conversion_html_edge_case_returns_string(self, tmp_path, md_content):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "edge.md"
        p.write_text(md_content)
        # Act
        result_html = _load_markdown(str(p), style="html")
        # Assert
        assert isinstance(result_html, str)

    @pytest.mark.parametrize(
        "md_content",
        [
            "",
            "\n\n\n",
            "Plain text without markdown",
            "# \n",
            "[broken link]()",
            "```\ncode block without language\n```",
        ],
    )
    def test_markdown_conversion_text_edge_case_returns_string(self, tmp_path, md_content):
        # Arrange
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "edge.md"
        p.write_text(md_content)
        # Act
        result_text = _load_markdown(str(p), style="plain_text")
        # Assert
        assert isinstance(result_text, str)


class TestMarkdownIntegration:
    """Integration tests for complete Markdown processing workflows."""

    _WORKFLOW_MD = (
        "# Main Title\n\n"
        "This is a paragraph with **bold** and *italic* text.\n\n"
        "## Section\n\n- List item 1\n- List item 2\n\n"
        "[Link](https://example.com)"
    )

    @pytest.fixture
    def workflow_html(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "wf.md"
        p.write_text(self._WORKFLOW_MD)
        return _load_markdown(str(p), style="html")

    @pytest.fixture
    def workflow_text(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown

        p = tmp_path / "wf.md"
        p.write_text(self._WORKFLOW_MD)
        return _load_markdown(str(p), style="plain_text")

    def test_workflow_html_emits_h1_tag(self, workflow_html):
        # Arrange
        loaded = workflow_html
        # Act
        result = "<h1>" in loaded
        # Assert
        assert result

    def test_workflow_html_emits_strong_tag(self, workflow_html):
        # Arrange
        loaded = workflow_html
        # Act
        result = "<strong>" in loaded
        # Assert
        assert result

    def test_workflow_html_emits_em_tag(self, workflow_html):
        # Arrange
        loaded = workflow_html
        # Act
        result = "<em>" in loaded
        # Assert
        assert result

    def test_workflow_html_emits_ul_tag(self, workflow_html):
        # Arrange
        loaded = workflow_html
        # Act
        result = "<ul>" in loaded
        # Assert
        assert result

    def test_workflow_html_emits_anchor_href(self, workflow_html):
        # Arrange
        loaded = workflow_html
        # Act
        result = "<a href=" in loaded
        # Assert
        assert result

    def test_workflow_text_includes_main_title(self, workflow_text):
        # Arrange
        loaded = workflow_text
        # Act
        result = "Main Title" in loaded
        # Assert
        assert result

    def test_workflow_text_includes_bold_token(self, workflow_text):
        # Arrange
        loaded = workflow_text
        # Act
        result = "bold" in loaded
        # Assert
        assert result

    def test_workflow_text_includes_italic_token(self, workflow_text):
        # Arrange
        loaded = workflow_text
        # Act
        result = "italic" in loaded
        # Assert
        assert result

    def test_workflow_text_strips_html_tags(self, workflow_text):
        # Arrange
        loaded = workflow_text
        # Act
        result = "<" not in loaded
        # Assert
        assert result

    @pytest.fixture
    def consistency_results(self, tmp_path):
        from scitex_io._load_modules._markdown import _load_markdown, load_markdown

        p = tmp_path / "cons.md"
        p.write_text("# Test\n\nContent **bold**")
        r1 = _load_markdown(str(p), style="plain_text")
        r2 = load_markdown(str(p), style="plain_text")
        return r1, r2

    def test_both_functions_include_test_token_in_primary(self, consistency_results):
        # Arrange
        r1, _r2 = consistency_results
        # Act
        result = "Test" in r1
        # Assert
        assert result

    def test_both_functions_include_test_token_in_alternative(self, consistency_results):
        # Arrange
        _r1, r2 = consistency_results
        # Act
        result = "Test" in r2
        # Assert
        assert result

    def test_both_functions_include_bold_token_in_primary(self, consistency_results):
        # Arrange
        r1, _r2 = consistency_results
        # Act
        result = "bold" in r1
        # Assert
        assert result

    def test_both_functions_include_bold_token_in_alternative(self, consistency_results):
        # Arrange
        _r1, r2 = consistency_results
        # Act
        result = "bold" in r2
        # Assert
        assert result


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_markdown.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-14 07:55:42 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_markdown.py
#
#
# def _load_markdown(lpath_md, style="plain_text", **kwargs):
#     """
#     Load and convert Markdown content from a file.
#
#     This function reads a Markdown file and converts it to either HTML or plain text format.
#
#     Parameters:
#     -----------
#     lpath_md : str
#         The path to the Markdown file to be loaded.
#     style : str, optional
#         The output style of the converted content.
#         Options are "html" or "plain_text" (default).
#
#     Returns:
#     --------
#     str
#         The converted content of the Markdown file, either as HTML or plain text.
#
#     Raises:
#     -------
#     FileNotFoundError
#         If the specified file does not exist.
#     IOError
#         If there's an error reading the file.
#     ValueError
#         If an invalid style option is provided.
#
#     Notes:
#     ------
#     This function uses the 'markdown' library to convert Markdown to HTML,
#     and 'html2text' to convert HTML to plain text when necessary.
#     """
#     import html2text
#     import markdown
#
#     # Load Markdown content from a file
#     with open(lpath_md, "r") as file:
#         markdown_content = file.read()
#
#     # Convert Markdown to HTML
#     html_content = markdown.markdown(markdown_content)
#     if style == "html":
#         return html_content
#     elif style == "plain_text":
#         text_maker = html2text.HTML2Text()
#         text_maker.ignore_links = True
#         text_maker.bypass_tables = False
#         plain_text = text_maker.handle(html_content)
#         return plain_text
#     else:
#         raise ValueError("Invalid style option. Choose 'html' or 'plain_text'.")
#
#
# def load_markdown(lpath_md, style="plain_text"):
#     """
#     Load and convert a Markdown file to either HTML or plain text.
#
#     Parameters:
#     -----------
#     lpath_md : str
#         The path to the Markdown file.
#     style : str, optional
#         The output style, either "html" or "plain_text" (default).
#
#     Returns:
#     --------
#     str
#         The converted content of the Markdown file.
#     """
#     import html2text
#     import markdown
#
#     # Load Markdown content from a file
#     with open(lpath_md, "r") as file:
#         markdown_content = file.read()
#
#     # Convert Markdown to HTML
#     html_content = markdown.markdown(markdown_content)
#     if style == "html":
#         return html_content
#
#     elif style == "plain_text":
#         text_maker = html2text.HTML2Text()
#         text_maker.ignore_links = True
#         text_maker.bypass_tables = False
#         plain_text = text_maker.handle(html_content)
#
#         return plain_text
#
#
# # def _load_markdown(lpath):
# #     md_text = StringIO(lpath.read().decode("utf-8"))
# #     html = markdown.markdown(md_text.read())
# #     return html
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_markdown.py
# --------------------------------------------------------------------------------
