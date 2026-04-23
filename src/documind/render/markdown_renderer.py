"""Markdown chunk rendering."""

from __future__ import annotations

import posixpath

from documind.render.frontmatter import render_frontmatter
from documind.render.html_table_renderer import HTMLTableRenderer
from documind.render.link_resolver import resolve_internal_url
from documind.types import CodeBlock, Chunk, Heading, ImageBlock, LinkRun, ListBlock, ListItem, Paragraph, ParagraphRun, TableBlock


class MarkdownRenderer:
    def __init__(
        self,
        html_table_renderer: HTMLTableRenderer | None = None,
        table_mode: str = "auto",
    ) -> None:
        self.html_table_renderer = html_table_renderer or HTMLTableRenderer()
        self.table_mode = table_mode
        self.anchor_map: dict[str, str] = {}

    def render_chunk(
        self,
        chunk: Chunk,
        *,
        include_frontmatter: bool = True,
        chunk_path: str | None = None,
    ) -> str:
        render_path = chunk_path or chunk.output_name
        self.html_table_renderer.anchor_map = self.anchor_map
        parts: list[str] = []
        if include_frontmatter:
            parts.append(render_frontmatter(chunk))
        for block in chunk.blocks:
            rendered = self._render_block(block, render_path)
            if rendered:
                parts.append(rendered)
        return "\n\n".join(parts).rstrip() + "\n"

    def _render_block(self, block: object, chunk_path: str) -> str:
        if isinstance(block, Heading):
            heading = f'{"#" * max(1, block.level)} {block.text}'
            if block.anchor:
                return f'<a id="{block.anchor}"></a>\n{heading}'
            return heading
        if isinstance(block, CodeBlock):
            rendered = f"```\n{block.text}\n```"
            return self._prepend_anchor(rendered, block.anchor)
        if isinstance(block, ListBlock):
            return self._render_list(block, chunk_path)
        if isinstance(block, Paragraph):
            return self._render_paragraph(block, chunk_path)
        if isinstance(block, ImageBlock):
            alt_text = block.alt_text or "image"
            asset_path = self._resolve_asset_path(block.asset_path, chunk_path)
            return f"![{alt_text}]({asset_path})"
        if isinstance(block, TableBlock):
            if self.table_mode == "html":
                rendered = self.html_table_renderer.render(block, chunk_path=chunk_path)
                return self._prepend_anchor(rendered, block.anchor)
            if self.table_mode == "auto" and block.complexity != "simple":
                rendered = self.html_table_renderer.render(block, chunk_path=chunk_path)
                return self._prepend_anchor(rendered, block.anchor)
            rendered = self._render_simple_table(block)
            return self._prepend_anchor(rendered, block.anchor)
        return ""

    def _render_paragraph(self, paragraph: Paragraph, chunk_path: str) -> str:
        content = self._render_runs(paragraph.runs, chunk_path)
        if paragraph.anchor:
            return f'<a id="{paragraph.anchor}"></a>\n{content}'
        return content

    def _render_run(self, run: ParagraphRun, chunk_path: str) -> str:
        text = run.text
        if isinstance(run, LinkRun):
            url = resolve_internal_url(run.url, self.anchor_map, chunk_path)
            text = f"[{text}]({url})"
        if run.bold:
            text = f"**{text}**"
        if run.italic:
            text = f"*{text}*"
        if run.strike:
            text = f"~~{text}~~"
        return text

    def _render_runs(self, runs: list[ParagraphRun], chunk_path: str) -> str:
        rendered_runs = [self._render_run(run, chunk_path) for run in runs]
        content = "".join(rendered_runs).strip()
        return content.replace("\n", "  \n")

    def _render_list(self, block: ListBlock, chunk_path: str) -> str:
        lines: list[str] = []
        for item, level in zip(block.items, self._normalized_list_levels(block), strict=False):
            content = self._render_list_item(item, level, chunk_path)
            if not content:
                continue
            lines.append(content)
        return "\n".join(lines)

    def _render_list_item(self, item: ListItem, level: int, chunk_path: str) -> str:
        indent = "    " * max(0, level)
        rendered = self._render_runs(item.runs, chunk_path)
        if not rendered:
            return ""

        content_lines = rendered.splitlines()
        first_line = f"{indent}- {content_lines[0]}"
        if len(content_lines) == 1:
            return first_line

        continuation_indent = f"{indent}  "
        continuation = "\n".join(
            f"{continuation_indent}{line}" if line else continuation_indent
            for line in content_lines[1:]
        )
        return "\n".join([first_line, continuation])

    def _normalized_list_levels(self, block: ListBlock) -> list[int]:
        if not block.items:
            return []

        base_level = block.items[0].level
        normalized_levels: list[int] = []
        previous_level = 0

        for index, item in enumerate(block.items):
            relative_level = max(0, item.level - base_level)
            if index == 0:
                normalized_level = 0
            else:
                normalized_level = min(relative_level, previous_level + 1)
            normalized_levels.append(normalized_level)
            previous_level = normalized_level

        return normalized_levels

    def _render_simple_table(self, table: TableBlock) -> str:
        if not table.rows:
            return ""

        rows = [
            [self._cell_text(cell).replace("|", r"\|") for cell in row.cells if not cell.is_continuation]
            for row in table.rows
        ]
        header = rows[0]
        divider = ["---"] * len(header)
        lines = [
            f"| {' | '.join(header)} |",
            f"| {' | '.join(divider)} |",
        ]
        for row in rows[1:]:
            lines.append(f"| {' | '.join(row)} |")
        return "\n".join(lines)

    def _cell_text(self, cell: object) -> str:
        return getattr(cell, "text", "")

    def _resolve_asset_path(self, asset_path: str, chunk_path: str) -> str:
        if not asset_path.startswith("./"):
            return asset_path

        chunk_dir = posixpath.dirname(chunk_path)
        if not chunk_dir:
            return asset_path

        relative = posixpath.relpath(asset_path[2:], chunk_dir)
        if relative.startswith("../"):
            return relative
        return f"./{relative}"

    def _prepend_anchor(self, rendered: str, anchor: str | None) -> str:
        if anchor:
            return f'<a id="{anchor}"></a>\n{rendered}'
        return rendered
