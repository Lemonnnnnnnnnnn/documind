from pathlib import Path

from documind.transform.chunker import Chunker
from documind.types import Document, Heading, Paragraph, TextRun


def test_split_level_2_creates_preface_h1_and_h2_chunks():
    document = Document(
        source_path=Path("demo.docx"),
        blocks=[
            Paragraph(runs=[TextRun(text="Preface text")]),
            Heading(level=1, text="1 Overview"),
            Paragraph(runs=[TextRun(text="Overview body")]),
            Heading(level=2, text="1.1 Scope"),
            Paragraph(runs=[TextRun(text="Scope body")]),
            Heading(level=3, text="1.1.1 Detail"),
            Paragraph(runs=[TextRun(text="Nested detail")]),
        ],
    )

    chunks = Chunker().split(document, split_level=2)

    assert [chunk.output_name for chunk in chunks] == [
        "00_preface.md",
        "1-overview/index.md",
        "1-overview/1-1-scope/index.md",
    ]
    assert chunks[0].relative_dir == ""
    assert chunks[1].relative_dir == "1-overview"
    assert chunks[1].parent_path is None
    assert chunks[2].relative_dir == "1-overview/1-1-scope"
    assert chunks[2].parent_path == "1-overview/index.md"
    assert chunks[1].breadcrumbs == []
    assert chunks[2].breadcrumbs == ["1 Overview"]
    assert chunks[2].blocks[0].text == "1.1 Scope"
    assert chunks[2].blocks[-1].runs[0].text == "Nested detail"


def test_chunk_ids_are_unique_and_slugger_state_does_not_leak_between_runs():
    chunker = Chunker()
    document = Document(
        source_path=Path("demo.docx"),
        blocks=[
            Heading(level=1, text="Intro"),
            Paragraph(runs=[TextRun(text="One")]),
            Heading(level=1, text="Intro"),
            Paragraph(runs=[TextRun(text="Two")]),
        ],
    )

    first = chunker.split(document, split_level=2)
    second = chunker.split(
        Document(
            source_path=Path("demo.docx"),
            blocks=[Heading(level=1, text="Intro"), Paragraph(runs=[TextRun(text="Again")])],
        ),
        split_level=2,
    )

    assert [chunk.chunk_id for chunk in first] == ["intro", "intro-2"]
    assert [chunk.output_name for chunk in first] == ["intro/index.md", "intro-2/index.md"]
    assert [chunk.output_name for chunk in second] == ["intro/index.md"]
