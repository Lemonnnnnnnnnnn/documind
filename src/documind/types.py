"""Core data structures for documind."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False
    strike: bool = False


@dataclass(slots=True)
class LinkRun:
    text: str
    url: str
    filename: str | None = None
    link_kind: str = "external"
    bold: bool = False
    italic: bool = False
    strike: bool = False


ParagraphRun = TextRun | LinkRun


@dataclass(slots=True)
class Paragraph:
    runs: list[ParagraphRun] = field(default_factory=list)
    anchor: str | None = None


@dataclass(slots=True)
class CodeBlock:
    text: str
    anchor: str | None = None


@dataclass(slots=True)
class ListItem:
    level: int = 0
    runs: list[ParagraphRun] = field(default_factory=list)


@dataclass(slots=True)
class ListBlock:
    items: list[ListItem] = field(default_factory=list)


@dataclass(slots=True)
class Heading:
    level: int
    text: str
    anchor: str | None = None


@dataclass(slots=True)
class ImageBlock:
    rel_id: str
    asset_path: str
    alt_text: str | None = None
    width: int | None = None
    height: int | None = None
    caption: str | None = None


@dataclass(slots=True)
class TableCell:
    text: str = ""
    blocks: list[Any] = field(default_factory=list)
    rowspan: int = 1
    colspan: int = 1
    is_continuation: bool = False


@dataclass(slots=True)
class TableRow:
    cells: list[TableCell] = field(default_factory=list)


@dataclass(slots=True)
class TableBlock:
    rows: list[TableRow] = field(default_factory=list)
    complexity: str = "simple"
    anchor: str | None = None


@dataclass(slots=True)
class Document:
    source_path: Path
    blocks: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    media_map: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    title: str
    level: int
    source_path: Path
    output_name: str
    relative_dir: str = ""
    parent_path: str | None = None
    breadcrumbs: list[str] = field(default_factory=list)
    blocks: list[Any] = field(default_factory=list)
