from pathlib import Path

from documind.render.inline_renderer import InlineRenderer
from documind.types import Chunk, Heading, ImageBlock, LinkRun, Paragraph, TextRun


def test_renders_chunks_into_single_markdown_document():
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
                Paragraph(
                    runs=[
                        TextRun(text="See "),
                        LinkRun(text="Two", url="#two"),
                    ]
                ),
                ImageBlock(rel_id="rId1", asset_path="./assets/img_001.png", alt_text="hero"),
            ],
        ),
        Chunk(
            chunk_id="two",
            title="Two",
            level=1,
            source_path=Path("demo.docx"),
            output_name="two/index.md",
            relative_dir="two",
            blocks=[
                Heading(level=1, text="Two", anchor="two"),
                Paragraph(runs=[TextRun(text="Done")]),
            ],
        ),
    ]

    output = InlineRenderer().render_document(chunks)

    assert not output.startswith("---\n")
    assert '<a id="one"></a>' in output
    assert "# One" in output
    assert "[Two](#two)" in output
    assert "![hero](./assets/img_001.png)" in output
    assert output.index("# One") < output.index("# Two")
