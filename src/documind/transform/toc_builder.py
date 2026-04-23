"""Build table-of-contents entries from chunks."""

from __future__ import annotations

from dataclasses import dataclass

from documind.types import Chunk


@dataclass(frozen=True, slots=True)
class TocEntry:
    chunk_id: str
    title: str
    level: int
    path: str
    source_doc: str
    breadcrumbs: tuple[str, ...]

    @property
    def breadcrumb_text(self) -> str:
        parts = [*self.breadcrumbs, self.title]
        return " / ".join(parts)


class TocBuilder:
    """Normalize chunk metadata for index-oriented outputs."""

    def build(self, chunks: list[Chunk]) -> list[TocEntry]:
        return [
            TocEntry(
                chunk_id=chunk.chunk_id,
                title=chunk.title,
                level=chunk.level,
                path=chunk.output_name,
                source_doc=chunk.source_path.name,
                breadcrumbs=tuple(chunk.breadcrumbs),
            )
            for chunk in chunks
        ]
