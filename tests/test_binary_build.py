import importlib.util
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace

import pytest

from documind.binary_build import (
    UnsupportedBuildTargetError,
    artifact_name_for_target,
    build_binary_path,
    build_pyinstaller_command,
    clean_binary_artifacts,
    detect_host_target,
    ensure_supported_target,
    resolve_build_target,
)
from tests.conftest import ROOT


def _load_build_script_module():
    spec = importlib.util.spec_from_file_location("build_binary_script", ROOT / "scripts" / "build_binary.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_detect_host_target_supports_macos_arm64():
    assert detect_host_target(system="Darwin", machine="arm64") == "macos-arm64"


def test_detect_host_target_supports_windows_x64():
    assert detect_host_target(system="Windows", machine="AMD64") == "windows-x64"


def test_detect_host_target_rejects_unsupported_hosts():
    with pytest.raises(UnsupportedBuildTargetError, match="Unsupported build host: Linux x86_64"):
        detect_host_target(system="Linux", machine="x86_64")


def test_ensure_supported_target_rejects_cross_platform_build():
    with pytest.raises(
        UnsupportedBuildTargetError,
        match="Cannot build target windows-x64 on host Darwin arm64",
    ):
        ensure_supported_target("windows-x64", host_system="Darwin", host_machine="arm64")


def test_artifact_names_match_distribution_contract():
    assert artifact_name_for_target("macos-arm64") == "documind-macos-arm64"
    assert artifact_name_for_target("windows-x64") == "documind-windows-x64.exe"


def test_build_binary_path_points_to_release_directory(tmp_path):
    assert build_binary_path(tmp_path, "macos-arm64") == tmp_path / "release" / "documind-macos-arm64"
    assert (
        build_binary_path(tmp_path, "windows-x64")
        == tmp_path / "release" / "documind-windows-x64.exe"
    )


def test_build_pyinstaller_command_uses_onefile_release_layout(tmp_path):
    command = build_pyinstaller_command(
        project_root=tmp_path,
        target="macos-arm64",
        python_executable="python3",
    )

    assert command[:3] == ["python3", "-m", "PyInstaller"]
    assert "--noconfirm" in command
    assert "--clean" in command
    assert "--onefile" in command
    assert command[command.index("--name") + 1] == "documind-macos-arm64"
    assert command[command.index("--distpath") + 1] == str(tmp_path / "release")
    assert command[command.index("--workpath") + 1] == str(tmp_path / "build" / "pyinstaller" / "macos-arm64")
    assert command[command.index("--specpath") + 1] == str(tmp_path / "build" / "pyinstaller" / "spec")
    assert command[command.index("--paths") + 1] == str(tmp_path / "src")
    assert command[-1] == str(tmp_path / "src" / "documind" / "cli.py")


def test_resolve_build_target_defaults_to_current_host():
    assert resolve_build_target(None, host_system="Darwin", host_machine="arm64") == "macos-arm64"


def test_clean_binary_artifacts_removes_release_and_pyinstaller_workdirs(tmp_path):
    (tmp_path / "release" / "nested").mkdir(parents=True)
    (tmp_path / "build" / "pyinstaller" / "macos-arm64").mkdir(parents=True)

    clean_binary_artifacts(tmp_path)

    assert not (tmp_path / "release").exists()
    assert not (tmp_path / "build").exists()


def test_clean_only_runs_without_supported_host(monkeypatch, tmp_path):
    module = _load_build_script_module()

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module.platform, "machine", lambda: "x86_64")
    (tmp_path / "build" / "pyinstaller" / "stale").mkdir(parents=True)

    assert module.main(["--clean-only"]) == 0
    assert not (tmp_path / "build").exists()


def test_build_script_bootstraps_src_path_for_direct_execution(monkeypatch):
    spec = importlib.util.spec_from_file_location("isolated_build_binary_script", ROOT / "scripts" / "build_binary.py")
    assert spec is not None
    assert spec.loader is not None

    original_modules = {
        name: sys.modules.pop(name, None)
        for name in ("documind", "documind.binary_build")
    }
    monkeypatch.setattr(
        sys,
        "path",
        [
            entry
            for entry in sys.path
            if entry not in {"", str(ROOT), str(ROOT / "src")}
        ],
    )

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for name, module_obj in original_modules.items():
            if module_obj is not None:
                sys.modules[name] = module_obj

    assert callable(module.main)


def test_build_script_is_executable():
    mode = os.stat(ROOT / "scripts" / "build_binary.py").st_mode
    assert mode & stat.S_IXUSR


def test_build_script_main_runs_pyinstaller_and_returns_exit_code(monkeypatch, tmp_path):
    module = _load_build_script_module()
    recorded: dict[str, object] = {}

    def fake_run(command, cwd, check):
        recorded["command"] = command
        recorded["cwd"] = cwd
        recorded["check"] = check
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(module.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    assert module.main([]) == 3
    assert recorded["cwd"] == tmp_path
    assert recorded["check"] is False
    assert "--onefile" in recorded["command"]
    assert recorded["command"][recorded["command"].index("--name") + 1] == "documind-macos-arm64"
