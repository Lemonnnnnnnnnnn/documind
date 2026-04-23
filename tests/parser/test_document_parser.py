from pathlib import Path
from xml.etree import ElementTree as ET

from documind.constants import W_NS
from documind.parser.document_parser import DocumentParser
from documind.reader.package_reader import DocxPackage, PackageReader
from documind.types import CodeBlock, Heading, ImageBlock, LinkRun, Paragraph, TableBlock, TextRun

from tests.conftest import SAMPLE_DOCX
from tests.fixtures import build_complex_table_docx


def test_parses_public_sample_headings_images_tables_and_strike_text():
    package = PackageReader().load(SAMPLE_DOCX)
    document = DocumentParser().parse(package)

    headings = [block for block in document.blocks if isinstance(block, Heading)]
    paragraphs = [block for block in document.blocks if isinstance(block, Paragraph)]
    images = [block for block in document.blocks if isinstance(block, ImageBlock)]
    tables = [block for block in document.blocks if isinstance(block, TableBlock)]

    assert any(heading.text == "Overview" and heading.level == 1 for heading in headings)
    assert any(heading.text == "Glossary" and heading.level == 2 for heading in headings)
    assert len(images) >= 2
    assert tables
    assert any(
        run.strike and "Legacy workflow to retire." in run.text
        for paragraph in paragraphs
        for run in paragraph.runs
    )


def test_marks_generated_merged_tables_as_complex(tmp_path):
    package = PackageReader().load(build_complex_table_docx(tmp_path / "complex-table.docx"))
    document = DocumentParser().parse(package)

    tables = [block for block in document.blocks if isinstance(block, TableBlock)]

    assert any(table.complexity == "complex" for table in tables)


def test_paragraph_parser_keeps_hyperlink_text():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <w:r><w:t>Before </w:t></w:r>
          <w:hyperlink r:id="rId9">
            <w:r><w:t>LinkText</w:t></w:r>
          </w:hyperlink>
          <w:r><w:t> after</w:t></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(paragraph)

    assert text == "Before LinkText after"
    assert "".join(run.text for run in parsed.runs) == "Before LinkText after"


def test_paragraph_parser_extracts_relationship_hyperlink_as_link_run():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <w:r><w:t>Before </w:t></w:r>
          <w:hyperlink r:id="rId9">
            <w:r><w:t>LinkText</w:t></w:r>
          </w:hyperlink>
          <w:r><w:t> after</w:t></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(
        paragraph,
        relationships={"rId9": "https://example.com/spec"},
    )

    assert text == "Before LinkText after"
    assert parsed.runs == [
        TextRun(text="Before "),
        LinkRun(text="LinkText", url="https://example.com/spec", link_kind="external"),
        TextRun(text=" after"),
    ]


def test_paragraph_parser_extracts_anchor_hyperlink_as_link_run():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:hyperlink w:anchor="section_1">
            <w:r><w:t>Go to section</w:t></w:r>
          </w:hyperlink>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(paragraph)

    assert text == "Go to section"
    assert parsed.runs == [
        LinkRun(text="Go to section", url="#section_1", link_kind="external")
    ]


def test_paragraph_parser_keeps_wrapped_text_and_hyperlinks_in_order():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <w:r><w:t>Before </w:t></w:r>
          <w:ins>
            <w:r><w:t>Inserted </w:t></w:r>
            <w:hyperlink r:id="rId9">
              <w:r><w:t>LinkText</w:t></w:r>
            </w:hyperlink>
          </w:ins>
          <w:r><w:t> after</w:t></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(
        paragraph,
        relationships={"rId9": "https://example.com/spec"},
    )

    assert text == "Before Inserted LinkText after"
    assert parsed.runs == [
        TextRun(text="Before "),
        TextRun(text="Inserted "),
        LinkRun(text="LinkText", url="https://example.com/spec", link_kind="external"),
        TextRun(text=" after"),
    ]


def test_paragraph_parser_extracts_field_hyperlink_as_link_run():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:r><w:t>See </w:t></w:r>
          <w:r><w:fldChar w:fldCharType="begin" /></w:r>
          <w:r><w:instrText xml:space="preserve">HYPERLINK https://example.com/downloads/spec-sheet.xlsx \\tdfn spec-sheet.xlsx </w:instrText></w:r>
          <w:r><w:fldChar w:fldCharType="separate" /></w:r>
          <w:r><w:t>spec-sheet.xlsx</w:t></w:r>
          <w:r><w:fldChar w:fldCharType="end" /></w:r>
          <w:r><w:t> now</w:t></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(paragraph)

    assert text == "See spec-sheet.xlsx now"
    assert parsed.runs == [
        TextRun(text="See "),
        LinkRun(
            text="spec-sheet.xlsx",
            url="https://example.com/downloads/spec-sheet.xlsx",
            filename="spec-sheet.xlsx",
            link_kind="attachment",
        ),
        TextRun(text=" now"),
    ]


def test_paragraph_parser_keeps_split_field_instructions_parseable():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:r><w:fldChar w:fldCharType="begin" /></w:r>
          <w:r><w:instrText xml:space="preserve">HYPERLINK </w:instrText></w:r>
          <w:r><w:instrText xml:space="preserve">https://example.com/spec.xlsx </w:instrText></w:r>
          <w:r><w:instrText xml:space="preserve">\\tdfn %u89C4%u683C.xlsx </w:instrText></w:r>
          <w:r><w:fldChar w:fldCharType="separate" /></w:r>
          <w:r><w:t>规格.xlsx</w:t></w:r>
          <w:r><w:fldChar w:fldCharType="end" /></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(paragraph)

    assert text == "规格.xlsx"
    assert parsed.runs == [
        LinkRun(
            text="规格.xlsx",
            url="https://example.com/spec.xlsx",
            filename="规格.xlsx",
            link_kind="attachment",
        )
    ]


def test_paragraph_parser_extracts_field_anchor_hyperlink_as_link_run():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:r><w:fldChar w:fldCharType="begin" /></w:r>
          <w:r><w:instrText xml:space="preserve">HYPERLINK \\l "section_1" </w:instrText></w:r>
          <w:r><w:fldChar w:fldCharType="separate" /></w:r>
          <w:r><w:t>Go to section</w:t></w:r>
          <w:r><w:fldChar w:fldCharType="end" /></w:r>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(paragraph)

    assert text == "Go to section"
    assert parsed.runs == [
        LinkRun(text="Go to section", url="#section_1", link_kind="external")
    ]


def test_paragraph_parser_preserves_mixed_styles_inside_hyperlinks():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <w:hyperlink r:id="rId9">
            <w:r>
              <w:rPr><w:b /></w:rPr>
              <w:t>Bold</w:t>
            </w:r>
            <w:r><w:t> normal</w:t></w:r>
          </w:hyperlink>
        </w:p>
        """
    )

    parsed, text = parser._parse_paragraph(
        paragraph,
        relationships={"rId9": "https://example.com/spec"},
    )

    assert text == "Bold normal"
    assert parsed.runs == [
        LinkRun(text="Bold", url="https://example.com/spec", link_kind="external", bold=True),
        LinkRun(text=" normal", url="https://example.com/spec", link_kind="external"),
    ]


def test_paragraph_parser_detects_attachment_links_from_url_suffix():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
          <w:hyperlink r:id="rId9">
            <w:r><w:t>Download spec</w:t></w:r>
          </w:hyperlink>
        </w:p>
        """
    )

    parsed, _ = parser._parse_paragraph(
        paragraph,
        relationships={"rId9": "https://example.com/spec.pdf"},
    )

    assert parsed.runs == [
        LinkRun(text="Download spec", url="https://example.com/spec.pdf", link_kind="attachment")
    ]


def test_groups_numbered_paragraphs_into_list_block():
    package = DocxPackage(
        source_path=Path("demo.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p><w:r><w:t>Intro</w:t></w:r></w:p>
                <w:p>
                  <w:pPr>
                    <w:numPr>
                      <w:ilvl w:val="0" />
                      <w:numId w:val="8" />
                    </w:numPr>
                  </w:pPr>
                  <w:r><w:t>Top level</w:t></w:r>
                </w:p>
                <w:p>
                  <w:pPr>
                    <w:numPr>
                      <w:ilvl w:val="1" />
                      <w:numId w:val="8" />
                    </w:numPr>
                  </w:pPr>
                  <w:r><w:t>Nested one</w:t></w:r>
                </w:p>
                <w:p>
                  <w:pPr>
                    <w:numPr>
                      <w:ilvl w:val="1" />
                      <w:numId w:val="8" />
                    </w:numPr>
                  </w:pPr>
                  <w:r><w:t>Nested two</w:t></w:r>
                </w:p>
                <w:p><w:r><w:t>Tail</w:t></w:r></w:p>
              </w:body>
            </w:document>
            """
        ),
        styles_root=ET.fromstring(
            """
            <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" />
            """
        ),
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    assert [type(block).__name__ for block in document.blocks] == ["Paragraph", "ListBlock", "Paragraph"]
    list_block = document.blocks[1]
    items = getattr(list_block, "items", [])
    assert [getattr(item, "level", None) for item in items] == [0, 1, 1]
    assert [
        "".join(run.text for run in getattr(item, "runs", []))
        for item in items
    ] == ["Top level", "Nested one", "Nested two"]


def test_groups_numbered_paragraphs_with_links_into_list_block():
    package = DocxPackage(
        source_path=Path("demo.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
              <w:body>
                <w:p>
                  <w:pPr>
                    <w:numPr>
                      <w:ilvl w:val="0" />
                      <w:numId w:val="8" />
                    </w:numPr>
                  </w:pPr>
                  <w:r><w:t>See </w:t></w:r>
                  <w:hyperlink r:id="rId9">
                    <w:r><w:t>Download spec</w:t></w:r>
                  </w:hyperlink>
                </w:p>
              </w:body>
            </w:document>
            """
        ),
        styles_root=None,
        relationships={"rId9": "https://example.com/spec.pdf"},
        media_files={},
    )

    document = DocumentParser().parse(package)

    assert [type(block).__name__ for block in document.blocks] == ["ListBlock"]
    item = document.blocks[0].items[0]
    assert item.runs == [
        TextRun(text="See "),
        LinkRun(text="Download spec", url="https://example.com/spec.pdf", link_kind="attachment"),
    ]


def test_heading_style_still_wins_over_numbered_list_metadata():
    styles_root = ET.fromstring(
        f"""
        <w:styles xmlns:w="{W_NS}">
          <w:style w:type="paragraph" w:styleId="h2">
            <w:name w:val="heading 2" />
            <w:pPr><w:outlineLvl w:val="1" /></w:pPr>
          </w:style>
        </w:styles>
        """
    )
    package = DocxPackage(
        source_path=Path("demo.docx"),
        document_root=ET.fromstring(
            f"""
            <w:document xmlns:w="{W_NS}">
              <w:body>
                <w:p>
                  <w:pPr>
                    <w:pStyle w:val="h2" />
                    <w:numPr>
                      <w:ilvl w:val="0" />
                      <w:numId w:val="9" />
                    </w:numPr>
                  </w:pPr>
                  <w:r><w:t>2.1 Scope</w:t></w:r>
                </w:p>
                <w:p><w:r><w:t>Tail</w:t></w:r></w:p>
              </w:body>
            </w:document>
            """
        ),
        styles_root=styles_root,
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    assert isinstance(document.blocks[0], Heading)
    assert document.blocks[0].text == "2.1 Scope"
    assert [type(block).__name__ for block in document.blocks] == ["Heading", "Paragraph"]


def test_document_parser_marks_table_with_links_as_complex_and_preserves_link_runs():
    package = DocxPackage(
        source_path=Path("table-links.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                        xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
              <w:body>
                <w:tbl>
                  <w:tr>
                    <w:tc>
                      <w:p>
                        <w:r><w:t>See </w:t></w:r>
                        <w:hyperlink r:id="rId9">
                          <w:r><w:t>Download spec</w:t></w:r>
                        </w:hyperlink>
                      </w:p>
                    </w:tc>
                  </w:tr>
                </w:tbl>
              </w:body>
            </w:document>
            """
        ),
        styles_root=None,
        relationships={"rId9": "https://example.com/spec.pdf"},
        media_files={},
    )

    document = DocumentParser().parse(package)

    table = next(block for block in document.blocks if isinstance(block, TableBlock))
    paragraph = table.rows[0].cells[0].blocks[0]

    assert table.complexity == "complex"
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs == [
        TextRun(text="See "),
        LinkRun(text="Download spec", url="https://example.com/spec.pdf", link_kind="attachment"),
    ]


def test_document_parser_marks_table_with_anchor_links_as_complex():
    package = DocxPackage(
        source_path=Path("table-anchor-links.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:tbl>
                  <w:tr>
                    <w:tc>
                      <w:p>
                        <w:hyperlink w:anchor="section_1">
                          <w:r><w:t>Go to section</w:t></w:r>
                        </w:hyperlink>
                      </w:p>
                    </w:tc>
                  </w:tr>
                </w:tbl>
              </w:body>
            </w:document>
            """
        ),
        styles_root=None,
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    table = next(block for block in document.blocks if isinstance(block, TableBlock))
    paragraph = table.rows[0].cells[0].blocks[0]

    assert table.complexity == "complex"
    assert isinstance(paragraph, Paragraph)
    assert paragraph.runs == [
        LinkRun(text="Go to section", url="#section_1", link_kind="external")
    ]


def test_document_parser_attaches_bookmark_only_paragraph_to_following_heading():
    styles_root = ET.fromstring(
        """
        <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:style w:type="paragraph" w:styleId="Heading1">
            <w:name w:val="heading 1" />
          </w:style>
        </w:styles>
        """
    )
    package = DocxPackage(
        source_path=Path("heading-links.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p>
                  <w:bookmarkStart w:id="1" w:name="_Toc123" />
                  <w:bookmarkEnd w:id="1" />
                </w:p>
                <w:p>
                  <w:pPr><w:pStyle w:val="Heading1" /></w:pPr>
                  <w:r><w:t>1 Overview</w:t></w:r>
                </w:p>
              </w:body>
            </w:document>
            """
        ),
        styles_root=styles_root,
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    heading = next(block for block in document.blocks if isinstance(block, Heading))

    assert heading.text == "1 Overview"
    assert heading.anchor == "_Toc123"


def test_paragraph_parser_extracts_field_filename_before_following_switches():
    parser = DocumentParser()
    paragraph = ET.fromstring(
        """
        <w:p xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:r><w:fldChar w:fldCharType="begin" /></w:r>
          <w:r><w:instrText xml:space="preserve">HYPERLINK https://drive.example/item \\tdfn spec.xlsx \\o "tip" </w:instrText></w:r>
          <w:r><w:fldChar w:fldCharType="separate" /></w:r>
          <w:r><w:t>spec.xlsx</w:t></w:r>
          <w:r><w:fldChar w:fldCharType="end" /></w:r>
        </w:p>
        """
    )

    parsed, _ = parser._parse_paragraph(paragraph)

    assert parsed.runs == [
        LinkRun(
            text="spec.xlsx",
            url="https://drive.example/item",
            filename="spec.xlsx",
            link_kind="attachment",
        )
    ]


def test_document_parser_attaches_bookmark_only_paragraph_to_following_table():
    package = DocxPackage(
        source_path=Path("table-anchor.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:body>
                <w:p>
                  <w:bookmarkStart w:id="1" w:name="_RefTable1" />
                  <w:bookmarkEnd w:id="1" />
                </w:p>
                <w:tbl>
                  <w:tr>
                    <w:tc>
                      <w:p><w:r><w:t>A</w:t></w:r></w:p>
                    </w:tc>
                  </w:tr>
                </w:tbl>
              </w:body>
            </w:document>
            """
        ),
        styles_root=None,
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    table = next(block for block in document.blocks if isinstance(block, TableBlock))

    assert table.anchor == "_RefTable1"


def test_extracts_code_block_from_textbox_paragraph():
    package = DocxPackage(
        source_path=Path("textbox-code.docx"),
        document_root=ET.fromstring(
            """
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                        xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                        xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                        xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
              <w:body>
                <w:p>
                  <w:r>
                    <w:drawing>
                      <wp:inline>
                        <a:graphic>
                          <a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
                            <wps:wsp>
                              <wps:txbx>
                                <w:txbxContent>
                                  <w:p>
                                    <w:pPr><w:pStyle w:val="codepara" /></w:pPr>
                                    <w:r><w:t>/**</w:t></w:r>
                                  </w:p>
                                  <w:p>
                                    <w:pPr><w:pStyle w:val="codepara" /></w:pPr>
                                    <w:r><w:t xml:space="preserve">    private String twoElementCheckStatus;</w:t></w:r>
                                  </w:p>
                                  <w:p>
                                    <w:pPr><w:pStyle w:val="codepara" /></w:pPr>
                                  </w:p>
                                  <w:p>
                                    <w:pPr><w:pStyle w:val="codepara" /></w:pPr>
                                    <w:r><w:t>*/</w:t></w:r>
                                  </w:p>
                                </w:txbxContent>
                              </wps:txbx>
                            </wps:wsp>
                          </a:graphicData>
                        </a:graphic>
                      </wp:inline>
                    </w:drawing>
                  </w:r>
                </w:p>
              </w:body>
            </w:document>
            """
        ),
        styles_root=ET.fromstring(
            """
            <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
              <w:style w:type="paragraph" w:styleId="codepara">
                <w:name w:val="melo-codeblock-Base-theme-para" />
              </w:style>
            </w:styles>
            """
        ),
        relationships={},
        media_files={},
    )

    document = DocumentParser().parse(package)

    assert document.blocks == [
        CodeBlock(text="/**\n    private String twoElementCheckStatus;\n\n*/")
    ]
