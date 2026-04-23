"""Relationship parsing for DOCX packages."""

from __future__ import annotations

from xml.etree import ElementTree as ET

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def parse_relationships(root: ET.Element | None) -> dict[str, str]:
    if root is None:
        return {}

    relationships: dict[str, str] = {}
    for node in root.findall(f"./{{{REL_NS}}}Relationship"):
        rel_id = node.attrib.get("Id")
        target = node.attrib.get("Target")
        if rel_id and target:
            relationships[rel_id] = target.lstrip("./")
    return relationships
