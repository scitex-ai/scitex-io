#!/usr/bin/env python3
# Timestamp: "2025-05-31"
# File: test__json2md.py

"""Tests for scitex.io._json2md module."""

import json
import os
import tempfile
from pathlib import Path

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


class TestJson2MdBasic:
    """Test basic JSON to Markdown conversion functionality."""

    def test_simple_dict_conversion(self):
        """Test converting simple dictionary to markdown."""
        # Arrange
        from scitex_io import json2md

        data = {"title": "Test Document", "author": "John Doe"}
        result = json2md(data)

        # Act
        expected = "# title\nTest Document\n\n# author\nJohn Doe\n"
        # Assert
        assert result == expected

    def test_nested_dict_conversion_chapter_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "chapter": "Introduction",
            "sections": {
                "overview": "This is an overview",
                "details": "These are the details",
            },
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# chapter" in result

    def test_nested_dict_conversion_overview_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "chapter": "Introduction",
            "sections": {
                "overview": "This is an overview",
                "details": "These are the details",
            },
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## overview" in result

    def test_nested_dict_conversion_details_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "chapter": "Introduction",
            "sections": {
                "overview": "This is an overview",
                "details": "These are the details",
            },
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## details" in result

    def test_nested_dict_conversion_introduction_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "chapter": "Introduction",
            "sections": {
                "overview": "This is an overview",
                "details": "These are the details",
            },
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "Introduction" in result

    def test_nested_dict_conversion_this_is_an_overview_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "chapter": "Introduction",
            "sections": {
                "overview": "This is an overview",
                "details": "These are the details",
            },
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "This is an overview" in result


    def test_simple_list_conversion(self):
        """Test converting simple list to markdown."""
        # Arrange
        from scitex_io import json2md

        data = ["item1", "item2", "item3"]
        result = json2md(data)

        # Act
        expected = "* item1\n* item2\n* item3"
        # Assert
        assert result == expected

    def test_mixed_types_conversion_text_value_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "string": "text value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "text value" in result

    def test_mixed_types_conversion_n_42_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "string": "text value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "42" in result

    def test_mixed_types_conversion_n_3_14_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "string": "text value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "3.14" in result

    def test_mixed_types_conversion_true_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "string": "text value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "True" in result

    def test_mixed_types_conversion_none_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "string": "text value",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "None" in result



class TestJson2MdNested:
    """Test nested structure conversions."""

    def test_dict_with_list_title_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"title": "Shopping List", "items": ["apples", "bananas", "oranges"]}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# title" in result

    def test_dict_with_list_items_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"title": "Shopping List", "items": ["apples", "bananas", "oranges"]}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# items" in result

    def test_dict_with_list_apples_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"title": "Shopping List", "items": ["apples", "bananas", "oranges"]}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* apples" in result

    def test_dict_with_list_bananas_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"title": "Shopping List", "items": ["apples", "bananas", "oranges"]}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* bananas" in result

    def test_dict_with_list_oranges_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"title": "Shopping List", "items": ["apples", "bananas", "oranges"]}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* oranges" in result


    def test_list_of_dicts_name_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# name" in result

    def test_list_of_dicts_alice_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "Alice" in result

    def test_list_of_dicts_bob_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "Bob" in result

    def test_list_of_dicts_age_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# age" in result

    def test_list_of_dicts_n_30_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "30" in result

    def test_list_of_dicts_n_25_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "25" in result


    def test_deeply_nested_structure_level1_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"level1": {"level2": {"level3": {"value": "deeply nested"}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# level1" in result

    def test_deeply_nested_structure_level2_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"level1": {"level2": {"level3": {"value": "deeply nested"}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## level2" in result

    def test_deeply_nested_structure_level3_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"level1": {"level2": {"level3": {"value": "deeply nested"}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "### level3" in result

    def test_deeply_nested_structure_value_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"level1": {"level2": {"level3": {"value": "deeply nested"}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "#### value" in result

    def test_deeply_nested_structure_deeply_nested_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {"level1": {"level2": {"level3": {"value": "deeply nested"}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "deeply nested" in result


    def test_complex_nested_structure_project_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# project" in result

    def test_complex_nested_structure_name_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## name" in result

    def test_complex_nested_structure_team_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## team" in result

    def test_complex_nested_structure_alice_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* Alice" in result

    def test_complex_nested_structure_metadata_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## metadata" in result

    def test_complex_nested_structure_version_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "### version" in result

    def test_complex_nested_structure_features_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "project": {
                "name": "Test Project",
                "team": ["Alice", "Bob", "Charlie"],
                "metadata": {"version": "1.0", "features": ["feature1", "feature2"]},
            }
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "### features" in result



class TestJson2MdFormatting:
    """Test markdown formatting aspects."""

    def test_header_levels_l1_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# l1" in result

    def test_header_levels_l2_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "## l2" in result

    def test_header_levels_l3_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "### l3" in result

    def test_header_levels_l4_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "#### l4" in result

    def test_header_levels_l5_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "##### l5" in result

    def test_header_levels_l6_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Test up to 6 levels (markdown limit)
        data = {"l1": {"l2": {"l3": {"l4": {"l5": {"l6": "value"}}}}}}
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "###### l6" in result


    def test_spacing_between_sections(self):
        """Test proper spacing between sections."""
        # Arrange
        from scitex_io import json2md

        data = {"section1": "content1", "section2": "content2", "section3": "content3"}
        result = json2md(data)

        # Should have empty lines between sections
        # Act
        lines = result.split("\n")
        # Check that there are empty lines (after filtering)
        # Assert
        assert "" in lines or result.count("\n\n") >= 2

    def test_list_formatting_result_count_6(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "groceries": ["milk", "bread", "eggs"],
            "tasks": ["code", "test", "deploy"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert result.count("* ") == 6

    def test_list_formatting_milk_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "groceries": ["milk", "bread", "eggs"],
            "tasks": ["code", "test", "deploy"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* milk" in result

    def test_list_formatting_code_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "groceries": ["milk", "bread", "eggs"],
            "tasks": ["code", "test", "deploy"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* code" in result



class TestJson2MdEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_dict_result_equals_case(self):
        """Test converting empty dictionary."""
        # Arrange
        from scitex_io import json2md

        data = {}
        # Act
        result = json2md(data)

        # Assert
        assert result == ""

    def test_empty_list_result_equals_case(self):
        """Test converting empty list."""
        # Arrange
        from scitex_io import json2md

        data = []
        # Act
        result = json2md(data)

        # Assert
        assert result == ""

    def test_single_value_types_json2md_string(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io import json2md
        # Act
        # Assert
        # Assert
        assert json2md("string") == ""  # Non-dict/list returns empty

    def test_single_value_types_json2md_123(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io import json2md
        # Act
        # Assert
        # Assert
        assert json2md(123) == ""

    def test_single_value_types_json2md_true(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io import json2md
        # Act
        # Assert
        # Assert
        assert json2md(True) == ""

    def test_single_value_types_json2md_none(self):
        # Arrange
        # Arrange
        # Act
        from scitex_io import json2md
        # Act
        # Assert
        # Assert
        assert json2md(None) == ""


    def test_special_characters_in_keys_key_with_spaces_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "key with spaces": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
            "key.with.dots": "value4",
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# key with spaces" in result

    def test_special_characters_in_keys_key_with_dashes_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "key with spaces": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
            "key.with.dots": "value4",
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# key-with-dashes" in result

    def test_special_characters_in_keys_key_with_underscores_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "key with spaces": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
            "key.with.dots": "value4",
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# key_with_underscores" in result

    def test_special_characters_in_keys_key_with_dots_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "key with spaces": "value1",
            "key-with-dashes": "value2",
            "key_with_underscores": "value3",
            "key.with.dots": "value4",
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "# key.with.dots" in result


    def test_unicode_content_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "greeting": "你好",
            "emoji": "🚀 Launch",
            "languages": ["English", "中文", "日本語", "한국어"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "你好" in result

    def test_unicode_content_launch_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "greeting": "你好",
            "emoji": "🚀 Launch",
            "languages": ["English", "中文", "日本語", "한국어"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "🚀 Launch" in result

    def test_unicode_content_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "greeting": "你好",
            "emoji": "🚀 Launch",
            "languages": ["English", "中文", "日本語", "한국어"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* 中文" in result

    def test_unicode_content_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        data = {
            "greeting": "你好",
            "emoji": "🚀 Launch",
            "languages": ["English", "中文", "日本語", "한국어"],
        }
        # Act
        result = json2md(data)
        # Act
        # Assert
        # Assert
        assert "* 日本語" in result



class TestJson2MdMain:
    """Test the main function and CLI interface."""

    def test_main_with_valid_json_file(self, tmp_path):
        """Test main function with valid JSON file."""
        # Arrange
        # Act
        # Assert
        import sys

        from scitex_io._json2md import main

        # Create test JSON file
        test_data = {"title": "Test", "items": ["a", "b", "c"]}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(test_data))

        # Mock command line arguments
        original_argv = sys.argv
        try:
            sys.argv = ["json2md", str(json_file)]

            # Capture stdout
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                main()

            output = f.getvalue()
            assert "# title" in output
            assert "* a" in output

        finally:
            sys.argv = original_argv

    def test_main_with_output_file(self, tmp_path):
        """Test main function with output file option."""
        # Arrange
        # Act
        # Assert
        import sys

        from scitex_io._json2md import main

        # Create test JSON file
        test_data = {"section": "content"}
        json_file = tmp_path / "input.json"
        json_file.write_text(json.dumps(test_data))
        output_file = tmp_path / "output.md"

        # Mock command line arguments
        original_argv = sys.argv
        try:
            sys.argv = ["json2md", str(json_file), "-o", str(output_file)]
            main()

            # Check output file created and contains expected content
            assert output_file.exists()
            content = output_file.read_text()
            assert "# section" in content
            assert "content" in content

        finally:
            sys.argv = original_argv

    def test_main_with_nonexistent_file(self, tmp_path):
        """Test main function with nonexistent file."""
        # Arrange
        # Act
        # Assert
        import sys

        from scitex_io._json2md import main

        nonexistent = tmp_path / "does_not_exist.json"

        original_argv = sys.argv
        try:
            sys.argv = ["json2md", str(nonexistent)]

            # Should exit with error
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

        finally:
            sys.argv = original_argv


class TestJson2MdIntegration:
    """Test integration scenarios."""

    def test_round_trip_json_to_md(self):
        """Test converting various JSON structures to markdown."""
        # Arrange
        # Act
        # Assert
        from scitex_io import json2md

        test_cases = [
            # Simple dict
            {"key": "value"},
            # Nested dict
            {"outer": {"inner": "value"}},
            # Dict with list
            {"items": [1, 2, 3]},
            # List of dicts
            [{"a": 1}, {"b": 2}],
            # Complex structure
            {
                "metadata": {"title": "Report", "date": "2024-01-01"},
                "sections": [
                    {"name": "Introduction", "content": "..."},
                    {"name": "Conclusion", "content": "..."},
                ],
            },
        ]

        for data in test_cases:
            result = json2md(data)
            assert isinstance(result, str)
            # Verify some conversion happened (not empty for non-empty inputs)
            if data:
                assert len(result) > 0

    def test_large_json_conversion_result_is_str(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Create a large nested structure
        large_data = {
            f"section_{i}": {
                f"subsection_{j}": [f"item_{k}" for k in range(10)] for j in range(5)
            }
            for i in range(10)
        }
        # Act
        result = json2md(large_data)
        # Act
        # Assert
        # Assert
        assert isinstance(result, str)

    def test_large_json_conversion_section_0_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Create a large nested structure
        large_data = {
            f"section_{i}": {
                f"subsection_{j}": [f"item_{k}" for k in range(10)] for j in range(5)
            }
            for i in range(10)
        }
        # Act
        result = json2md(large_data)
        # Act
        # Assert
        # Assert
        assert "section_0" in result

    def test_large_json_conversion_subsection_0_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Create a large nested structure
        large_data = {
            f"section_{i}": {
                f"subsection_{j}": [f"item_{k}" for k in range(10)] for j in range(5)
            }
            for i in range(10)
        }
        # Act
        result = json2md(large_data)
        # Act
        # Assert
        # Assert
        assert "subsection_0" in result

    def test_large_json_conversion_item_0_in_result(self):
        # Arrange
        # Arrange
        from scitex_io import json2md
        # Create a large nested structure
        large_data = {
            f"section_{i}": {
                f"subsection_{j}": [f"item_{k}" for k in range(10)] for j in range(5)
            }
            for i in range(10)
        }
        # Act
        result = json2md(large_data)
        # Act
        # Assert
        # Assert
        assert "* item_0" in result



# --------------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_json2md.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-10-30 09:08:07 (ywatanabe)"
# # File: /home/ywatanabe/proj/scitex-code/src/scitex/io/_json2md.py
# # ----------------------------------------
# from __future__ import annotations
# import os
#
# __FILE__ = "./src/scitex/io/_json2md.py"
# __DIR__ = os.path.dirname(__FILE__)
# # ----------------------------------------
#
# import json
# import sys
# import argparse
#
#
# def json2md(obj, level=1):
#     output = []
#     if isinstance(obj, dict):
#         for key, value in obj.items():
#             if output:  # Add extra newline between sections
#                 output.append("")
#             output.append("#" * level + " " + str(key))
#             if isinstance(value, (dict, list)):
#                 output.append(json2md(value, level + 1))
#             else:
#                 output.append(str(value) + "\n")
#     elif isinstance(obj, list):
#         for item in obj:
#             if isinstance(item, (dict, list)):
#                 output.append(json2md(item, level))
#             else:
#                 output.append("* " + str(item))
#     return "\n".join(filter(None, output))
#
#
# def main():
#     parser = argparse.ArgumentParser(description="Convert JSON to Markdown")
#     parser.add_argument("input", help="Input JSON file")
#     parser.add_argument("-o", "--output", help="Output file (default: stdout)")
#     args = parser.parse_args()
#
#     try:
#         with open(args.input, "r") as f:
#             data = json.load(f)
#
#         result = json2md(data)
#
#         if args.output:
#             with open(args.output, "w") as f:
#                 f.write(result)
#         else:
#             print(result)
#
#     except FileNotFoundError:
#         print(f"Error: File {args.input} not found", file=sys.stderr)
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     main()
#
# """
# python ./Ninja/workspace/formats/json2md.py
# python -m workspace.formats.json2md
# """
# # #!/usr/bin/env python3
# # # -*- coding: utf-8 -*-
# # # Time-stamp: "2024-12-19 15:29:28 (ywatanabe)"
# # # File: ./Ninja/workspace/formats/json2md.py
#
# # THIS_FILE = "/home/ywatanabe/.emacs.d/lisp/Ninja/workspace/formats/json2md.py"
#
# # import json
# # import sys
#
# # def json2md(obj, level=1):
# #     output = []
# #     if isinstance(obj, dict):
# #         for key, value in obj.items():
# #             if output:  # Add extra newline between sections
# #                 output.append("")
# #             output.append("#" * level + " " + str(key))
# #             if isinstance(value, (dict, list)):
# #                 output.append(json2md(value, level + 1))
# #             else:
# #                 output.append(str(value) + "\n")
# #     elif isinstance(obj, list):
# #         for item in obj:
# #             if isinstance(item, (dict, list)):
# #                 output.append(json2md(item, level))
# #             else:
# #                 output.append("* " + str(item))
# #     return "\n".join(filter(None, output))
#
# # def main():
# #     if len(sys.argv) != 2:
# #         print("Usage: json2md.py <input.json>")
# #         sys.exit(1)
#
# #     lpath = sys.argv[1].replace("/./", "/")
# #     with open(lpath, "r") as f:
# #         data = json.load(f)
#
#
# # if __name__ == "__main__":
# #     main()
#
#
# # """
# # python ./Ninja/workspace/formats/json2md.py
# # python -m workspace.formats.json2md
# # """
#
# # # EOF
#
# # EOF

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_json2md.py
# --------------------------------------------------------------------------------
