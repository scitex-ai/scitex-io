import os
import tempfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

from scitex_io import XmlDictConfig, XmlListConfig, xml2dict


class TestXmlDictConfigBasic:
    """Test basic XmlDictConfig functionality."""

    def test_simple_element_result_equals_case(self):
        """Test conversion of simple XML element."""
        # Arrange
        xml_string = "<root>Hello World</root>"
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result == {}  # Text is in root.text, not in dict

    def test_single_child_element(self):
        """Test XML with single child element."""
        # Arrange
        xml_string = "<root><child>value</child></root>"
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result == {"child": "value"}

    def test_multiple_child_elements(self):
        """Test XML with multiple different child elements."""
        # Arrange
        xml_string = """
        <root>
            <name>John</name>
            <age>30</age>
            <city>New York</city>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result == {"name": "John", "age": "30", "city": "New York"}

    def test_attributes_only_result_equals_id_123_type_test(self):
        """Test XML element with attributes only."""
        # Arrange
        xml_string = '<root id="123" type="test"/>'
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result == {"id": "123", "type": "test"}

    def test_attributes_with_child_result_id_123(self):
        # Arrange
        # Arrange
        xml_string = '<root id="123"><child>value</child></root>'
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["id"] == "123"

    def test_attributes_with_child_result_child_value(self):
        # Arrange
        # Arrange
        xml_string = '<root id="123"><child>value</child></root>'
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["child"] == "value"



class TestXmlDictConfigNested:
    """Test XmlDictConfig with nested structures."""

    def test_nested_elements_result_level1_level2_level3_deep_value(self):
        """Test deeply nested XML structure."""
        # Arrange
        xml_string = """
        <root>
            <level1>
                <level2>
                    <level3>deep value</level3>
                </level2>
            </level1>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result["level1"]["level2"]["level3"] == "deep value"

    def test_mixed_content_person_in_result(self):
        """Test XML with mixed content types."""
        # Arrange
        xml_string = """
        <root>
            <person id="1">
                <name>Alice</name>
                <age>25</age>
            </person>
            <person id="2">
                <name>Bob</name>
                <age>30</age>
            </person>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # When multiple elements have same tag, should create a list
        # Assert
        assert "person" in result

    def test_empty_elements_result_empty1_is_none(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <empty1></empty1>
            <empty2/>
            <nonempty>value</nonempty>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["empty1"] is None

    def test_empty_elements_result_empty2_is_none(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <empty1></empty1>
            <empty2/>
            <nonempty>value</nonempty>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["empty2"] is None

    def test_empty_elements_result_nonempty_value(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <empty1></empty1>
            <empty2/>
            <nonempty>value</nonempty>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["nonempty"] == "value"



class TestXmlListConfig:
    """Test XmlListConfig functionality."""

    def test_list_creation_result_equals_first_second_third(self):
        """Test creation of list from repeated elements."""
        # Arrange
        xml_string = """
        <items>
            <item>First</item>
            <item>Second</item>
            <item>Third</item>
        </items>
        """
        root = ElementTree.XML(xml_string)
        # Manually create list config
        items = root.findall("item")
        # Act
        result = XmlListConfig(items)
        # Assert
        assert result == ["First", "Second", "Third"]

    def test_list_with_attributes(self):
        """Test list elements with attributes."""
        # Arrange
        xml_string = """
        <items>
            <item id="1">First</item>
            <item id="2">Second</item>
        </items>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Should detect repeated 'item' tags and create appropriate structure
        # Assert
        assert "item" in result

    def test_empty_list_elements(self):
        """Test list with some empty elements."""
        # Arrange
        xml_string = """
        <items>
            <item>Value</item>
            <item></item>
            <item>Another</item>
        </items>
        """
        root = ElementTree.XML(xml_string)
        items = root.findall("item")
        # Act
        result = XmlListConfig(items)
        # Empty elements might be skipped or included as None
        # Assert
        assert len(result) >= 2  # At least the non-empty items


class TestXml2Dict:
    """Test the main xml2dict function."""

    def test_file_parsing_smoke_case(self):
        """Test parsing XML from file."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <catalog>
            <book id="1">
                <author>Smith</author>
                <title>Python Guide</title>
                <price>29.99</price>
            </book>
            <book id="2">
                <author>Jones</author>
                <title>XML Processing</title>
                <price>39.99</price>
            </book>
        </catalog>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        # Act
        try:
            result = xml2dict(temp_path)
            books = result.get("book")
            if isinstance(books, list):
                shape = ("list", len(books))
            else:
                # Single book or dict structure
                shape = ("scalar", "author" in str(result))
        finally:
            os.unlink(temp_path)
        # Assert
        assert shape in (("list", 2), ("scalar", True))

    def test_simple_config_file(self):
        """Test parsing a simple configuration XML."""
        # Arrange
        xml_content = """<?xml version="1.0"?>
        <config>
            <database>
                <host>localhost</host>
                <port>5432</port>
                <name>mydb</name>
            </database>
            <cache>
                <enabled>true</enabled>
                <ttl>3600</ttl>
            </cache>
        </config>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        # Act
        try:
            result = xml2dict(temp_path)
            observed = (
                result["database"]["host"],
                result["database"]["port"],
                result["cache"]["enabled"],
                result["cache"]["ttl"],
            )
        finally:
            os.unlink(temp_path)
        # Assert
        assert observed == ("localhost", "5432", "true", "3600")

    def test_complex_structure_smoke_case(self):
        """Test parsing complex XML with mixed content."""
        # Arrange
        # Act
        # Assert
        xml_content = """<?xml version="1.0"?>
        <company name="TechCorp">
            <departments>
                <department id="1" name="Engineering">
                    <employee id="101">
                        <name>Alice</name>
                        <role>Developer</role>
                    </employee>
                    <employee id="102">
                        <name>Bob</name>
                        <role>Manager</role>
                    </employee>
                </department>
                <department id="2" name="Sales">
                    <employee id="201">
                        <name>Charlie</name>
                        <role>Sales Rep</role>
                    </employee>
                </department>
            </departments>
        </company>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            result = xml2dict(temp_path)
            observed = ("name" in result, "departments" in result)
        finally:
            os.unlink(temp_path)
        # Assert
        assert observed == (True, True)


class TestXmlDictConfigEdgeCases:
    """Test edge cases and special scenarios."""

    def test_text_with_whitespace_len_result_item_0(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <item>  Text with spaces  </item>
            <item2>
                Multiline
                Text
            </item2>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert len(result["item"]) > 0

    def test_text_with_whitespace_len_result_item2_0(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <item>  Text with spaces  </item>
            <item2>
                Multiline
                Text
            </item2>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert len(result["item2"]) > 0


    def test_special_characters_result_item_tag(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <item>&lt;tag&gt;</item>
            <item2>&amp;symbol</item2>
            <item3>&quot;quoted&quot;</item3>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["item"] == "<tag>"

    def test_special_characters_result_item2_symbol(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <item>&lt;tag&gt;</item>
            <item2>&amp;symbol</item2>
            <item3>&quot;quoted&quot;</item3>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["item2"] == "&symbol"

    def test_special_characters_result_item3_quoted(self):
        # Arrange
        # Arrange
        xml_string = """
        <root>
            <item>&lt;tag&gt;</item>
            <item2>&amp;symbol</item2>
            <item3>&quot;quoted&quot;</item3>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Act
        # Assert
        # Assert
        assert result["item3"] == '"quoted"'


    def test_cdata_section_function_test_in_result_script(self):
        """Test handling of CDATA sections."""
        # Arrange
        xml_string = """
        <root>
            <script><![CDATA[
                function test() {
                    return x < 10 && y > 5;
                }
            ]]></script>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # CDATA content should be preserved
        # Assert
        assert "function test()" in result["script"]

    def test_namespace_handling_len_result_0(self):
        """Test XML with namespaces."""
        # Arrange
        xml_string = """
        <root xmlns:custom="http://example.com/custom">
            <custom:element>Value</custom:element>
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Should handle namespaced elements
        # Assert
        assert len(result) > 0

    def test_comments_ignored_result_equals_item_value(self):
        """Test that XML comments are ignored."""
        # Arrange
        xml_string = """
        <root>
            <!-- This is a comment -->
            <item>Value</item>
            <!-- Another comment -->
        </root>
        """
        root = ElementTree.XML(xml_string)
        # Act
        result = XmlDictConfig(root)
        # Assert
        assert result == {"item": "Value"}


class TestRealWorldExamples:
    """Test with real-world XML examples."""

    def test_rss_feed_structure(self):
        """Test parsing RSS-like structure."""
        # Arrange
        # Act
        # Assert
        xml_content = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Example Feed</title>
                <link>http://example.com</link>
                <item>
                    <title>First Post</title>
                    <link>http://example.com/1</link>
                    <pubDate>2024-01-01</pubDate>
                </item>
                <item>
                    <title>Second Post</title>
                    <link>http://example.com/2</link>
                    <pubDate>2024-01-02</pubDate>
                </item>
            </channel>
        </rss>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            result = xml2dict(temp_path)
            channel = result.get("channel", {})
            observed = (
                "version" in result,
                "channel" in result,
                channel.get("title"),
                "item" in channel,
            )
        finally:
            os.unlink(temp_path)
        # Assert
        assert observed == (True, True, "Example Feed", True)

    def test_svg_structure_smoke_case(self):
        """Test parsing SVG-like XML structure."""
        # Arrange
        # Act
        # Assert
        xml_content = """<?xml version="1.0"?>
        <svg width="100" height="100">
            <circle cx="50" cy="50" r="40" fill="red"/>
            <rect x="10" y="10" width="30" height="30" fill="blue"/>
        </svg>
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            temp_path = f.name

        try:
            result = xml2dict(temp_path)
            observed = (
                result.get("width"),
                result.get("height"),
                "circle" in result,
                "rect" in result,
            )
        finally:
            os.unlink(temp_path)
        # Assert
        assert observed == ("100", "100", True, True)


# --------------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/gen/_xml2dict.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # Time-stamp: "2021-09-07 13:06:33 (ylab)"
#
# from xml.etree import cElementTree as ElementTree
#
#
# def xml2dict(lpath_xml):
#     # tree = ElementTree.parse('your_file.xml')
#     tree = ElementTree.parse(lpath_xml)
#     root = tree.getroot()
#     xmldict = XmlDictConfig(root)
#     return xmldict
#
#
# class XmlListConfig(list):
#     def __init__(self, aList):
#         for element in aList:
#             if element:
#                 # treat like dict
#                 if len(element) == 1 or element[0].tag != element[1].tag:
#                     self.append(XmlDictConfig(element))
#                 # treat like list
#                 elif element[0].tag == element[1].tag:
#                     self.append(XmlListConfig(element))
#             elif element.text:
#                 text = element.text.strip()
#                 if text:
#                     self.append(text)
#
#
# class XmlDictConfig(dict):
#     """
#     Example usage:
#
#     >>> tree = ElementTree.parse('your_file.xml')
#     >>> root = tree.getroot()
#     >>> xmldict = XmlDictConfig(root)
#
#     Or, if you want to use an XML string:
#
#     >>> root = ElementTree.XML(xml_string)
#     >>> xmldict = XmlDictConfig(root)
#
#     And then use xmldict for what it is... a dict.
#     """
#
#     def __init__(self, parent_element):
#         if parent_element.items():
#             self.update(dict(parent_element.items()))
#         for element in parent_element:
#             if element:
#                 # treat like dict - we assume that if the first two tags
#                 # in a series are different, then they are all different.
#                 if len(element) == 1 or element[0].tag != element[1].tag:
#                     aDict = XmlDictConfig(element)
#                 # treat like list - we assume that if the first two tags
#                 # in a series are the same, then the rest are the same.
#                 else:
#                     # here, we put the list in dictionary; the key is the
#                     # tag name the list elements all share in common, and
#                     # the value is the list itself
#                     aDict = {element[0].tag: XmlListConfig(element)}
#                 # if the tag has attributes, add those to the dict
#                 if element.items():
#                     aDict.update(dict(element.items()))
#                 self.update({element.tag: aDict})
#             # this assumes that if you've got an attribute in a tag,
#             # you won't be having any text. This may or may not be a
#             # good idea -- time will tell. It works for the way we are
#             # currently doing XML configuration files...
#             elif element.items():
#                 self.update({element.tag: dict(element.items())})
#             # finally, if there are no child tags and no attributes, extract
#             # the text
#             else:
#                 self.update({element.tag: element.text})

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/gen/_xml2dict.py
# --------------------------------------------------------------------------------
