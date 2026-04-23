"""Iterate block-level elements from a DOCX body in source order."""

from __future__ import annotations

from collections.abc import Iterator
from xml.etree import ElementTree as ET

from documind.constants import W_NS


class BlockIterator:
    def iter_blocks(self, document_root: ET.Element) -> Iterator[ET.Element]:
        body = document_root.find(f"./{{{W_NS}}}body")
        if body is None:
            return
        for child in body:
            if child.tag in {f"{{{W_NS}}}p", f"{{{W_NS}}}tbl"}:
                yield child
