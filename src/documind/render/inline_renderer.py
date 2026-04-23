"""Render all chunks into a single Markdown document."""

from __future__ import annotations

from documind.render.link_resolver import iter_chunk_anchors
from documind.render.markdown_renderer import MarkdownRenderer
from documind.types import Chunk


class InlineRenderer:
    def __init__(
        self,
        markdown_renderer: MarkdownRenderer | None = None,
        output_name: str = "index.md",
    ) -> None:
        self.markdown_renderer = markdown_renderer or MarkdownRenderer()
        self.output_name = output_name

    def render_document(self, chunks: list[Chunk]) -> str:
        self.markdown_renderer.anchor_map = self._build_anchor_map(chunks)
        parts = [
            self.markdown_renderer.render_chunk(
                chunk,
                include_frontmatter=False,
                chunk_path=self.output_name,
            ).rstrip()
            for chunk in chunks
        ]
        return "\n\n".join(part for part in parts if part).rstrip() + "\n"

    def _build_anchor_map(self, chunks: list[Chunk]) -> dict[str, str]:
        anchors: dict[str, str] = {}
        for chunk in chunks:
            for anchor in iter_chunk_anchors(chunk):
                anchors.setdefault(anchor, self.output_name)
        return anchors
