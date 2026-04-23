"""Split documents into Markdown-friendly chunks."""

from __future__ import annotations

import posixpath

from documind.transform.slugger import Slugger
from documind.types import Chunk, Document, Heading


class Chunker:
    def __init__(self, slugger: Slugger | None = None) -> None:
        self.slugger = slugger or Slugger()

    def split(self, document: Document, split_level: int = 2) -> list[Chunk]:
        chunks: list[Chunk] = []
        preface_blocks = []
        current: Chunk | None = None
        heading_stack: dict[int, str] = {}
        dir_stack: dict[int, str] = {}
        slug_counts_by_parent: dict[str, dict[str, int]] = {}

        for block in document.blocks:
            if isinstance(block, Heading):
                heading_stack = {level: value for level, value in heading_stack.items() if level < block.level}
                dir_stack = {level: value for level, value in dir_stack.items() if level < block.level}
                if block.level <= split_level:
                    if current is not None:
                        chunks.append(current)
                    parent_dir = self._nearest_parent_dir(block.level, dir_stack)
                    slug_counts = slug_counts_by_parent.setdefault(parent_dir, {})
                    unique_slug = self.slugger.unique_slug(block.text, slug_counts)
                    relative_dir = posixpath.join(parent_dir, unique_slug) if parent_dir else unique_slug
                    output_name = posixpath.join(relative_dir, "index.md")
                    parent_path = posixpath.join(parent_dir, "index.md") if parent_dir else None
                    current = Chunk(
                        chunk_id=relative_dir,
                        title=block.text,
                        level=block.level,
                        source_path=document.source_path,
                        output_name=output_name,
                        relative_dir=relative_dir,
                        parent_path=parent_path,
                        breadcrumbs=[heading_stack[level] for level in sorted(heading_stack)],
                        blocks=[block],
                    )
                    dir_stack[block.level] = relative_dir
                else:
                    if current is None:
                        preface_blocks.append(block)
                    else:
                        current.blocks.append(block)
                heading_stack[block.level] = block.text
                continue

            if current is None:
                preface_blocks.append(block)
            else:
                current.blocks.append(block)

        if preface_blocks:
            chunks.insert(
                0,
                Chunk(
                    chunk_id="preface",
                    title="Preface",
                    level=0,
                    source_path=document.source_path,
                    output_name="00_preface.md",
                    relative_dir="",
                    parent_path=None,
                    breadcrumbs=[],
                    blocks=preface_blocks,
                ),
            )
        if current is not None:
            chunks.append(current)
        return chunks

    def _nearest_parent_dir(self, level: int, dir_stack: dict[int, str]) -> str:
        parent_levels = [ancestor for ancestor in dir_stack if ancestor < level]
        if not parent_levels:
            return ""
        return dir_stack[max(parent_levels)]
