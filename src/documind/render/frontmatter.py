"""YAML frontmatter rendering."""

from __future__ import annotations

from documind.types import Chunk


def render_frontmatter(chunk: Chunk) -> str:
    lines = [
        "---",
        f'title: "{chunk.title.replace("\"", "\\\"")}"',
        f"level: {chunk.level}",
        f'chunk_id: "{chunk.chunk_id}"',
        f'source_doc: "{chunk.source_path.name}"',
        f'path: "{chunk.output_name}"',
    ]
    if chunk.parent_path is None:
        lines.append("parent_path: null")
    else:
        lines.append(f'parent_path: "{chunk.parent_path}"')
    if chunk.breadcrumbs:
        lines.append("breadcrumbs:")
        lines.extend(f'  - "{crumb.replace("\"", "\\\"")}"' for crumb in chunk.breadcrumbs)
    else:
        lines.append("breadcrumbs: []")
    lines.append("---")
    return "\n".join(lines)
