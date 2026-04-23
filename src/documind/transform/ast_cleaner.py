"""AST normalization helpers."""

from __future__ import annotations

from documind.types import Document, LinkRun, ListBlock, ListItem, Paragraph, ParagraphRun, TableBlock, TableCell, TableRow, TextRun


class ASTCleaner:
    def clean(self, document: Document) -> Document:
        cleaned_blocks: list[object] = []
        for block in document.blocks:
            cleaned = self._clean_block(block)
            if cleaned is not None:
                cleaned_blocks.append(cleaned)
        return Document(
            source_path=document.source_path,
            blocks=cleaned_blocks,
            metadata=document.metadata.copy(),
            media_map=document.media_map.copy(),
        )

    def _clean_block(self, block: object) -> object | None:
        if isinstance(block, Paragraph):
            runs = self._merge_runs(block.runs)
            if not runs:
                return None
            return Paragraph(runs=runs, anchor=block.anchor)
        if isinstance(block, ListBlock):
            items: list[ListItem] = []
            for item in block.items:
                runs = self._merge_runs(item.runs)
                if not runs:
                    continue
                items.append(ListItem(level=item.level, runs=runs))
            if not items:
                return None
            return ListBlock(items=items)
        if isinstance(block, TableBlock):
            return TableBlock(
                rows=[
                    TableRow(
                        cells=[
                            TableCell(
                                text=cell.text,
                                blocks=[
                                    cleaned_block
                                    for cell_block in cell.blocks
                                    if (cleaned_block := self._clean_block(cell_block)) is not None
                                ],
                                rowspan=cell.rowspan,
                                colspan=cell.colspan,
                                is_continuation=cell.is_continuation,
                            )
                            for cell in row.cells
                        ]
                    )
                    for row in block.rows
                ],
                complexity=block.complexity,
                anchor=block.anchor,
            )
        return block

    def _merge_runs(self, runs: list[ParagraphRun]) -> list[ParagraphRun]:
        merged: list[ParagraphRun] = []
        for run in runs:
            if run.text == "":
                continue
            candidate = self._copy_run(run)
            if merged and self._same_style(merged[-1], candidate):
                merged[-1].text += candidate.text
            else:
                merged.append(candidate)
        return merged

    def _copy_run(self, run: ParagraphRun) -> ParagraphRun:
        if isinstance(run, LinkRun):
            return LinkRun(
                text=run.text,
                url=run.url,
                filename=run.filename,
                link_kind=run.link_kind,
                bold=run.bold,
                italic=run.italic,
                strike=run.strike,
            )
        return TextRun(text=run.text, bold=run.bold, italic=run.italic, strike=run.strike)

    def _same_style(self, left: ParagraphRun, right: ParagraphRun) -> bool:
        if type(left) is not type(right):
            return False
        if isinstance(left, LinkRun) and isinstance(right, LinkRun):
            return (
                left.url == right.url
                and left.filename == right.filename
                and left.link_kind == right.link_kind
                and left.bold == right.bold
                and left.italic == right.italic
                and left.strike == right.strike
            )
        return (
            left.bold == right.bold
            and left.italic == right.italic
            and left.strike == right.strike
        )
