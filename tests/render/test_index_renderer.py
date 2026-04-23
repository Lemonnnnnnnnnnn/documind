import json
from pathlib import Path

from documind.render.index_renderer import IndexRenderer
from documind.types import Chunk, Heading, LinkRun, ListBlock, ListItem, Paragraph, TableBlock, TableCell, TableRow


def test_renders_markdown_index_and_summary_json():
    chunks = [
        Chunk(
            chunk_id="preface",
            title="Preface",
            level=0,
            source_path=Path("demo.docx"),
            output_name="00_preface.md",
            relative_dir="",
        ),
        Chunk(
            chunk_id="overview",
            title="1 Overview",
            level=1,
            source_path=Path("demo.docx"),
            output_name="1-overview/index.md",
            relative_dir="1-overview",
        ),
        Chunk(
            chunk_id="scope",
            title="1.1 Scope",
            level=2,
            source_path=Path("demo.docx"),
            output_name="1-overview/1-1-scope/index.md",
            relative_dir="1-overview/1-1-scope",
            parent_path="1-overview/index.md",
            breadcrumbs=["1 Overview"],
        ),
    ]

    renderer = IndexRenderer()
    index_output = renderer.render_index(chunks)
    summary_output = renderer.render_summary(chunks)
    parsed = json.loads(summary_output)

    assert "[1 Overview](./1-overview/index.md)" in index_output
    assert "1 Overview / 1.1 Scope" in index_output
    assert parsed["chunks"][2]["breadcrumbs"] == ["1 Overview"]
    assert parsed["chunks"][2]["path"] == "1-overview/1-1-scope/index.md"


def test_summary_merges_adjacent_link_segments_for_one_logical_link():
    chunks = [
        Chunk(
            chunk_id="links",
            title="Links",
            level=1,
            source_path=Path("demo.docx"),
            output_name="links/index.md",
            relative_dir="links",
            blocks=[
                Paragraph(
                    runs=[
                        LinkRun(
                            text="Bold",
                            url="https://example.com/spec",
                            link_kind="external",
                            bold=True,
                        ),
                        LinkRun(
                            text=" normal",
                            url="https://example.com/spec",
                            link_kind="external",
                        ),
                    ]
                )
            ],
        )
    ]

    parsed = json.loads(IndexRenderer().render_summary(chunks))

    assert parsed["chunks"][0]["links"] == [
        {
            "text": "Bold normal",
            "url": "https://example.com/spec",
            "kind": "external",
        }
    ]


def test_summary_collects_links_inside_tables():
    chunks = [
        Chunk(
            chunk_id="table-links",
            title="Table Links",
            level=1,
            source_path=Path("demo.docx"),
            output_name="table-links/index.md",
            relative_dir="table-links",
            blocks=[
                TableBlock(
                    rows=[
                        TableRow(
                            cells=[
                                TableCell(
                                    blocks=[
                                        Paragraph(
                                            runs=[
                                                LinkRun(
                                                    text="Download spec",
                                                    url="https://example.com/spec.pdf",
                                                    link_kind="attachment",
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        )
                    ],
                    complexity="complex",
                )
            ],
        )
    ]

    parsed = json.loads(IndexRenderer().render_summary(chunks))

    assert parsed["chunks"][0]["links"] == [
        {
            "text": "Download spec",
            "url": "https://example.com/spec.pdf",
            "kind": "attachment",
        }
    ]


def test_summary_collects_links_inside_list_items():
    chunks = [
        Chunk(
            chunk_id="list-links",
            title="List Links",
            level=1,
            source_path=Path("demo.docx"),
            output_name="list-links/index.md",
            relative_dir="list-links",
            blocks=[
                ListBlock(
                    items=[
                        ListItem(
                            level=0,
                            runs=[
                                LinkRun(
                                    text="spec-sheet.xlsx",
                                    url="https://example.com/spec.xlsx",
                                    link_kind="attachment",
                                )
                            ],
                        )
                    ]
                )
            ],
        )
    ]

    parsed = json.loads(IndexRenderer().render_summary(chunks))

    assert parsed["chunks"][0]["links"] == [
        {
            "text": "spec-sheet.xlsx",
            "url": "https://example.com/spec.xlsx",
            "kind": "attachment",
        }
    ]


def test_summary_rewrites_internal_anchor_links_to_target_chunk_paths():
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

    parsed = json.loads(IndexRenderer().render_summary(chunks))

    assert parsed["chunks"][0]["links"] == [
        {
            "text": "Two",
            "url": "two/index.md#two",
            "kind": "external",
        }
    ]
