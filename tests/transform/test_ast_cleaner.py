from pathlib import Path

from documind.render.markdown_renderer import MarkdownRenderer
from documind.transform.ast_cleaner import ASTCleaner
from documind.types import Chunk, Document, LinkRun, ListBlock, ListItem, Paragraph, TableBlock, TableCell, TableRow, TextRun


def test_cleaner_preserves_spaces_around_styled_runs():
    document = Document(
        source_path=Path("demo.docx"),
        blocks=[
            Paragraph(
                runs=[
                    TextRun(text="Keep "),
                    TextRun(text="bold", bold=True),
                    TextRun(text=" text"),
                ]
            )
        ],
    )

    cleaned = ASTCleaner().clean(document)
    chunk = Chunk(
        chunk_id="demo",
        title="Demo",
        level=1,
        source_path=document.source_path,
        output_name="demo/index.md",
        relative_dir="demo",
        blocks=cleaned.blocks,
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "Keep **bold** text" in output


def test_cleaner_merges_runs_inside_list_items():
    document = Document(
        source_path=Path("demo.docx"),
        blocks=[
            ListBlock(
                items=[
                    ListItem(
                        level=0,
                        runs=[
                            TextRun(text="Keep "),
                            TextRun(text="bold", bold=True),
                            TextRun(text=" text"),
                        ],
                    )
                ]
            )
        ],
    )

    cleaned = ASTCleaner().clean(document)
    chunk = Chunk(
        chunk_id="demo",
        title="Demo",
        level=1,
        source_path=document.source_path,
        output_name="demo/index.md",
        relative_dir="demo",
        blocks=cleaned.blocks,
    )

    output = MarkdownRenderer().render_chunk(chunk)

    assert "- Keep **bold** text" in output


def test_cleaner_merges_adjacent_list_item_link_runs():
    document = Document(
        source_path=Path("demo.docx"),
        blocks=[
            ListBlock(
                items=[
                    ListItem(
                        level=0,
                        runs=[
                            LinkRun(
                                text="spec",
                                url="https://example.com/spec.xlsx",
                                link_kind="attachment",
                            ),
                            LinkRun(
                                text=".xlsx",
                                url="https://example.com/spec.xlsx",
                                link_kind="attachment",
                            ),
                        ],
                    )
                ]
            )
        ],
    )

    cleaned = ASTCleaner().clean(document)
    item = cleaned.blocks[0].items[0]

    assert item.runs == [
        LinkRun(
            text="spec.xlsx",
            url="https://example.com/spec.xlsx",
            link_kind="attachment",
        )
    ]


def test_cleaner_merges_adjacent_table_link_runs():
    document = Document(
        source_path=Path("demo.docx"),
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
                                                text="spec",
                                                url="https://example.com/spec.xlsx",
                                                link_kind="attachment",
                                            ),
                                            LinkRun(
                                                text=".xlsx",
                                                url="https://example.com/spec.xlsx",
                                                link_kind="attachment",
                                            ),
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

    cleaned = ASTCleaner().clean(document)
    paragraph = cleaned.blocks[0].rows[0].cells[0].blocks[0]

    assert paragraph.runs == [
        LinkRun(
            text="spec.xlsx",
            url="https://example.com/spec.xlsx",
            link_kind="attachment",
        )
    ]
