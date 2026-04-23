from documind.render.html_table_renderer import HTMLTableRenderer
from documind.types import LinkRun, Paragraph, TableBlock, TableCell, TableRow


def test_renders_html_for_complex_table_with_rowspan_and_colspan():
    table = TableBlock(
        rows=[
            TableRow(cells=[TableCell(text="A", rowspan=2), TableCell(text="B", colspan=2)]),
            TableRow(cells=[TableCell(text="C"), TableCell(text="D")]),
        ],
        complexity="complex",
    )

    output = HTMLTableRenderer().render(table)

    assert output.startswith("<table>")
    assert 'rowspan="2"' in output
    assert 'colspan="2"' in output
    assert "<td>A</td>" not in output
    assert ">A</td>" in output


def test_renders_links_inside_table_cells_as_anchors():
    table = TableBlock(
        rows=[
            TableRow(
                cells=[
                    TableCell(
                        text="Download spec",
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
                        ],
                    )
                ]
            )
        ],
        complexity="complex",
    )

    output = HTMLTableRenderer().render(table)

    assert '<a href="https://example.com/spec.pdf">Download spec</a>' in output
