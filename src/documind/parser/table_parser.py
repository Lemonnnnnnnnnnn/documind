"""Parse DOCX tables into an intermediate structure."""

from __future__ import annotations

from collections.abc import Callable
from xml.etree import ElementTree as ET

from documind.constants import NS, W_NS
from documind.parser.image_parser import ImageParser
from documind.reader.package_reader import DocxPackage
from documind.types import ImageBlock, LinkRun, Paragraph, TableBlock, TableCell, TableRow, TextRun

ParagraphParser = Callable[[ET.Element, dict[str, str] | None], tuple[Paragraph, str]]


class TableParser:
    def __init__(
        self,
        image_parser: ImageParser | None = None,
        paragraph_parser: ParagraphParser | None = None,
    ) -> None:
        self.image_parser = image_parser or ImageParser()
        self.paragraph_parser = paragraph_parser

    def parse(self, table: ET.Element, package: DocxPackage) -> TableBlock:
        rows: list[TableRow] = []
        complexity = "simple"
        active_vertical: dict[int, TableCell] = {}

        for row in table.findall("./w:tr", NS):
            parsed_cells: list[TableCell] = []
            column_index = 0
            for cell_el in row.findall("./w:tc", NS):
                cell, vmerge_state, has_images, has_links = self._parse_cell(cell_el, package)
                if cell.colspan > 1 or "\n" in cell.text or has_images or has_links:
                    complexity = "complex"

                if vmerge_state == "continue":
                    complexity = "complex"
                    anchor = active_vertical.get(column_index)
                    if anchor is not None:
                        anchor.rowspan += 1
                    cell.is_continuation = True
                elif vmerge_state == "restart":
                    complexity = "complex"
                    for offset in range(cell.colspan):
                        active_vertical[column_index + offset] = cell
                else:
                    for offset in range(cell.colspan):
                        active_vertical.pop(column_index + offset, None)

                parsed_cells.append(cell)
                column_index += cell.colspan

            rows.append(TableRow(cells=parsed_cells))

        return TableBlock(rows=rows, complexity=complexity)

    def _parse_cell(
        self,
        cell: ET.Element,
        package: DocxPackage,
    ) -> tuple[TableCell, str | None, bool, bool]:
        tc_pr = cell.find("./w:tcPr", NS)
        colspan = 1
        vmerge_state: str | None = None
        if tc_pr is not None:
            grid_span = tc_pr.find("./w:gridSpan", NS)
            if grid_span is not None:
                colspan = int(grid_span.attrib.get(f"{{{W_NS}}}val", "1"))
            vmerge = tc_pr.find("./w:vMerge", NS)
            if vmerge is not None:
                vmerge_state = vmerge.attrib.get(f"{{{W_NS}}}val", "continue")

        texts: list[str] = []
        blocks: list[Paragraph | ImageBlock] = []
        has_images = False
        has_links = False
        for paragraph in cell.findall("./w:p", NS):
            parsed_paragraph, paragraph_text = self._parse_paragraph(paragraph, package)
            if paragraph_text:
                texts.append(paragraph_text)
            if parsed_paragraph.runs:
                blocks.append(parsed_paragraph)
                has_links = has_links or any(
                    isinstance(run, LinkRun) for run in parsed_paragraph.runs
                )

            image_blocks = self.image_parser.parse(paragraph, package)
            if image_blocks:
                has_images = True
                blocks.extend(image_blocks)

        return (
            TableCell(text="\n".join(texts), blocks=blocks, colspan=colspan),
            vmerge_state,
            has_images,
            has_links,
        )

    def _parse_paragraph(self, paragraph: ET.Element, package: DocxPackage) -> tuple[Paragraph, str]:
        if self.paragraph_parser is not None:
            return self.paragraph_parser(paragraph, package.relationships)

        paragraph_text = "".join(
            node.text or ""
            for node in paragraph.findall(".//w:t", NS)
        ).strip()
        if not paragraph_text:
            return Paragraph(), ""
        return Paragraph(runs=[TextRun(text=paragraph_text)]), paragraph_text
