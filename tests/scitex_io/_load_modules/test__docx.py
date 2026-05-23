#!/usr/bin/env python3
# Time-stamp: "2025-06-02 17:01:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__docx.py

"""Comprehensive tests for DOCX file loading functionality."""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
# python-docx (`from docx import Document`) is required by the DOCX loader.
pytest.importorskip("docx")
from unittest.mock import MagicMock, patch


class TestLoadDocx:
    """Test suite for _load_docx function"""

    def test_valid_extension_check(self):
        """Test that function validates .docx extension"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._docx import _load_docx

        # Test invalid extensions
        invalid_files = ["file.txt", "document.doc", "text.pdf", "data.xlsx"]

        for invalid_file in invalid_files:
            with pytest.raises(ValueError, match="File must have .docx extension"):
                _load_docx(invalid_file)

    @patch("docx.Document")
    def test_document_loading_and_text_extraction_result_equals_expected_text(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "This is the first paragraph."
        mock_para2 = MagicMock()
        mock_para2.text = "This is the second paragraph."
        mock_para3 = MagicMock()
        mock_para3.text = "Final paragraph here."
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc
        # Call function
        result = _load_docx("test_document.docx")
        # Verify Document was called correctly
        mock_document_class.assert_called_once_with("test_document.docx")
        # Verify text extraction
        # Act
        expected_text = "This is the first paragraph.This is the second paragraph.Final paragraph here."
        # Act
        # Assert
        # Assert
        assert result == expected_text

    @patch("docx.Document")
    def test_document_loading_and_text_extraction_result_is_str(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "This is the first paragraph."
        mock_para2 = MagicMock()
        mock_para2.text = "This is the second paragraph."
        mock_para3 = MagicMock()
        mock_para3.text = "Final paragraph here."
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc
        # Call function
        result = _load_docx("test_document.docx")
        # Verify Document was called correctly
        mock_document_class.assert_called_once_with("test_document.docx")
        # Verify text extraction
        # Act
        expected_text = "This is the first paragraph.This is the second paragraph.Final paragraph here."
        # Act
        # Assert
        # Assert
        assert isinstance(result, str)


    @patch("docx.Document")
    def test_empty_document_handling_result_equals_case(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock document with no paragraphs
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("empty_document.docx")
        # Act
        # Assert
        # Assert
        assert result == ""

    @patch("docx.Document")
    def test_empty_document_handling_result_is_str(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock document with no paragraphs
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("empty_document.docx")
        # Act
        # Assert
        # Assert
        assert isinstance(result, str)


    @patch("docx.Document")
    def test_document_with_empty_paragraphs(self, mock_document_class):
        """Test handling of documents with empty paragraphs"""
        # Arrange
        from scitex_io._load_modules._docx import _load_docx

        # Create mock paragraphs with some empty ones
        mock_para1 = MagicMock()
        mock_para1.text = "First paragraph."
        mock_para2 = MagicMock()
        mock_para2.text = ""  # Empty paragraph
        mock_para3 = MagicMock()
        mock_para3.text = "Third paragraph."
        mock_para4 = MagicMock()
        mock_para4.text = ""  # Another empty paragraph

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3, mock_para4]
        mock_document_class.return_value = mock_doc

        result = _load_docx("mixed_document.docx")

        # Act
        expected_text = "First paragraph.Third paragraph."
        # Assert
        assert result == expected_text

    @patch("docx.Document")
    def test_unicode_text_handling_result_equals_expected_text(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock paragraphs with Unicode characters
        mock_para1 = MagicMock()
        mock_para1.text = "Héllo Wörld! 你好世界"
        mock_para2 = MagicMock()
        mock_para2.text = "Математика 🔬📊"
        mock_para3 = MagicMock()
        mock_para3.text = "العربية language test"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc
        result = _load_docx("unicode_document.docx")
        # Act
        expected_text = "Héllo Wörld! 你好世界Математика 🔬📊العربية language test"
        # Act
        # Assert
        # Assert
        assert result == expected_text

    @patch("docx.Document")
    def test_unicode_text_handling_result_is_str(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create mock paragraphs with Unicode characters
        mock_para1 = MagicMock()
        mock_para1.text = "Héllo Wörld! 你好世界"
        mock_para2 = MagicMock()
        mock_para2.text = "Математика 🔬📊"
        mock_para3 = MagicMock()
        mock_para3.text = "العربية language test"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc
        result = _load_docx("unicode_document.docx")
        # Act
        expected_text = "Héllo Wörld! 你好世界Математика 🔬📊العربية language test"
        # Act
        # Assert
        # Assert
        assert isinstance(result, str)


    @patch("docx.Document")
    def test_whitespace_and_special_characters(self, mock_document_class):
        """Test handling of whitespace and special characters"""
        # Arrange
        from scitex_io._load_modules._docx import _load_docx

        # Create mock paragraphs with various whitespace scenarios
        mock_para1 = MagicMock()
        mock_para1.text = "  Leading and trailing spaces  "
        mock_para2 = MagicMock()
        mock_para2.text = "Tab\there\tand\tthere"
        mock_para3 = MagicMock()
        mock_para3.text = "Line\nbreaks\ninside"
        mock_para4 = MagicMock()
        mock_para4.text = "Special chars: !@#$%^&*()"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3, mock_para4]
        mock_document_class.return_value = mock_doc

        result = _load_docx("whitespace_document.docx")

        # Act
        expected_text = "  Leading and trailing spaces  Tab\there\tand\tthereLine\nbreaks\ninsideSpecial chars: !@#$%^&*()"
        # Assert
        assert result == expected_text

    @patch("docx.Document")
    def test_docx_exception_propagation_raises_filenotfounderror(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Test FileNotFoundError
        # Act
        mock_document_class.side_effect = FileNotFoundError("File not found")
        # Act
        # Assert
        # Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            _load_docx("nonexistent.docx")

    @patch("docx.Document")
    def test_docx_exception_propagation_raises_packagenotfounderror(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Test FileNotFoundError
        # Act
        mock_document_class.side_effect = FileNotFoundError("File not found")
        # Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            _load_docx("nonexistent.docx")
        # Test PackageNotFoundError (invalid DOCX file)
        from docx.opc.exceptions import PackageNotFoundError
        mock_document_class.side_effect = PackageNotFoundError("Invalid DOCX file")
        # Act
        # Assert
        with pytest.raises(PackageNotFoundError, match="Invalid DOCX file"):
            _load_docx("invalid.docx")


    @patch("docx.Document")
    def test_large_document_handling_result_is_str(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create a large number of mock paragraphs
        mock_paragraphs = []
        for i in range(1000):
            mock_para = MagicMock()
            mock_para.text = f"This is paragraph number {i}. "
            mock_paragraphs.append(mock_para)
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("large_document.docx")
        # Act
        # Assert
        # Assert
        assert isinstance(result, str)

    @patch("docx.Document")
    def test_large_document_handling_len_result_20000(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create a large number of mock paragraphs
        mock_paragraphs = []
        for i in range(1000):
            mock_para = MagicMock()
            mock_para.text = f"This is paragraph number {i}. "
            mock_paragraphs.append(mock_para)
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("large_document.docx")
        # Act
        # Assert
        # Assert
        assert len(result) > 20000  # Should be quite long

    @patch("docx.Document")
    def test_large_document_handling_this_is_paragraph_number_0_in_result(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create a large number of mock paragraphs
        mock_paragraphs = []
        for i in range(1000):
            mock_para = MagicMock()
            mock_para.text = f"This is paragraph number {i}. "
            mock_paragraphs.append(mock_para)
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("large_document.docx")
        # Act
        # Assert
        # Assert
        assert "This is paragraph number 0. " in result

    @patch("docx.Document")
    def test_large_document_handling_this_is_paragraph_number_999_in_result(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        # Create a large number of mock paragraphs
        mock_paragraphs = []
        for i in range(1000):
            mock_para = MagicMock()
            mock_para.text = f"This is paragraph number {i}. "
            mock_paragraphs.append(mock_para)
        mock_doc = MagicMock()
        mock_doc.paragraphs = mock_paragraphs
        mock_document_class.return_value = mock_doc
        # Act
        result = _load_docx("large_document.docx")
        # Act
        # Assert
        # Assert
        assert "This is paragraph number 999. " in result


    def test_function_signature_lpath_in_sig_parameters(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._docx import _load_docx
        # Act
        sig = inspect.signature(_load_docx)
        # Act
        # Assert
        # Assert
        assert "lpath" in sig.parameters

    def test_function_signature_kwargs_in_sig_parameters_or_len_sig_parameters_1(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._docx import _load_docx
        # Act
        sig = inspect.signature(_load_docx)
        # Act
        # Assert
        # Assert
        assert "kwargs" in sig.parameters or len(sig.parameters) >= 1

    def test_function_signature_sig_return_annotation_inspect_signature_empty(self):
        # Arrange
        # Arrange
        import inspect
        from scitex_io._load_modules._docx import _load_docx
        # Act
        sig = inspect.signature(_load_docx)
        # Act
        # Assert
        # Assert
        assert sig.return_annotation != inspect.Signature.empty


    def test_function_docstring_hasattr_load_docx_doc(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Act
        # Assert
        # Assert
        assert hasattr(_load_docx, "__doc__")

    def test_function_docstring_load_docx_doc_is_not_none(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Act
        # Assert
        # Assert
        assert _load_docx.__doc__ is not None

    def test_function_docstring_load_and_extract_text_content_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Assert
        assert hasattr(_load_docx, "__doc__")
        assert _load_docx.__doc__ is not None
        docstring = _load_docx.__doc__
        # Act
        # Assert
        assert "Load and extract text content" in docstring

    def test_function_docstring_parameters_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Assert
        assert hasattr(_load_docx, "__doc__")
        assert _load_docx.__doc__ is not None
        docstring = _load_docx.__doc__
        # Act
        # Assert
        assert "Parameters" in docstring

    def test_function_docstring_returns_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Assert
        assert hasattr(_load_docx, "__doc__")
        assert _load_docx.__doc__ is not None
        docstring = _load_docx.__doc__
        # Act
        # Assert
        assert "Returns" in docstring

    def test_function_docstring_raises_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Assert
        assert hasattr(_load_docx, "__doc__")
        assert _load_docx.__doc__ is not None
        docstring = _load_docx.__doc__
        # Act
        # Assert
        assert "Raises" in docstring

    def test_function_docstring_docx_in_docstring(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx
        # Assert
        assert hasattr(_load_docx, "__doc__")
        assert _load_docx.__doc__ is not None
        docstring = _load_docx.__doc__
        # Act
        # Assert
        assert ".docx" in docstring


    @patch("docx.Document")
    def test_kwargs_ignored_result_equals_test_text(self, mock_document_class):
        """Test that kwargs are ignored (not passed to Document)"""
        # Arrange
        from scitex_io._load_modules._docx import _load_docx

        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Test text"
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc

        # Call with various kwargs
        result = _load_docx(
            "test.docx", verbose=True, encoding="utf-8", custom_param="value"
        )

        # Verify Document was called only with the path
        # Act
        mock_document_class.assert_called_once_with("test.docx")
        # Assert
        assert result == "Test text"

    def test_case_sensitive_extension_check(self):
        """Test case sensitivity of .docx extension"""
        # Arrange
        # Act
        # Assert
        from scitex_io._load_modules._docx import _load_docx

        # Test case variations that should fail
        case_variations = ["file.DOCX", "file.Docx", "file.dOcX"]

        for variant in case_variations:
            with pytest.raises(ValueError, match="File must have .docx extension"):
                _load_docx(variant)

    @patch("docx.Document")
    def test_document_with_only_whitespace(self, mock_document_class):
        """Test handling of document with only whitespace paragraphs"""
        # Arrange
        from scitex_io._load_modules._docx import _load_docx

        # Create mock paragraphs with only whitespace
        mock_para1 = MagicMock()
        mock_para1.text = "   "
        mock_para2 = MagicMock()
        mock_para2.text = "\t\t"
        mock_para3 = MagicMock()
        mock_para3.text = "\n\n"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc

        result = _load_docx("whitespace_only.docx")

        # Act
        expected_text = "   \t\t\n\n"
        # Assert
        assert result == expected_text

    @patch("docx.Document")
    def test_absolute_and_relative_paths_result_equals_test_content(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Test content"
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc
        # Test absolute path
        abs_path = "/home/user/documents/report.docx"
        result = _load_docx(abs_path)
        # Act
        mock_document_class.assert_called_with(abs_path)
        # Act
        # Assert
        # Assert
        assert result == "Test content"

    @patch("docx.Document")
    def test_absolute_and_relative_paths_result_equals_test_content(self, mock_document_class):
        # Arrange
        # Arrange
        from scitex_io._load_modules._docx import _load_docx
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "Test content"
        mock_doc.paragraphs = [mock_para]
        mock_document_class.return_value = mock_doc
        # Test absolute path
        abs_path = "/home/user/documents/report.docx"
        result = _load_docx(abs_path)
        # Act
        mock_document_class.assert_called_with(abs_path)
        # Assert
        assert result == "Test content"
        # Reset mock and test relative path
        mock_document_class.reset_mock()
        rel_path = "./data/document.docx"
        result = _load_docx(rel_path)
        mock_document_class.assert_called_with(rel_path)
        # Act
        # Assert
        assert result == "Test content"


    @patch("docx.Document")
    def test_complex_paragraph_text_scenarios(self, mock_document_class):
        """Test complex scenarios with paragraph text extraction"""
        # Arrange
        from scitex_io._load_modules._docx import _load_docx

        # Test paragraphs with complex formatting (text should still be extracted)
        mock_para1 = MagicMock()
        mock_para1.text = "Bold and italic text mixed together"
        mock_para2 = MagicMock()
        mock_para2.text = "Text with hyperlinks and footnotes"
        mock_para3 = MagicMock()
        mock_para3.text = "Tables and lists converted to text"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_document_class.return_value = mock_doc

        result = _load_docx("complex_formatting.docx")

        # Act
        expected_text = "Bold and italic text mixed togetherText with hyperlinks and footnotesTables and lists converted to text"
        # Assert
        assert result == expected_text

    def test_module_dependencies_callable_load_docx(self):
        """Test that the function depends on python-docx module"""
        # Arrange
        # Act
        from scitex_io._load_modules._docx import _load_docx

        # Verify that the function exists and is callable
        # Assert
        assert callable(_load_docx)

        # The function should import docx inside, so check it works with mocked Document
        with patch("docx.Document") as mock_doc:
            mock_doc.return_value.paragraphs = []
            result = _load_docx("test.docx")
            assert result == ""

    @pytest.mark.skipif(
        True, reason="Real file test - requires actual docx file creation"
    )
    def test_real_docx_file_integration(self):
        """Integration test with real DOCX file (skipped by default)"""
        # Arrange
        # Act
        # Assert
        try:
            from docx import Document
        except ImportError:
            pytest.skip("python-docx not available")

            from scitex_io._load_modules._docx import _load_docx

        # Create a real DOCX file
        doc = Document()
        doc.add_heading("Integration Test Document", 0)
        doc.add_paragraph("This is a real test paragraph.")
        doc.add_paragraph("Testing actual DOCX file loading.")

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            doc.save(f.name)
            temp_path = f.name

        try:
            content = _load_docx(temp_path)

            assert isinstance(content, str)
            assert "Integration Test Document" in content
            assert "real test paragraph" in content
            assert "actual DOCX file loading" in content

        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_docx.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Time-stamp: "2024-11-14 07:55:35 (ywatanabe)"
# # File: ./scitex_repo/src/scitex/io/_load_modules/_docx.py
#
# from typing import Any
#
#
# def _load_docx(lpath: str, **kwargs) -> Any:
#     """
#     Load and extract text content from a .docx file.
#
#     Parameters:
#     -----------
#     lpath : str
#         The path to the .docx file.
#
#     Returns:
#     --------
#     str
#         The extracted text content from the .docx file.
#
#     Raises:
#     -------
#     FileNotFoundError
#         If the specified file does not exist.
#     docx.opc.exceptions.PackageNotFoundError
#         If the file is not a valid .docx file.
#     """
#     if not lpath.endswith(".docx"):
#         raise ValueError("File must have .docx extension")
#
#     from docx import Document
#
#     doc = Document(lpath)
#     full_text = []
#     for para in doc.paragraphs:
#         full_text.append(para.text)
#     return "".join(full_text)
#
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_load_modules/_docx.py
# --------------------------------------------------------------------------------
