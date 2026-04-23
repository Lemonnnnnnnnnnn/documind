from __future__ import annotations

from pathlib import Path
import shutil


class UnsupportedBuildTargetError(ValueError):
    """Raised when the requested binary target cannot be built on the current host."""


_TARGETS: dict[str, dict[str, object]] = {
    "macos-arm64": {
        "system": "Darwin",
        "machines": {"arm64", "aarch64"},
        "artifact_name": "documind-macos-arm64",
    },
    "windows-x64": {
        "system": "Windows",
        "machines": {"AMD64", "x86_64"},
        "artifact_name": "documind-windows-x64.exe",
    },
}


def detect_host_target(system: str, machine: str) -> str:
    for target, config in _TARGETS.items():
        if system == config["system"] and machine in config["machines"]:
            return target
    raise UnsupportedBuildTargetError(f"Unsupported build host: {system} {machine}")


def ensure_supported_target(target: str, host_system: str, host_machine: str) -> str:
    host_target = detect_host_target(system=host_system, machine=host_machine)
    if target != host_target:
        raise UnsupportedBuildTargetError(
            f"Cannot build target {target} on host {host_system} {host_machine}"
        )
    return target


def resolve_build_target(target: str | None, host_system: str, host_machine: str) -> str:
    if target is None:
        return detect_host_target(system=host_system, machine=host_machine)
    return ensure_supported_target(target, host_system=host_system, host_machine=host_machine)


def artifact_name_for_target(target: str) -> str:
    try:
        return str(_TARGETS[target]["artifact_name"])
    except KeyError as exc:
        raise UnsupportedBuildTargetError(f"Unsupported build target: {target}") from exc


def supported_targets() -> tuple[str, ...]:
    return tuple(_TARGETS)


def build_binary_path(project_root: Path, target: str) -> Path:
    return project_root / "release" / artifact_name_for_target(target)


def clean_binary_artifacts(project_root: Path) -> None:
    shutil.rmtree(project_root / "release", ignore_errors=True)
    shutil.rmtree(project_root / "build", ignore_errors=True)


def build_pyinstaller_command(project_root: Path, target: str, python_executable: str) -> list[str]:
    return [
        python_executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        artifact_name_for_target(target),
        "--distpath",
        str(project_root / "release"),
        "--workpath",
        str(project_root / "build" / "pyinstaller" / target),
        "--specpath",
        str(project_root / "build" / "pyinstaller" / "spec"),
        "--paths",
        str(project_root / "src"),
        str(project_root / "src" / "documind" / "cli.py"),
    ]
