"""Image parsing helpers."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from documind.constants import NS, R_NS
from documind.reader.package_reader import DocxPackage
from documind.types import ImageBlock


class ImageParser:
    def parse(self, paragraph: ET.Element, package: DocxPackage) -> list[ImageBlock]:
        blocks: list[ImageBlock] = []
        for drawing in paragraph.findall(".//w:drawing", NS):
            blip = drawing.find(".//a:blip", NS)
            if blip is None:
                continue
            rel_id = blip.attrib.get(f"{{{R_NS}}}embed")
            if not rel_id:
                continue
            target = package.relationships.get(rel_id, "")
            asset_path = package.asset_map.get(target)
            if asset_path is None and target:
                asset_path = f"./assets/{Path(target).name}"

            extent = drawing.find(".//wp:extent", NS)
            doc_pr = drawing.find(".//wp:docPr", NS)
            alt_text = None
            if doc_pr is not None:
                alt_text = doc_pr.attrib.get("descr") or doc_pr.attrib.get("name")

            width = int(extent.attrib.get("cx", "0")) if extent is not None else None
            height = int(extent.attrib.get("cy", "0")) if extent is not None else None
            blocks.append(
                ImageBlock(
                    rel_id=rel_id,
                    asset_path=asset_path or "",
                    alt_text=alt_text,
                    width=width,
                    height=height,
                )
            )
        return blocks
