"""Read DOCX package contents into a lightweight bundle."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile
from zipfile import ZipFile

from docx import Document as WordDocument

from documind.errors import InvalidInputError
from documind.reader.relationships import parse_relationships


@dataclass(slots=True)
class DocxPackage:
    source_path: Path
    document_root: ET.Element
    styles_root: ET.Element | None
    relationships: dict[str, str]
    media_files: dict[str, bytes]
    asset_map: dict[str, str] = field(default_factory=dict)
    word_document: object | None = None


class PackageReader:
    def load(self, path: Path) -> DocxPackage:
        source_path = Path(path)
        if not source_path.exists():
            raise InvalidInputError(f"Input file does not exist: {source_path}")
        if source_path.suffix.lower() != ".docx":
            raise InvalidInputError(f"Only .docx files are supported: {source_path}")

        try:
            with ZipFile(source_path) as archive:
                document_root = ET.fromstring(archive.read("word/document.xml"))
                styles_root = self._optional_xml(archive, "word/styles.xml")
                rels_root = self._optional_xml(archive, "word/_rels/document.xml.rels")
                media_files = self._read_media(archive)
            word_document = WordDocument(str(source_path))
        except (BadZipFile, KeyError, ET.ParseError, ValueError) as exc:
            raise InvalidInputError(f"Invalid DOCX package: {source_path}") from exc

        return DocxPackage(
            source_path=source_path,
            document_root=document_root,
            styles_root=styles_root,
            relationships=parse_relationships(rels_root),
            media_files=media_files,
            word_document=word_document,
        )

    def _optional_xml(self, archive: ZipFile, name: str) -> ET.Element | None:
        try:
            return ET.fromstring(archive.read(name))
        except KeyError:
            return None

    def _read_media(self, archive: ZipFile) -> dict[str, bytes]:
        media: dict[str, bytes] = {}
        for member in sorted(archive.namelist()):
            if not member.startswith("word/media/") or member.endswith("/"):
                continue
            media[member.removeprefix("word/")] = archive.read(member)
        return media
