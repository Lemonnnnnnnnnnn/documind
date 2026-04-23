from pathlib import Path

from documind.render.link_resolver import build_anchor_map
from documind.render.markdown_renderer import MarkdownRenderer
from documind.types import (
    CodeBlock,
    Chunk,
    Heading,
    ImageBlock,
    LinkRun,
    ListBlock,
    ListItem,
    Paragraph,
    TableBlock,
    TableCell,
    TableRow,
    TextRun,
)


def test_renders_inline_styles_images_and_simple_table():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="1 Overview",
        level=1,
        source_path=Path("demo.docx"),
        output_name="1-overview/index.md",
        relative_dir="1-overview",
        breadcrumbs=[],
        blocks=[
            Heading(level=1, text="1 Overview"),
            Paragraph(
                runs=[
                    TextRun(text="Keep "),
                    TextRun(text="bold", bold=True),
                    TextRun(text=", "),
                    TextRun(text="italic", italic=True),
                    TextRun(text=", "),
                    TextRun(text="strike", strike=True),
                ]
            ),
            ImageBlock(rel_id="rId5", asset_path="./assets/img_001.png", alt_text="hero"),
            TableBlock(
                rows=[
                    TableRow(cells=[TableCell(text="Term"), TableCell(text="Meaning")]),
                    TableRow(cells=[TableCell(text="RAG"), TableCell(text="Retrieval augmented generation")]),
                ],
                complexity="simple",
            ),
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert output.startswith("---\n")
    assert 'path: "1-overview/index.md"' in output
    assert 'parent_path: null' in output
    assert "# 1 Overview" in output
    assert "**bold**" in output
    assert "*italic*" in output
    assert "~~strike~~" in output
    assert "![hero](../assets/img_001.png)" in output
    assert "| Term | Meaning |" in output


def test_renders_soft_breaks_inside_paragraph_runs():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Breaks",
        level=1,
        source_path=Path("demo.docx"),
        output_name="breaks/index.md",
        relative_dir="breaks",
        breadcrumbs=[],
        blocks=[Paragraph(runs=[TextRun(text="Line 1\nLine 2")])],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "Line 1  \nLine 2" in output


def test_renders_markdown_links_inside_paragraphs():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Links",
        level=1,
        source_path=Path("demo.docx"),
        output_name="links/index.md",
        relative_dir="links",
        breadcrumbs=[],
        blocks=[
            Paragraph(
                runs=[
                    TextRun(text="下载 "),
                    LinkRun(
                        text="spec-sheet.xlsx",
                        url="https://example.com/downloads/spec-sheet.xlsx",
                        filename="spec-sheet.xlsx",
                        link_kind="attachment",
                        bold=True,
                    ),
                    TextRun(text=" 查看"),
                ]
            )
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "**[spec-sheet.xlsx](https://example.com/downloads/spec-sheet.xlsx)**" in output


def test_can_force_html_table_mode_for_simple_table():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Tables",
        level=1,
        source_path=Path("demo.docx"),
        output_name="tables/index.md",
        relative_dir="tables",
        breadcrumbs=[],
        blocks=[
            TableBlock(
                rows=[
                    TableRow(cells=[TableCell(text="A"), TableCell(text="B")]),
                    TableRow(cells=[TableCell(text="1"), TableCell(text="2")]),
                ],
                complexity="simple",
            )
        ],
    )

    output = MarkdownRenderer(table_mode="html").render_chunk(chunk)

    assert "<table>" in output


def test_renders_nested_list_blocks_with_inline_styles():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Lists",
        level=1,
        source_path=Path("demo.docx"),
        output_name="lists/index.md",
        relative_dir="lists",
        breadcrumbs=[],
        blocks=[
            ListBlock(
                items=[
                    ListItem(runs=[TextRun(text="Top level")], level=0),
                    ListItem(
                        runs=[TextRun(text="Nested "), TextRun(text="detail", bold=True)],
                        level=1,
                    ),
                    ListItem(runs=[TextRun(text="Tail item")], level=0),
                ]
            )
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "\n- Top level\n    - Nested **detail**\n- Tail item\n" in output


def test_renders_markdown_links_inside_list_items():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Lists",
        level=1,
        source_path=Path("demo.docx"),
        output_name="lists/index.md",
        relative_dir="lists",
        breadcrumbs=[],
        blocks=[
            ListBlock(
                items=[
                    ListItem(
                        runs=[
                            TextRun(text="下载 "),
                            LinkRun(
                                text="spec-sheet.xlsx",
                                url="https://example.com/downloads/spec-sheet.xlsx",
                                filename="spec-sheet.xlsx",
                                link_kind="attachment",
                            ),
                        ],
                        level=0,
                    )
                ]
            )
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "\n- 下载 [spec-sheet.xlsx](https://example.com/downloads/spec-sheet.xlsx)\n" in output


def test_normalizes_non_zero_starting_list_levels_for_markdown_output():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Lists",
        level=1,
        source_path=Path("demo.docx"),
        output_name="lists/index.md",
        relative_dir="lists",
        breadcrumbs=[],
        blocks=[
            ListBlock(
                items=[
                    ListItem(runs=[TextRun(text="Top level")], level=2),
                    ListItem(runs=[TextRun(text="Nested detail")], level=3),
                    ListItem(runs=[TextRun(text="Tail item")], level=2),
                ]
            )
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "\n- Top level\n    - Nested detail\n- Tail item\n" in output


def test_indents_soft_break_continuations_inside_list_items():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Lists",
        level=1,
        source_path=Path("demo.docx"),
        output_name="lists/index.md",
        relative_dir="lists",
        breadcrumbs=[],
        blocks=[ListBlock(items=[ListItem(runs=[TextRun(text="Line 1\nLine 2")], level=0)])],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "\n- Line 1  \n  Line 2\n" in output


def test_renders_heading_anchor_targets():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Anchors",
        level=1,
        source_path=Path("demo.docx"),
        output_name="anchors/index.md",
        relative_dir="anchors",
        breadcrumbs=[],
        blocks=[Heading(level=1, text="1 Overview", anchor="heading_1")],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert '<a id="heading_1"></a>' in output
    assert "# 1 Overview" in output


def test_rewrites_internal_anchor_links_across_chunks():
    chunks = [
        Chunk(
            chunk_id="one",
            title="One",
            level=1,
            source_path=Path("demo.docx"),
            output_name="one/index.md",
            relative_dir="one",
            blocks=[
                Heading(level=1, text="One", anchor="one"),
                Paragraph(runs=[LinkRun(text="Two", url="#two")]),
            ],
        ),
        Chunk(
            chunk_id="two",
            title="Two",
            level=1,
            source_path=Path("demo.docx"),
            output_name="two/index.md",
            relative_dir="two",
            blocks=[Heading(level=1, text="Two", anchor="two")],
        ),
    ]

    renderer = MarkdownRenderer()
    renderer.anchor_map = build_anchor_map(chunks)

    output = renderer.render_chunk(chunks[0])

    assert "[Two](../two/index.md#two)" in output


def test_renders_table_anchor_targets():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Tables",
        level=1,
        source_path=Path("demo.docx"),
        output_name="tables/index.md",
        relative_dir="tables",
        breadcrumbs=[],
        blocks=[
            TableBlock(
                rows=[TableRow(cells=[TableCell(text="A")])],
                complexity="simple",
                anchor="_RefTable1",
            )
        ],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert '<a id="_RefTable1"></a>' in output


def test_rewrites_internal_anchor_links_inside_html_fallback_tables():
    chunks = [
        Chunk(
            chunk_id="one",
            title="One",
            level=1,
            source_path=Path("demo.docx"),
            output_name="one/index.md",
            relative_dir="one",
            blocks=[
                TableBlock(
                    rows=[
                        TableRow(
                            cells=[
                                TableCell(
                                    blocks=[Paragraph(runs=[LinkRun(text="Two", url="#two")])]
                                )
                            ]
                        )
                    ],
                    complexity="complex",
                )
            ],
        ),
        Chunk(
            chunk_id="two",
            title="Two",
            level=1,
            source_path=Path("demo.docx"),
            output_name="two/index.md",
            relative_dir="two",
            blocks=[Heading(level=1, text="Two", anchor="two")],
        ),
    ]

    renderer = MarkdownRenderer()
    renderer.anchor_map = build_anchor_map(chunks)

    output = renderer.render_chunk(chunks[0])

    assert '<a href="../two/index.md#two">Two</a>' in output


def test_renders_fenced_code_blocks():
    chunk = Chunk(
        chunk_id="chunk-1",
        title="Code",
        level=1,
        source_path=Path("demo.docx"),
        output_name="code/index.md",
        relative_dir="code",
        breadcrumbs=[],
        blocks=[CodeBlock(text="/**\n    private String twoElementCheckStatus;\n\n*/")],
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "```\n/**\n    private String twoElementCheckStatus;\n\n*/\n```" in output
