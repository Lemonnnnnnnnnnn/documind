"""CLI entrypoint for documind."""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from documind.errors import DocuMindError, InvalidInputError, OutputConflictError
from documind.logging import configure_logging
from documind.pipeline.convert import ConvertPipeline
from documind.progress import ProgressReporter


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logger = configure_logging(verbose=getattr(args, "verbose", False))
    progress = ProgressReporter(logger.info)

    if args.command != "convert":
        parser.print_help()
        return 1

    try:
        out_dir = _resolve_output_dir(args.input, args.out_dir, overwrite=args.overwrite)
        pipeline = ConvertPipeline.build_default(progress=progress)
        pipeline.run(
            input_path=args.input,
            out_dir=out_dir,
            split_level=args.split_level,
            assets_dir_name=args.assets_dir,
            index_format=args.index_format,
            table_mode=args.table_mode,
            mode=args.mode,
        )
        return 0
    except (DocuMindError, OSError) as exc:
        logger.error(str(exc))
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="documind")
    subparsers = parser.add_subparsers(dest="command")

    convert = subparsers.add_parser("convert", help="Convert a DOCX file into markdown chunks.")
    convert.add_argument("input", type=Path)
    convert.add_argument("--out-dir", type=Path, default=None)
    convert.add_argument("--split-level", type=int, default=2)
    convert.add_argument("--assets-dir", default="assets")
    convert.add_argument("--mode", choices=("split", "inline"), default="split")
    convert.add_argument("--index-format", choices=("md", "json", "both"), default="both")
    convert.add_argument("--table-mode", choices=("auto", "markdown", "html"), default="auto")
    convert.add_argument("--overwrite", action="store_true")
    convert.add_argument("--verbose", action="store_true")
    return parser


def _resolve_output_dir(input_path: Path, requested: Path | None, overwrite: bool) -> Path:
    if not input_path.exists():
        raise InvalidInputError(f"Input file does not exist: {input_path}")

    out_dir = requested or Path("dist") / input_path.stem
    if out_dir.exists() and any(out_dir.iterdir()):
        if not overwrite:
            raise OutputConflictError(
                f"Output directory already exists and is not empty: {out_dir}. Use --overwrite to replace it."
            )
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
