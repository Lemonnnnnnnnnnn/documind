"""Parse a DOCX package into the documind AST."""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from documind.constants import NS, R_NS, W_NS
from documind.parser.block_iterator import BlockIterator
from documind.parser.heading_detector import HeadingDetector
from documind.parser.image_parser import ImageParser
from documind.parser.table_parser import TableParser
from documind.reader.package_reader import DocxPackage
from documind.types import CodeBlock, Document, LinkRun, ListBlock, ListItem, Paragraph, ParagraphRun, TextRun


class DocumentParser:
    def __init__(
        self,
        block_iterator: BlockIterator | None = None,
        image_parser: ImageParser | None = None,
        table_parser: TableParser | None = None,
    ) -> None:
        self.block_iterator = block_iterator or BlockIterator()
        self.image_parser = image_parser or ImageParser()
        self.table_parser = table_parser or TableParser()
        self.table_parser.paragraph_parser = self._parse_paragraph

    def parse(self, package: DocxPackage) -> Document:
        detector = HeadingDetector(package.styles_root)
        codeblock_styles = self._codeblock_style_ids(package.styles_root)
        blocks: list[object] = []
        pending_list_items: list[ListItem] = []
        pending_list_id: str | None = None
        pending_anchor: str | None = None

        def flush_list() -> None:
            nonlocal pending_list_items, pending_list_id
            if not pending_list_items:
                return
            blocks.append(ListBlock(items=pending_list_items))
            pending_list_items = []
            pending_list_id = None

        for element in self.block_iterator.iter_blocks(package.document_root):
            if element.tag == f"{{{W_NS}}}p":
                paragraph, text = self._parse_paragraph(element, relationships=package.relationships)
                textbox_blocks = self._parse_textbox_code_blocks(element, codeblock_styles)
                paragraph.anchor = paragraph.anchor or pending_anchor
                heading = detector.detect(element, text)
                images = self.image_parser.parse(element, package)
                list_info = self._parse_list_info(element)

                if heading is not None:
                    flush_list()
                    heading.anchor = paragraph.anchor
                    blocks.append(heading)
                    pending_anchor = None
                    if paragraph.runs:
                        # Avoid duplicating heading text as a normal paragraph.
                        pass
                elif list_info is not None and paragraph.runs and not images:
                    list_id, level = list_info
                    if pending_list_id is not None and pending_list_id != list_id:
                        flush_list()
                    pending_list_items.append(ListItem(level=level, runs=paragraph.runs))
                    pending_list_id = list_id
                    pending_anchor = None
                elif paragraph.runs:
                    flush_list()
                    blocks.append(paragraph)
                    pending_anchor = None
                else:
                    flush_list()
                    if paragraph.anchor and not images and not textbox_blocks:
                        pending_anchor = paragraph.anchor
                if textbox_blocks:
                    blocks.extend(textbox_blocks)
                    pending_anchor = None

                if images and not paragraph.runs:
                    blocks.extend(images)
                elif images:
                    blocks.extend(images)
            elif element.tag == f"{{{W_NS}}}tbl":
                flush_list()
                table = self.table_parser.parse(element, package)
                table.anchor = pending_anchor or table.anchor
                pending_anchor = None
                blocks.append(table)

        flush_list()

        return Document(
            source_path=package.source_path,
            blocks=blocks,
            metadata={},
            media_map=package.asset_map.copy(),
        )

    def _parse_paragraph(
        self,
        paragraph: ET.Element,
        relationships: dict[str, str] | None = None,
    ) -> tuple[Paragraph, str]:
        paragraph_runs: list[ParagraphRun] = []
        relationships = relationships or {}
        paragraph_defaults = self._style_flags(paragraph.find("./w:pPr/w:rPr", NS))
        field_state: dict[str, object] | None = None

        for child in self._iter_inline_elements(paragraph):
            if child.tag == f"{{{W_NS}}}hyperlink":
                paragraph_runs.extend(self._parse_hyperlink(child, paragraph_defaults, relationships))
                continue
            if child.tag != f"{{{W_NS}}}r":
                continue

            field_char = child.find("./w:fldChar", NS)
            if field_char is not None:
                field_type = field_char.attrib.get(f"{{{W_NS}}}fldCharType")
                if field_type == "begin":
                    field_state = {"instruction_parts": [], "display_runs": [], "displaying": False}
                    continue
                if field_state is not None and field_type == "separate":
                    field_state["displaying"] = True
                    continue
                if field_state is not None and field_type == "end":
                    paragraph_runs.extend(self._finalize_field_runs(field_state))
                    field_state = None
                    continue

            instruction = self._run_instruction_text(child)
            if field_state is not None and instruction:
                instruction_parts = field_state["instruction_parts"]
                if isinstance(instruction_parts, list):
                    instruction_parts.append(instruction)
                continue

            run = self._parse_text_run(child, paragraph_defaults)
            if run is None:
                continue
            if field_state is not None:
                if field_state.get("displaying"):
                    display_runs = field_state["display_runs"]
                    if isinstance(display_runs, list):
                        display_runs.append(run)
                continue
            paragraph_runs.append(run)

        if field_state is not None:
            paragraph_runs.extend(self._fallback_field_runs(field_state))

        bookmark_names = self._bookmark_names(paragraph)
        paragraph_obj = Paragraph(
            runs=paragraph_runs,
            anchor=bookmark_names[0] if bookmark_names else None,
        )
        text = "".join(run.text for run in paragraph_runs).strip()
        return paragraph_obj, text

    def _parse_hyperlink(
        self,
        hyperlink: ET.Element,
        paragraph_defaults: dict[str, bool],
        relationships: dict[str, str],
    ) -> list[ParagraphRun]:
        text_runs = self._parse_text_runs(hyperlink, paragraph_defaults)
        if not text_runs:
            return []

        rel_id = hyperlink.attrib.get(f"{{{R_NS}}}id")
        anchor = hyperlink.attrib.get(f"{{{W_NS}}}anchor")
        target = relationships.get(rel_id, "") if rel_id else ""
        if not target and anchor:
            target = f"#{anchor}"
        if not target:
            return text_runs

        display_text = "".join(run.text for run in text_runs)
        link_kind = self._classify_link(display_text, None, target)
        return [
            LinkRun(
                text=run.text,
                url=target,
                link_kind=link_kind,
                bold=run.bold,
                italic=run.italic,
                strike=run.strike,
            )
            for run in text_runs
        ]

    def _parse_text_runs(
        self,
        container: ET.Element,
        paragraph_defaults: dict[str, bool],
    ) -> list[TextRun]:
        runs: list[TextRun] = []
        for run in self._iter_run_elements(container):
            parsed_run = self._parse_text_run(run, paragraph_defaults)
            if parsed_run is not None:
                runs.append(parsed_run)
        return runs

    def _parse_text_run(
        self,
        run: ET.Element,
        paragraph_defaults: dict[str, bool],
    ) -> TextRun | None:
        text = self._run_text(run)
        if not text:
            return None
        flags = paragraph_defaults | self._style_flags(run.find("./w:rPr", NS))
        return TextRun(
            text=text,
            bold=flags["bold"],
            italic=flags["italic"],
            strike=flags["strike"],
        )

    def _run_instruction_text(self, run: ET.Element) -> str:
        parts = [node.text or "" for node in run.findall("./w:instrText", NS)]
        return "".join(parts)

    def _finalize_field_runs(self, field_state: dict[str, object]) -> list[ParagraphRun]:
        display_runs = self._fallback_field_runs(field_state)
        if not display_runs:
            return []

        instruction = "".join(field_state.get("instruction_parts", []))
        url = self._extract_field_hyperlink_url(instruction)
        if not url:
            return display_runs

        display_text = "".join(run.text for run in display_runs)
        filename = self._extract_field_filename(instruction)
        link_kind = self._classify_link(display_text, filename, url)
        return [
            LinkRun(
                text=run.text,
                url=url,
                filename=filename,
                link_kind=link_kind,
                bold=run.bold,
                italic=run.italic,
                strike=run.strike,
            )
            for run in display_runs
        ]

    def _fallback_field_runs(self, field_state: dict[str, object]) -> list[TextRun]:
        display_runs = field_state.get("display_runs", [])
        if isinstance(display_runs, list):
            return list(display_runs)
        return []

    def _extract_field_hyperlink_url(self, instruction: str) -> str | None:
        anchor_quoted = re.search(r'HYPERLINK\s+\\l\s+"([^"]+)"', instruction, flags=re.IGNORECASE)
        if anchor_quoted:
            return f"#{anchor_quoted.group(1)}"
        anchor_unquoted = re.search(r"HYPERLINK\s+\\l\s+(\S+)", instruction, flags=re.IGNORECASE)
        if anchor_unquoted:
            return f"#{anchor_unquoted.group(1)}"
        quoted = re.search(r'HYPERLINK\s+"([^"]+)"', instruction, flags=re.IGNORECASE)
        if quoted:
            return quoted.group(1)
        unquoted = re.search(r"HYPERLINK\s+(\S+)", instruction, flags=re.IGNORECASE)
        if unquoted:
            return unquoted.group(1)
        return None

    def _extract_field_filename(self, instruction: str) -> str | None:
        match = re.search(
            r"(?:^|\s)(?:\\t|\t)?dfn\s+(.+?)(?=(?:\s(?:\\[a-z]+|(?:\\t|\t)[a-z]+)\b)|$)",
            instruction,
            flags=re.IGNORECASE,
        )
        if match is None:
            return None
        return self._decode_field_value(match.group(1).strip())

    def _decode_field_value(self, value: str) -> str:
        value = re.sub(
            r"%u([0-9A-Fa-f]{4})",
            lambda match: chr(int(match.group(1), 16)),
            value,
        )
        return unquote(value)

    def _classify_link(self, text: str, filename: str | None, url: str | None) -> str:
        candidates = [text.lower()]
        if filename:
            candidates.append(filename.lower())
        if url:
            lowered_url = url.lower()
            candidates.extend([lowered_url, urlsplit(lowered_url).path])
        attachment_suffixes = (
            ".csv",
            ".doc",
            ".docx",
            ".pdf",
            ".ppt",
            ".pptx",
            ".tsv",
            ".xls",
            ".xlsx",
            ".zip",
        )
        if any(
            candidate.endswith(attachment_suffixes)
            or any(f"{suffix}?" in candidate for suffix in attachment_suffixes)
            for candidate in candidates
        ):
            return "attachment"
        return "external"

    def _iter_inline_elements(self, container: ET.Element):
        for child in container:
            if child.tag in {f"{{{W_NS}}}r", f"{{{W_NS}}}hyperlink"}:
                yield child
                continue
            yield from self._iter_inline_elements(child)

    def _bookmark_names(self, paragraph: ET.Element) -> list[str]:
        names: list[str] = []
        for bookmark in paragraph.findall(".//w:bookmarkStart", NS):
            name = bookmark.attrib.get(f"{{{W_NS}}}name") or ""
            if not name:
                continue
            names.append(name)
        return names

    def _iter_run_elements(self, container: ET.Element):
        for child in container:
            if child.tag == f"{{{W_NS}}}r":
                yield child
                continue
            yield from self._iter_run_elements(child)

    def _run_text(self, run: ET.Element) -> str:
        parts: list[str] = []
        for node in run:
            if node.tag == f"{{{W_NS}}}t":
                parts.append(node.text or "")
            elif node.tag == f"{{{W_NS}}}tab":
                parts.append("    ")
            elif node.tag == f"{{{W_NS}}}br":
                parts.append("\n")
        return "".join(parts)

    def _style_flags(self, properties: ET.Element | None) -> dict[str, bool]:
        if properties is None:
            return {"bold": False, "italic": False, "strike": False}
        return {
            "bold": self._enabled(properties.find("./w:b", NS)),
            "italic": self._enabled(properties.find("./w:i", NS)),
            "strike": self._enabled(properties.find("./w:strike", NS)),
        }

    def _enabled(self, node: ET.Element | None) -> bool:
        if node is None:
            return False
        value = node.attrib.get(f"{{{W_NS}}}val")
        return value not in {"false", "0", "none"}

    def _parse_list_info(self, paragraph: ET.Element) -> tuple[str, int] | None:
        num_pr = paragraph.find("./w:pPr/w:numPr", NS)
        if num_pr is None:
            return None

        num_id = num_pr.find("./w:numId", NS)
        ilvl = num_pr.find("./w:ilvl", NS)
        if num_id is None or ilvl is None:
            return None

        list_id = num_id.attrib.get(f"{{{W_NS}}}val")
        level = ilvl.attrib.get(f"{{{W_NS}}}val")
        if not list_id or level is None or not level.isdigit():
            return None

        return list_id, int(level)

    def _codeblock_style_ids(self, styles_root: ET.Element | None) -> set[str]:
        if styles_root is None:
            return set()

        style_ids: set[str] = set()
        for style in styles_root.findall("./w:style", NS):
            if style.attrib.get(f"{{{W_NS}}}type") != "paragraph":
                continue
            style_id = style.attrib.get(f"{{{W_NS}}}styleId")
            if not style_id:
                continue
            name = style.find("./w:name", NS)
            style_name = (name.attrib.get(f"{{{W_NS}}}val") if name is not None else "") or ""
            if "melo-codeblock" in style_name.lower():
                style_ids.add(style_id)
        return style_ids

    def _parse_textbox_code_blocks(
        self,
        paragraph: ET.Element,
        codeblock_styles: set[str],
    ) -> list[CodeBlock]:
        if not codeblock_styles:
            return []

        blocks: list[CodeBlock] = []
        for textbox in paragraph.findall(".//w:txbxContent", NS):
            pending_lines: list[str] = []
            for textbox_paragraph in textbox.findall("./w:p", NS):
                if not self._is_codeblock_paragraph(textbox_paragraph, codeblock_styles):
                    if pending_lines:
                        normalized = self._normalize_codeblock_lines(pending_lines)
                        if normalized:
                            blocks.append(CodeBlock(text=normalized))
                        pending_lines = []
                    continue
                pending_lines.append(self._raw_paragraph_text(textbox_paragraph))
            if pending_lines:
                normalized = self._normalize_codeblock_lines(pending_lines)
                if normalized:
                    blocks.append(CodeBlock(text=normalized))
        return blocks

    def _is_codeblock_paragraph(self, paragraph: ET.Element, codeblock_styles: set[str]) -> bool:
        style = paragraph.find("./w:pPr/w:pStyle", NS)
        if style is None:
            return False
        style_id = style.attrib.get(f"{{{W_NS}}}val")
        return bool(style_id and style_id in codeblock_styles)

    def _raw_paragraph_text(self, paragraph: ET.Element) -> str:
        return "".join(self._run_text(run) for run in self._iter_run_elements(paragraph))

    def _normalize_codeblock_lines(self, lines: list[str]) -> str:
        normalized = list(lines)
        while normalized and normalized[0] == "":
            normalized.pop(0)
        while normalized and normalized[-1] == "":
            normalized.pop()
        return "\n".join(normalized)
