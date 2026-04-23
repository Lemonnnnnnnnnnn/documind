"""YAML frontmatter rendering."""

from __future__ import annotations

import json

from documind.types import Chunk


def _quote_yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_frontmatter(chunk: Chunk) -> str:
    lines = [
        "---",
        f"title: {_quote_yaml_string(chunk.title)}",
        f"level: {chunk.level}",
        f"chunk_id: {_quote_yaml_string(chunk.chunk_id)}",
        f"source_doc: {_quote_yaml_string(chunk.source_path.name)}",
        f"path: {_quote_yaml_string(chunk.output_name)}",
    ]
    if chunk.parent_path is None:
        lines.append("parent_path: null")
    else:
        lines.append(f"parent_path: {_quote_yaml_string(chunk.parent_path)}")
    if chunk.breadcrumbs:
        lines.append("breadcrumbs:")
        lines.extend(f"  - {_quote_yaml_string(crumb)}" for crumb in chunk.breadcrumbs)
    else:
        lines.append("breadcrumbs: []")
    lines.append("---")
    return "\n".join(lines)
