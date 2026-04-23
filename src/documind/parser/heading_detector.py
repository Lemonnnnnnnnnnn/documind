"""Heading detection helpers."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from documind.constants import NS, W_NS
from documind.types import Heading

NUMBERED_HEADING_RE = re.compile(r"^(?P<prefix>\d+\.\d+(?:\.\d+){0,4})\s*\S")


class HeadingDetector:
    """Resolve heading levels from styles first, then text heuristics."""

    def __init__(self, styles_root: ET.Element | None = None) -> None:
        self.style_levels = self._parse_styles(styles_root)

    def detect(self, paragraph: ET.Element, text: str) -> Heading | None:
        cleaned = " ".join(text.split())
        if not cleaned:
            return None

        style_level = self._style_level(paragraph)
        if style_level is not None:
            return Heading(level=style_level, text=cleaned)

        fallback_level = self._regex_level(cleaned)
        if fallback_level is None:
            return None
        return Heading(level=fallback_level, text=cleaned)

    def _style_level(self, paragraph: ET.Element) -> int | None:
        style = paragraph.find("./w:pPr/w:pStyle", NS)
        if style is None:
            return None
        style_id = style.attrib.get(f"{{{W_NS}}}val")
        if not style_id:
            return None
        return self.style_levels.get(style_id)

    def _parse_styles(self, styles_root: ET.Element | None) -> dict[str, int]:
        if styles_root is None:
            return {}

        levels: dict[str, int] = {}
        for style in styles_root.findall("./w:style", NS):
            style_id = style.attrib.get(f"{{{W_NS}}}styleId")
            if not style_id:
                continue

            outline = style.find("./w:pPr/w:outlineLvl", NS)
            if outline is not None:
                outline_value = outline.attrib.get(f"{{{W_NS}}}val")
                if outline_value and outline_value.isdigit():
                    levels[style_id] = int(outline_value) + 1
                    continue

            name = style.find("./w:name", NS)
            if name is None:
                continue
            style_name = (name.attrib.get(f"{{{W_NS}}}val") or "").lower()
            match = re.search(r"heading\s+(\d+)", style_name)
            if match:
                levels[style_id] = int(match.group(1))
            elif style_name == "title":
                levels[style_id] = 1
        return levels

    def _regex_level(self, text: str) -> int | None:
        match = NUMBERED_HEADING_RE.match(text)
        if not match:
            return None
        return len(match.group("prefix").split("."))
