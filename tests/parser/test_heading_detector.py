from xml.etree import ElementTree as ET

from documind.parser.heading_detector import HeadingDetector


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _p_with_style(style_id: str, text: str) -> ET.Element:
    return ET.fromstring(
        f"""
        <w:p xmlns:w="{W_NS}">
          <w:pPr><w:pStyle w:val="{style_id}" /></w:pPr>
          <w:r><w:t>{text}</w:t></w:r>
        </w:p>
        """
    )


def _styles_xml() -> ET.Element:
    return ET.fromstring(
        f"""
        <w:styles xmlns:w="{W_NS}">
          <w:style w:type="paragraph" w:styleId="h1">
            <w:name w:val="heading 1" />
            <w:pPr><w:outlineLvl w:val="0" /></w:pPr>
          </w:style>
          <w:style w:type="paragraph" w:styleId="h2">
            <w:name w:val="heading 2" />
            <w:pPr><w:outlineLvl w:val="1" /></w:pPr>
          </w:style>
        </w:styles>
        """
    )


def test_detects_heading_level_from_styles_xml():
    detector = HeadingDetector(_styles_xml())
    paragraph = _p_with_style("h2", "2.1 Scope")

    heading = detector.detect(paragraph, "2.1 Scope")

    assert heading is not None
    assert heading.level == 2
    assert heading.text == "2.1 Scope"


def test_falls_back_to_numbered_heading_regex_without_style():
    detector = HeadingDetector(_styles_xml())
    paragraph = ET.fromstring(
        f"""
        <w:p xmlns:w="{W_NS}">
          <w:r><w:t>5.1.3 Adjust UI</w:t></w:r>
        </w:p>
        """
    )

    heading = detector.detect(paragraph, "5.1.3 Adjust UI")

    assert heading is not None
    assert heading.level == 3


def test_does_not_treat_plain_numbered_list_item_as_heading_without_style():
    detector = HeadingDetector(_styles_xml())
    paragraph = ET.fromstring(
        f"""
        <w:p xmlns:w="{W_NS}">
          <w:r><w:t>1 First item</w:t></w:r>
        </w:p>
        """
    )

    heading = detector.detect(paragraph, "1 First item")

    assert heading is None
