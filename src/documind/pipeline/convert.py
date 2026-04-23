"""Conversion pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from documind.parser.document_parser import DocumentParser
from documind.reader.media_exporter import MediaExporter
from documind.render.inline_renderer import InlineRenderer
from documind.reader.package_reader import PackageReader
from documind.render.index_renderer import IndexRenderer
from documind.render.link_resolver import build_anchor_map
from documind.render.markdown_renderer import MarkdownRenderer
from documind.transform.ast_cleaner import ASTCleaner
from documind.transform.chunker import Chunker


class ConvertPipeline:
    def __init__(
        self,
        reader: PackageReader,
        media_exporter: MediaExporter,
        parser: DocumentParser,
        cleaner: ASTCleaner,
        chunker: Chunker,
        renderer: MarkdownRenderer,
        inline_renderer: InlineRenderer,
        index_renderer: IndexRenderer,
        progress=None,
    ) -> None:
        self.reader = reader
        self.media_exporter = media_exporter
        self.parser = parser
        self.cleaner = cleaner
        self.chunker = chunker
        self.renderer = renderer
        self.inline_renderer = inline_renderer
        self.index_renderer = index_renderer
        self.progress = progress

    @classmethod
    def build_default(cls, progress=None) -> "ConvertPipeline":
        renderer = MarkdownRenderer()
        return cls(
            reader=PackageReader(),
            media_exporter=MediaExporter(),
            parser=DocumentParser(),
            cleaner=ASTCleaner(),
            chunker=Chunker(),
            renderer=renderer,
            inline_renderer=InlineRenderer(markdown_renderer=renderer),
            index_renderer=IndexRenderer(),
            progress=progress,
        )

    def run(
        self,
        input_path: Path,
        out_dir: Path,
        split_level: int = 2,
        assets_dir_name: str = "assets",
        index_format: str = "both",
        table_mode: str = "auto",
        mode: str = "split",
    ) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        package = self._run_stage("Reading docx", lambda: self.reader.load(Path(input_path)))
        self._run_stage(
            "Exporting assets",
            lambda: self.media_exporter.export(package, out_dir, assets_dir_name=assets_dir_name),
        )
        document = self._run_stage("Parsing document", lambda: self.parser.parse(package))
        document = self._run_stage("Cleaning AST", lambda: self.cleaner.clean(document))
        chunks = self._run_stage(
            "Splitting chunks",
            lambda: self.chunker.split(document, split_level=split_level),
        )
        anchor_map = build_anchor_map(chunks)
        self.renderer.anchor_map = anchor_map
        self.index_renderer.anchor_map = anchor_map
        self.renderer.table_mode = table_mode
        self.inline_renderer.markdown_renderer.table_mode = table_mode
        if mode == "inline":
            self._run_stage(
                "Writing inline markdown",
                lambda: self._write_inline_document(chunks, out_dir),
            )
            return

        self._run_stage("Rendering markdown", lambda: self._write_chunks(chunks, out_dir))
        self._run_stage(
            "Writing index",
            lambda: self._write_indexes(chunks, out_dir, index_format=index_format),
        )

    def _write_chunks(self, chunks, out_dir: Path) -> None:
        for chunk in chunks:
            chunk_path = out_dir / chunk.output_name
            chunk_path.parent.mkdir(parents=True, exist_ok=True)
            chunk_path.write_text(self.renderer.render_chunk(chunk), encoding="utf-8")

    def _write_indexes(self, chunks, out_dir: Path, index_format: str) -> None:
        if index_format in {"md", "both"}:
            (out_dir / "index.md").write_text(
                self.index_renderer.render_index(chunks),
                encoding="utf-8",
            )
        if index_format in {"json", "both"}:
            (out_dir / "summary.json").write_text(
                self.index_renderer.render_summary(chunks),
                encoding="utf-8",
            )

    def _write_inline_document(self, chunks, out_dir: Path) -> None:
        (out_dir / "index.md").write_text(
            self.inline_renderer.render_document(chunks),
            encoding="utf-8",
        )

    def _run_stage(self, label: str, action):
        if self.progress is None:
            return action()
        with self.progress.stage(label):
            return action()
