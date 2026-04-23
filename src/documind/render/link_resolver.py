"""Helpers for resolving internal bookmark links across rendered chunks."""

from __future__ import annotations

import posixpath

from documind.types import CodeBlock, Chunk, Heading, Paragraph, TableBlock


def build_anchor_map(chunks: list[Chunk]) -> dict[str, str]:
    anchors: dict[str, str] = {}
    for chunk in chunks:
        for anchor in iter_chunk_anchors(chunk):
            anchors.setdefault(anchor, chunk.output_name)
    return anchors


def resolve_internal_url(
    url: str,
    anchor_map: dict[str, str],
    current_path: str,
    root_relative: bool = False,
) -> str:
    if not url.startswith("#"):
        return url

    anchor = url[1:]
    target_path = anchor_map.get(anchor)
    if not target_path:
        return url
    if root_relative:
        return f"{target_path}#{anchor}"
    if target_path == current_path:
        return url

    current_dir = posixpath.dirname(current_path) or "."
    relative_path = posixpath.relpath(target_path, current_dir)
    if not relative_path.startswith(("../", "./")):
        relative_path = f"./{relative_path}"
    return f"{relative_path}#{anchor}"


def iter_chunk_anchors(chunk: Chunk):
    for block in chunk.blocks:
        yield from iter_block_anchors(block)


def iter_block_anchors(block: object):
    if isinstance(block, Heading) and block.anchor:
        yield block.anchor
        return
    if isinstance(block, Paragraph) and block.anchor:
        yield block.anchor
        return
    if isinstance(block, CodeBlock) and block.anchor:
        yield block.anchor
        return
    if isinstance(block, TableBlock):
        if block.anchor:
            yield block.anchor
        for row in block.rows:
            for cell in row.cells:
                if cell.is_continuation:
                    continue
                for cell_block in cell.blocks:
                    yield from iter_block_anchors(cell_block)
