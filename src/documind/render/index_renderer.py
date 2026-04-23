"""Render document indexes and summaries."""

from __future__ import annotations

import json

from documind.render.link_resolver import build_anchor_map, resolve_internal_url
from documind.transform.toc_builder import TocBuilder, TocEntry
from documind.types import Chunk, LinkRun, ListBlock, Paragraph, ParagraphRun, TableBlock


class IndexRenderer:
    def __init__(self, toc_builder: TocBuilder | None = None) -> None:
        self.toc_builder = toc_builder or TocBuilder()
        self.anchor_map: dict[str, str] = {}

    def render_index(self, chunks: list[Chunk]) -> str:
        entries = self.toc_builder.build(chunks)
        lines = ["# Index", ""]
        lines.extend(self._render_entry(entry) for entry in entries)
        return "\n".join(lines).rstrip() + "\n"

    def render_summary(self, chunks: list[Chunk]) -> str:
        entries = self.toc_builder.build(chunks)
        self.anchor_map = build_anchor_map(chunks)
        payload = {
            "source_doc": entries[0].source_doc if entries else "",
            "chunks": [self._summary_entry(entry, chunk) for entry, chunk in zip(entries, chunks)],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    def _render_entry(self, entry: TocEntry) -> str:
        indent = "  " * max(entry.level - 1, 0)
        link = f"[{entry.title}](./{entry.path})"
        if entry.breadcrumbs:
            return f"{indent}- {link} ({entry.breadcrumb_text})"
        return f"{indent}- {link}"

    def _summary_entry(self, entry: TocEntry, chunk: Chunk) -> dict[str, object]:
        payload = {
            "chunk_id": entry.chunk_id,
            "title": entry.title,
            "level": entry.level,
            "path": entry.path,
            "breadcrumbs": list(entry.breadcrumbs),
        }
        links = self._collect_links(chunk)
        if links:
            payload["links"] = links
        return payload

    def _collect_links(self, chunk: Chunk) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        for block in chunk.blocks:
            links.extend(self._collect_links_from_block(block, chunk.output_name))
        return links

    def _collect_links_from_block(self, block: object, chunk_path: str) -> list[dict[str, str]]:
        if isinstance(block, Paragraph):
            return self._collect_links_from_runs(block.runs, chunk_path)
        if isinstance(block, ListBlock):
            links: list[dict[str, str]] = []
            for item in block.items:
                links.extend(self._collect_links_from_runs(item.runs, chunk_path))
            return links
        if isinstance(block, TableBlock):
            links: list[dict[str, str]] = []
            for row in block.rows:
                for cell in row.cells:
                    if cell.is_continuation:
                        continue
                    for cell_block in cell.blocks:
                        links.extend(self._collect_links_from_block(cell_block, chunk_path))
            return links
        return []

    def _collect_links_from_runs(self, runs: list[ParagraphRun], chunk_path: str) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        active_link: dict[str, str] | None = None
        for run in runs:
            if isinstance(run, LinkRun):
                resolved_url = resolve_internal_url(
                    run.url,
                    self.anchor_map,
                    chunk_path,
                    root_relative=True,
                )
                if (
                    active_link is not None
                    and active_link["url"] == resolved_url
                    and active_link["kind"] == run.link_kind
                ):
                    active_link["text"] += run.text
                    continue
                active_link = {
                    "text": run.text,
                    "url": resolved_url,
                    "kind": run.link_kind,
                }
                links.append(active_link)
                continue
            active_link = None
        return links
