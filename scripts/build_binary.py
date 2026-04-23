#!/usr/bin/env python3

from __future__ import annotations

import argparse
import platform
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from documind.binary_build import (
    UnsupportedBuildTargetError,
    build_pyinstaller_command,
    clean_binary_artifacts,
    resolve_build_target,
    supported_targets,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_binary.py",
        description="Build a local PyInstaller onefile binary for the current host platform.",
    )
    parser.add_argument("--target", choices=supported_targets(), default=None)
    parser.add_argument("--clean", action="store_true", help="Delete previous PyInstaller artifacts before building.")
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Delete previous PyInstaller artifacts and exit without building.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.clean or args.clean_only:
        clean_binary_artifacts(ROOT)
    if args.clean_only:
        return 0

    try:
        target = resolve_build_target(
            args.target,
            host_system=platform.system(),
            host_machine=platform.machine(),
        )
    except UnsupportedBuildTargetError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    command = build_pyinstaller_command(
        project_root=ROOT,
        target=target,
        python_executable=sys.executable,
    )
    print("Running:", shlex.join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
