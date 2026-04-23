"""Fallback HTML renderer for complex tables."""

from __future__ import annotations

import posixpath
from html import escape

from documind.render.link_resolver import resolve_internal_url
from documind.types import ImageBlock, LinkRun, Paragraph, TableBlock, TableCell, TextRun


class HTMLTableRenderer:
    def __init__(self) -> None:
        self.anchor_map: dict[str, str] = {}

    def render(self, table: TableBlock, chunk_path: str | None = None) -> str:
        lines = ["<table>", "  <tbody>"]
        for row in table.rows:
            lines.append("    <tr>")
            for cell in row.cells:
                if cell.is_continuation:
                    continue
                lines.append(f"      {self._render_cell(cell, chunk_path=chunk_path)}")
            lines.append("    </tr>")
        lines.extend(["  </tbody>", "</table>"])
        return "\n".join(lines)

    def _render_cell(self, cell: TableCell, chunk_path: str | None = None) -> str:
        attrs = []
        if cell.rowspan > 1:
            attrs.append(f'rowspan="{cell.rowspan}"')
        if cell.colspan > 1:
            attrs.append(f'colspan="{cell.colspan}"')
        attr_text = f" {' '.join(attrs)}" if attrs else ""
        text = self._render_cell_content(cell, chunk_path=chunk_path)
        return f"<td{attr_text}>{text}</td>"

    def _render_cell_content(self, cell: TableCell, chunk_path: str | None = None) -> str:
        if not cell.blocks:
            return escape(cell.text)

        parts: list[str] = []
        for block in cell.blocks:
            if isinstance(block, Paragraph):
                text = self._render_paragraph(block, chunk_path=chunk_path)
                if text:
                    parts.append(text)
            elif isinstance(block, ImageBlock):
                alt = escape(block.alt_text or "image", quote=True)
                src = escape(self._resolve_asset_path(block.asset_path, chunk_path), quote=True)
                parts.append(f'<img src="{src}" alt="{alt}" />')
        return "<br/>".join(parts)

    def _render_paragraph(self, paragraph: Paragraph, chunk_path: str | None = None) -> str:
        text = "".join(self._render_run(run, chunk_path=chunk_path) for run in paragraph.runs)
        text = text.replace("\n", "<br/>")
        if paragraph.anchor:
            return f'<a id="{escape(paragraph.anchor, quote=True)}"></a>{text}'
        return text

    def _render_run(self, run: TextRun | LinkRun, chunk_path: str | None = None) -> str:
        text = escape(run.text)
        if isinstance(run, LinkRun):
            href = escape(
                resolve_internal_url(run.url, self.anchor_map, chunk_path or ""),
                quote=True,
            )
            text = f'<a href="{href}">{text}</a>'
        if run.bold:
            text = f"<strong>{text}</strong>"
        if run.italic:
            text = f"<em>{text}</em>"
        if run.strike:
            text = f"<s>{text}</s>"
        return text

    def _resolve_asset_path(self, asset_path: str, chunk_path: str | None) -> str:
        if not chunk_path or not asset_path.startswith("./"):
            return asset_path

        chunk_dir = posixpath.dirname(chunk_path)
        if not chunk_dir:
            return asset_path

        relative = posixpath.relpath(asset_path[2:], chunk_dir)
        if relative.startswith("../"):
            return relative
        return f"./{relative}"
