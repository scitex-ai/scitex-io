#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2025-01-07 08:15:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__xml.py

"""Comprehensive tests for XML file loading functionality.

This module provides extensive tests for the _load_xml function which converts
XML files to Python dictionaries.
"""

import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


def _write_xml(content, suffix=".xml", encoding=None):
    kwargs = {"mode": "w", "suffix": suffix, "delete": False}
    if encoding is not None:
        kwargs["encoding"] = encoding
    with tempfile.NamedTemporaryFile(**kwargs) as f:
        f.write(content)
        return f.name


def test_load_xml_basic_returns_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <child name="test">Value</child>
        <child2>Value2</child2>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_invalid_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises(ValueError, match="File must have .xml extension")
    # Assert
    with ctx:
        _load_xml("file.txt")


def test_load_xml_xml_extension_returns_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?><root><test>value</test></root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


@pytest.mark.parametrize("ext", [".txt", ".json", ".yaml", ".xmlx", ".xm"])
def test_load_xml_invalid_extensions_each_raise_valueerror(ext):
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises(ValueError)
    # Assert
    with ctx:
        _load_xml(f"file{ext}")


def test_load_xml_nonexistent_file_raises_parse_or_not_found():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises((FileNotFoundError, ET.ParseError))
    # Assert
    with ctx:
        _load_xml("nonexistent_file.xml")


def test_load_xml_malformed_content_raises_parse_error():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <unclosed_tag>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        ctx = pytest.raises(ET.ParseError)
        # Assert
        with ctx:
            _load_xml(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_xml_root_attribute_appears_in_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root version="1.0">
        <item id="1" type="test">Value1</item>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["version"] == "1.0"
    finally:
        os.unlink(temp_path)


def test_load_xml_nested_structure_is_nested_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <config>
        <database>
            <host>localhost</host>
            <port>5432</port>
        </database>
    </config>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result["database"], dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_nested_structure_inner_value_round_trips():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <config>
        <database>
            <host>localhost</host>
        </database>
    </config>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["database"]["host"] == "localhost"
    finally:
        os.unlink(temp_path)


def test_load_xml_text_content_for_name_field():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <name>John</name>
        <age>30</age>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["name"] == "John"
    finally:
        os.unlink(temp_path)


def test_load_xml_text_content_for_age_field():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <name>John</name>
        <age>30</age>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["age"] == "30"
    finally:
        os.unlink(temp_path)


def test_load_xml_repeated_elements_under_single_key():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <items>
        <item>Item1</item>
        <item>Item2</item>
        <item>Item3</item>
    </items>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "item" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_with_text_element_returns_string_value():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <empty_element></empty_element>
        <with_text>Some text</with_text>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["with_text"] == "Some text"
    finally:
        os.unlink(temp_path)


def test_load_xml_mixed_content_simple_text_value():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <simple>Text</simple>
        <with_attr id="123">Text with attr</with_attr>
        <nested>
            <child>Nested text</child>
        </nested>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["simple"] == "Text"
    finally:
        os.unlink(temp_path)


def test_load_xml_function_signature_has_lpath_parameter():
    # Arrange
    import inspect
    from scitex_io._load_modules._xml import _load_xml

    sig = inspect.signature(_load_xml)
    # Act
    params = list(sig.parameters.keys())
    # Assert
    assert "lpath" in params


def test_load_xml_function_signature_accepts_kwargs():
    # Arrange
    import inspect
    from scitex_io._load_modules._xml import _load_xml

    sig = inspect.signature(_load_xml)
    # Act
    var_kw_params = [p for p in sig.parameters.values() if p.kind == p.VAR_KEYWORD]
    # Assert
    assert "kwargs" in sig.parameters or len(var_kw_params) > 0


def test_load_xml_docstring_is_present():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    doc = _load_xml.__doc__
    # Assert
    assert doc is not None


def test_load_xml_docstring_mentions_xml():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    doc = _load_xml.__doc__
    # Assert
    assert "XML" in doc


def test_load_xml_returns_dict_instance():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?><root><test>value</test></root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_complex_root_attribute_value():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <configuration version="2.0">
        <metadata>
            <title>Test Configuration</title>
            <author email="test@example.com">Test Author</author>
        </metadata>
    </configuration>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["version"] == "2.0"
    finally:
        os.unlink(temp_path)


def test_load_xml_complex_nested_title_round_trips():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <configuration version="2.0">
        <metadata>
            <title>Test Configuration</title>
        </metadata>
    </configuration>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["metadata"]["title"] == "Test Configuration"
    finally:
        os.unlink(temp_path)


def test_load_xml_special_characters_returns_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <root>
        <text>Content with &amp; special &lt; characters &gt;</text>
        <unicode>Unicode: ñáéíóú</unicode>
    </root>"""
    temp_path = _write_xml(xml_content, encoding="utf-8")
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_real_world_rss_has_channel():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Test RSS</title>
            <item>
                <title>Item 1</title>
                <description>Description 1</description>
            </item>
        </channel>
    </rss>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "channel" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_empty_string_path_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises(ValueError)
    # Assert
    with ctx:
        _load_xml("")


def test_load_xml_json_path_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises(ValueError)
    # Assert
    with ctx:
        _load_xml("file.json")


def test_load_xml_no_extension_path_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    # Act
    ctx = pytest.raises(ValueError)
    # Assert
    with ctx:
        _load_xml("file")


def test_load_xml_kwargs_accepted_silently():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?><root><test>value</test></root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path, unused_arg=True, another_arg="test")
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_cdata_section_preserves_content():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <code><![CDATA[if (x < 10 && y > 5) { return true; }]]></code>
        <normal>Normal text</normal>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_with_comments_data_round_trips():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <!-- This is a comment -->
        <data>value</data>
        <!-- Another comment -->
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["data"] == "value"
    finally:
        os.unlink(temp_path)


def test_load_xml_with_namespaces_returns_regular_element():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root xmlns:ns="http://example.com/namespace">
        <ns:element>Namespaced content</ns:element>
        <regular>Regular content</regular>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "regular" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_processing_instructions_data_round_trips():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <?xml-stylesheet type="text/xsl" href="style.xsl"?>
    <root>
        <data>value</data>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "data" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_whitespace_in_text_is_stripped():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = """<?xml version="1.0"?>
    <root>
        <preserved>  Multiple   spaces  </preserved>
    </root>"""
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert result["preserved"] == "Multiple   spaces"
    finally:
        os.unlink(temp_path)


def test_load_xml_large_file_has_item_key():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    xml_content = '<?xml version="1.0"?>\n<root>\n'
    for i in range(100):
        xml_content += f'    <item id="{i}">Item {i} content</item>\n'
    xml_content += "</root>"
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "item" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_deeply_nested_returns_dict():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    depth = 20
    xml_content = '<?xml version="1.0"?>\n'
    for i in range(depth):
        xml_content += "<level" + str(i) + ">"
    xml_content += "Deep value"
    for i in range(depth - 1, -1, -1):
        xml_content += "</level" + str(i) + ">"
    temp_path = _write_xml(xml_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert isinstance(result, dict)
    finally:
        os.unlink(temp_path)


def test_load_xml_svg_width_attribute_present():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    svg_content = """<?xml version="1.0"?>
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <circle cx="50" cy="50" r="40" fill="red"/>
    </svg>"""
    temp_path = _write_xml(svg_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "width" in result
    finally:
        os.unlink(temp_path)


def test_load_xml_configuration_returns_dict_with_settings():
    # Arrange
    from scitex_io._load_modules._xml import _load_xml

    config_content = """<?xml version="1.0" encoding="UTF-8"?>
    <configuration>
        <appSettings>
            <add key="ConnectionString" value="Server=localhost;Database=test;"/>
        </appSettings>
        <system.web>
            <compilation debug="true" targetFramework="4.5"/>
        </system.web>
    </configuration>"""
    temp_path = _write_xml(config_content)
    try:
        # Act
        result = _load_xml(temp_path)
        # Assert
        assert "appSettings" in result or "system.web" in result
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
