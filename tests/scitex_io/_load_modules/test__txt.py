#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:30:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__txt.py

"""Tests for text file loading functionality.

This module tests the _load_txt function from scitex_io._load_modules._txt,
which handles loading text files with various encodings and formats.
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


def _write_txt(content, suffix=".txt", encoding=None):
    kwargs = {"mode": "w", "suffix": suffix, "delete": False}
    if encoding is not None:
        kwargs["encoding"] = encoding
    with tempfile.NamedTemporaryFile(**kwargs) as f:
        f.write(content)
        return f.name


def test_load_txt_basic_as_lines_default_returns_stripped_list():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Hello World\nThis is a test\nThird line"
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert loaded_lines == ["Hello World", "This is a test", "Third line"]
    finally:
        os.unlink(temp_path)


def test_load_txt_as_lines_false_returns_full_content_string():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Hello World\nThis is a test\nThird line"
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_content = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded_content == content
    finally:
        os.unlink(temp_path)


def test_load_txt_as_lines_false_with_strip_returns_stripped_string():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Hello World\nThis is a test\nThird line"
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_stripped = _load_txt(temp_path, as_lines=False, strip=True)
        # Assert
        assert loaded_stripped == content.strip()
    finally:
        os.unlink(temp_path)


def test_load_txt_empty_lines_default_filters_blank_lines():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Line 1\n\n\nLine 2\n   \nLine 3\n"
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert loaded_lines == ["Line 1", "Line 2", "Line 3"]
    finally:
        os.unlink(temp_path)


def test_load_txt_empty_lines_as_lines_false_preserves_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Line 1\n\n\nLine 2\n   \nLine 3\n"
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_content = _load_txt(temp_path, as_lines=False, strip=False)
        # Assert
        assert loaded_content == content
    finally:
        os.unlink(temp_path)


@pytest.mark.parametrize("ext", [".txt", ".log", ".event", ".py", ".sh"])
def test_load_txt_supported_extension_returns_lines(ext):
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Test content"
    temp_path = _write_txt(content, suffix=ext)
    try:
        # Act
        loaded = _load_txt(temp_path)
        # Assert
        assert loaded == [content]
    finally:
        os.unlink(temp_path)


@pytest.mark.parametrize("ext", [".txt", ".log", ".event", ".py", ".sh"])
def test_load_txt_supported_extension_returns_string_when_as_lines_false(ext):
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Test content"
    temp_path = _write_txt(content, suffix=ext)
    try:
        # Act
        loaded_str = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded_str == content
    finally:
        os.unlink(temp_path)


def test_load_txt_unexpected_extension_returns_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content = "Test content"
    temp_path = _write_txt(content, suffix=".json")
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded == content
    finally:
        os.unlink(temp_path)


def test_load_txt_unicode_as_lines_false_returns_unicode_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    unicode_content = "Hello 世界\n日本語テスト\n🎉 Emoji test"
    temp_path = _write_txt(unicode_content, encoding="utf-8")
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded == unicode_content
    finally:
        os.unlink(temp_path)


def test_load_txt_unicode_as_lines_returns_unicode_list():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    unicode_content = "Hello 世界\n日本語テスト\n🎉 Emoji test"
    temp_path = _write_txt(unicode_content, encoding="utf-8")
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert loaded_lines == ["Hello 世界", "日本語テスト", "🎉 Emoji test"]
    finally:
        os.unlink(temp_path)


def test_load_txt_latin1_encoded_file_returns_decoded_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    latin1_content = "Café résumé naïve"
    temp_path = _write_txt(latin1_content, encoding="latin1")
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded == latin1_content
    finally:
        os.unlink(temp_path)


def test_load_txt_strip_false_preserves_whitespace():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content_with_whitespace = "  \n  Hello World  \n  \n"
    temp_path = _write_txt(content_with_whitespace)
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False, strip=False)
        # Assert
        assert loaded == content_with_whitespace
    finally:
        os.unlink(temp_path)


def test_load_txt_strip_true_strips_full_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content_with_whitespace = "  \n  Hello World  \n  \n"
    temp_path = _write_txt(content_with_whitespace)
    try:
        # Act
        loaded_stripped = _load_txt(temp_path, as_lines=False, strip=True)
        # Assert
        assert loaded_stripped == "Hello World"
    finally:
        os.unlink(temp_path)


def test_load_txt_default_strips_per_line_filters_blank_lines():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    content_with_whitespace = "  \n  Hello World  \n  \n"
    temp_path = _write_txt(content_with_whitespace)
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert loaded_lines == ["Hello World"]
    finally:
        os.unlink(temp_path)


def test_load_txt_nonexistent_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_txt("/nonexistent/path/file.txt")


def test_load_txt_empty_file_default_returns_empty_list():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    temp_path = _write_txt("")
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert loaded_lines == []
    finally:
        os.unlink(temp_path)


def test_load_txt_empty_file_as_lines_false_returns_empty_string():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    temp_path = _write_txt("")
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded == ""
    finally:
        os.unlink(temp_path)


def test_load_txt_large_file_as_lines_false_returns_full_content():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    lines = [f"Line {i}: " + "x" * 100 for i in range(200)]
    content = "\n".join(lines)
    temp_path = _write_txt(content)
    try:
        # Act
        loaded = _load_txt(temp_path, as_lines=False)
        # Assert
        assert loaded == content
    finally:
        os.unlink(temp_path)


def test_load_txt_large_file_returns_expected_line_count():
    # Arrange
    from scitex_io._load_modules._txt import _load_txt

    lines = [f"Line {i}: " + "x" * 100 for i in range(200)]
    content = "\n".join(lines)
    temp_path = _write_txt(content)
    try:
        # Act
        loaded_lines = _load_txt(temp_path)
        # Assert
        assert len(loaded_lines) == 200
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
